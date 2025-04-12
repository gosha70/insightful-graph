import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype, is_string_dtype, is_categorical_dtype, is_datetime64_any_dtype, is_extension_array_dtype, is_bool_dtype

# Configure logging once at the top‐level of your app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_relationship_types(json_path: Path):
    logging.info(f"Loading relationship types from {json_path}")
    with json_path.open('r', encoding='utf-8') as f:
        rels = json.load(f)
    # validate keys
    for i, obj in enumerate(rels):
        if not all(k in obj for k in ("value", "label", "description")):
            raise KeyError(f"Entry {i} missing one of ['value','label','description']")
    return rels

# Load at module import (or you could lazy‐load in your classes)
REL_TYPES_FILE = Path(__file__).parent / "relationship_types.json"
COMMON_RELATIONSHIP_TYPES = load_relationship_types(REL_TYPES_FILE)

def preprocess_dataframe(df):
    """Ensure all columns in the DataFrame are compatible with Arrow serialization."""
    for col in df.columns:
        try:
            # Handle categorical columns
            if pd.api.types.is_categorical_dtype(df[col]):
                df[col] = df[col].astype(str)
            # Handle object columns
            elif pd.api.types.is_object_dtype(df[col]):
                df[col] = df[col].astype(str)
            # Handle integer columns (convert to int64)
            elif pd.api.types.is_integer_dtype(df[col]):
                df[col] = df[col].astype('int64')
            # Handle float columns (convert to float64)
            elif pd.api.types.is_float_dtype(df[col]):
                df[col] = df[col].astype('float64')
            # Handle boolean columns
            elif pd.api.types.is_bool_dtype(df[col]):
                df[col] = df[col].astype(bool)
            # Handle datetime columns
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors='coerce')
            # Handle unsupported types
            else:
                df[col] = df[col].astype(str)
        except Exception as e:
            # Log and convert problematic columns to strings
            print(f"Error processing column '{col}': {e}")
            df[col] = df[col].astype(str)
    return df

class DataLoader:
    @staticmethod
    def load_csv(file_path_or_buffer, **kwargs):
        """Load data from CSV file with automatic type inference"""
        logging.info("Loading CSV data")
        df = pd.read_csv(file_path_or_buffer, **kwargs)
        return DataLoader.clean_dataframe(df)
    
    @staticmethod
    def load_sql(connection_string, query):
        """Load data from SQL database"""
        logging.info(f"Loading SQL data with query: {query}")
        try:
            df = pd.read_sql(query, connection_string)
            return DataLoader.clean_dataframe(df)
        except Exception as e:
            logging.error(f"Error loading SQL data: {e}")
            raise
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize, fill missing, and cast all pandas extension dtypes to NumPy/Python types."""
        # 1) Normalize column names
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # 2) Fill missing values
        for col in df.columns:
            if is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(0)
            elif is_string_dtype(df[col]) or is_categorical_dtype(df[col]):
                df[col] = df[col].fillna('').astype(str)
            elif is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 3) Cast pandas extension dtypes → native types for Arrow
        for col in df.columns:
            series = df[col]
            # Any pandas ExtensionArray (Int64Dtype, boolean, StringDtype, etc.)
            if is_extension_array_dtype(series):
                # nullable ints → int64
                if pd.api.types.is_integer_dtype(series.dtype):
                    logging.debug(f"Casting {col}: {series.dtype} → int64")
                    df[col] = series.astype('int64')
                # nullable booleans → bool
                elif is_bool_dtype(series.dtype):
                    logging.debug(f"Casting {col}: {series.dtype} → bool")
                    df[col] = series.astype('bool')
                # other extension types (e.g. StringDtype) → str
                else:
                    logging.debug(f"Casting {col}: {series.dtype} → str")
                    df[col] = series.astype(str)
        
        return df
            

class SchemaDetector:
    @staticmethod
    def infer_schema(df: pd.DataFrame) -> dict:
        """Infer schema from dataframe"""
        logging.info("Inferring schema from dataframe")
        schema = {"columns": {}, "relationships": []}
        total_rows = len(df)
        
        for col in df.columns:
            unique_count = df[col].nunique()
            unique_ratio = unique_count / total_rows if total_rows else 0
            null_count = df[col].isna().sum()
            
            if pd.api.types.is_numeric_dtype(df[col]):
                col_type = "numeric"
            elif pd.api.types.is_datetime64_dtype(df[col]):
                col_type = "datetime"
            else:
                col_type = "datetime" if SchemaDetector._is_potential_date(df[col]) else "string"
            
            if unique_ratio > 0.9:
                role = "identifier"
            elif unique_ratio < 0.1:
                role = "categorical"
            else:
                role = "property"
            
            schema["columns"][col] = {
                "type": col_type,
                "role": role,
                "unique_count": unique_count,
                "unique_ratio": unique_ratio,
                "null_count": null_count,
                "sample_values": df[col].dropna().sample(min(5, unique_count) if unique_count else 0).tolist()
            }
        
        schema["relationships"] = SchemaDetector._detect_relationships(df, schema["columns"])
        logging.info(f"Schema inference complete: {len(schema['columns'])} columns, "
                     f"{len(schema['relationships'])} relationships detected")
        return schema
    
    @staticmethod
    def _is_potential_date(series: pd.Series) -> bool:
        sample = series.dropna()
        if sample.empty:
            return False
        sample = sample.sample(min(10, len(sample)))
        try:
            pd.to_datetime(sample)
            return True
        except Exception:
            return False
    
    @staticmethod
    def _detect_relationships(df: pd.DataFrame, schema: dict) -> list:
        relationships = []
        id_columns = [c for c, info in schema.items() if info["role"] == "identifier" or "_id" in c]
        
        for col in id_columns:
            for other in df.columns:
                if col == other:
                    continue
                # name‐based heuristics
                if col.replace("_id", "") == other or other.replace("_id", "") == col:
                    rel_type = "RELATES_TO"
                    base = col.replace("_id", "").lower()
                    if "owner" in base:
                        rel_type = "BELONGS_TO"
                    elif "creator" in base:
                        rel_type = "CREATED"
                    elif "part" in base:
                        rel_type = "PART_OF"
                    elif "location" in base:
                        rel_type = "LOCATED_IN"
                    elif "employee" in base:
                        rel_type = "WORKS_FOR"
                    relationships.append({"source": col, "target": other, "type": rel_type})
            
            # value‐overlap heuristic
            for other in id_columns:
                if col == other:
                    continue
                vals, oth = set(df[col].dropna()), set(df[other].dropna())
                if vals and oth:
                    overlap = vals & oth
                    if len(overlap) / len(vals) > 0.5:
                        relationships.append({"source": col, "target": other, "type": "REFERENCES"})
        
        return relationships
