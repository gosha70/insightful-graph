import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataLoader:
    @staticmethod
    def load_csv(file_path_or_buffer, **kwargs):
        """Load data from CSV file with automatic type inference"""
        logging.info(f"Loading CSV data")
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
            logging.error(f"Error loading SQL data: {str(e)}")
            raise
    
    @staticmethod
    def clean_dataframe(df):
        """Basic cleaning operations"""
        # Make column names consistent
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Handle missing values
        for col in df.columns:
            # Fill numeric columns with 0 or mean
            if pd.api.types.is_numeric_dtype(df[col]):
                if df[col].isna().sum() > 0:
                    df[col] = df[col].fillna(0)
            # Fill string columns with empty string
            elif pd.api.types.is_string_dtype(df[col]):
                if df[col].isna().sum() > 0:
                    df[col] = df[col].fillna('')
        
        return df


class SchemaDetector:
    @staticmethod
    def infer_schema(df):
        """Infer schema from dataframe"""
        logging.info("Inferring schema from dataframe")
        schema = {"columns": {}, "relationships": []}
        total_rows = len(df)
        
        for col in df.columns:
            # Get basic stats
            unique_count = df[col].nunique()
            unique_ratio = unique_count / total_rows if total_rows > 0 else 0
            null_count = df[col].isna().sum()
            
            # Determine column type
            if pd.api.types.is_numeric_dtype(df[col]):
                col_type = "numeric"
            elif pd.api.types.is_datetime64_dtype(df[col]):
                col_type = "datetime"
            else:
                # Check if it might be a date string
                if SchemaDetector._is_potential_date(df[col]):
                    col_type = "datetime"
                else:
                    col_type = "string"
            
            # Determine column role
            if unique_ratio > 0.9:  # Likely an ID or unique identifier
                role = "identifier"
            elif unique_ratio < 0.1:  # Likely a categorical field
                role = "categorical"
            else:
                role = "property"
            
            # Store schema information
            schema["columns"][col] = {
                "type": col_type,
                "role": role,
                "unique_count": unique_count,
                "unique_ratio": unique_ratio,
                "null_count": null_count,
                "sample_values": df[col].dropna().sample(min(5, unique_count) if unique_count > 0 else 0).tolist()
            }
        
        # Detect potential relationships
        relationships = SchemaDetector._detect_relationships(df, schema["columns"])
        schema["relationships"] = relationships
        
        logging.info(f"Schema inference complete. Found {len(schema['columns'])} columns and {len(relationships)} potential relationships")
        return schema
    
    @staticmethod
    def _is_potential_date(series):
        """Check if a string series might contain dates"""
        # Sample a few non-null values
        sample = series.dropna().sample(min(10, len(series.dropna())))
        if len(sample) == 0:
            return False
        
        # Try to parse as dates
        try:
            pd.to_datetime(sample)
            return True
        except:
            return False
    
    @staticmethod
    def _detect_relationships(df, schema):
        """Detect potential relationships between columns"""
        relationships = []
        
        # Find columns that might be foreign keys
        id_columns = [col for col, info in schema.items() 
                     if info["role"] == "identifier" or "_id" in col]
        
        # Look for potential foreign key relationships
        for col in id_columns:
            # Look for columns with similar names in the same dataframe
            for other_col in df.columns:
                if col != other_col and (
                    col.replace("_id", "") == other_col or
                    other_col.replace("_id", "") == col
                ):
                    relationships.append({
                        "source": col,
                        "target": other_col,
                        "type": "RELATES_TO"
                    })
            
            # Look for columns that might reference each other
            for other_col in id_columns:
                if col != other_col:
                    # Check if values in one column are a subset of values in another
                    col_values = set(df[col].dropna().unique())
                    other_values = set(df[other_col].dropna().unique())
                    
                    # If there's significant overlap, might be a relationship
                    if len(col_values) > 0 and len(other_values) > 0:
                        overlap = col_values.intersection(other_values)
                        if len(overlap) / len(col_values) > 0.5:
                            relationships.append({
                                "source": col,
                                "target": other_col,
                                "type": "REFERENCES"
                            })
        
        return relationships
