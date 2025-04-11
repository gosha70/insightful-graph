import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_relationship_types(json_path: Path):
    """
    Load relationship types from a JSON file.
    """
    logging.info(f"Loading relationship types from {json_path}")
    try:
        with json_path.open('r', encoding='utf-8') as f:
            rels = json.load(f)
        # Basic validation
        if not isinstance(rels, list):
            raise ValueError("Expected a list of relationship objects")
        for idx, obj in enumerate(rels):
            if not all(k in obj for k in ("value", "label", "description")):
                raise KeyError(f"Missing keys in relationship entry at index {idx}")
        return rels
    except Exception as e:
        logging.error(f"Failed to load relationship types: {e}")
        raise

# Load at module import (or you could lazy‐load in your classes)
REL_TYPES_FILE = Path(__file__).parent / "relationship_types.json"
COMMON_RELATIONSHIP_TYPES = load_relationship_types(REL_TYPES_FILE)


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
        """Basic cleaning operations"""
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                if df[col].isna().any():
                    df[col] = df[col].fillna(0)
            elif pd.api.types.is_string_dtype(df[col]):
                if df[col].isna().any():
                    df[col] = df[col].fillna('')
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
