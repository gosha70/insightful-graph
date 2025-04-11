# pages/1_Data_Upload.py

import streamlit as st
import pandas as pd
import numpy as np
import os

from src.data_loader import DataLoader

# Initialize session state helper
if "is_step_available" not in st.session_state:
    st.session_state.is_step_available = lambda step: False

st.title("Data Upload")
st.markdown("Upload your data or use a sample dataset to get started.")

# --- Sample data loaders (unchanged) ---
use_sample = st.checkbox("Use sample dataset")

def load_orders_csv():
    try:
        path = os.path.join("data", "sample_customer_orders.csv")
        data = pd.read_csv(path)
        st.success(f"Loaded sample customer orders dataset with {len(data)} rows")
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
        st.session_state.data = data
    except Exception as e:
        st.error(f"Error loading sample data: {e}")
        st.warning("Using generated sample data instead")
        # ... generate fallback orders DataFrame ...
        # (omitted for brevity; same as your existing code)
        # then assign to st.session_state.data

def load_movies_csv():
    try:
        path = os.path.join("data", "sample_movies.csv")
        data = pd.read_csv(path)
        st.success(f"Loaded sample movie dataset with {len(data)} rows")
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
        st.session_state.data = data
    except Exception as e:
        st.error(f"Error loading sample data: {e}")
        st.warning("Using generated sample data instead")
        # ... generate fallback movies DataFrame ...
        st.session_state.data = data

def load_incidents_csv():
    try:
        path = os.path.join("data", "sample_event_log.csv")
        data = pd.read_csv(path)
        st.success(f"Loaded sample incidents event log dataset with {len(data)} rows")
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
        st.session_state.data = data
    except Exception as e:
        st.error(f"Error loading sample data: {e}")
        st.warning("Using generated sample data instead")
        # ... generate fallback incidents DataFrame ...
        st.session_state.data = data

# Choose sample or upload
if use_sample:
    sample_option = st.selectbox(
        "Select sample dataset:",
        ["Customer Orders", "Movie Database", "Incident Reports"]
    )
    if sample_option == "Customer Orders":
        load_orders_csv()
    elif sample_option == "Movie Database":
        load_movies_csv()
    elif sample_option == "Incident Reports":
        load_incidents_csv()
else:
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        try:
            # This will normalize, fill NAs, and cast all ints → int64 (Arrow‑compatible)
            data = DataLoader.load_csv(uploaded_file)
            st.success(f"Loaded {len(data)} rows and {len(data.columns)} columns")
            if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
                if hasattr(st.session_state, 'reset_state_on_data_change'):
                    st.session_state.reset_state_on_data_change()
            st.session_state.data = data
        except Exception as e:
            st.error(f"Error loading data: {e}")

# Database connection (unchanged)…
with st.expander("Connect to Database"):
    st.markdown("""
    Connect to a SQL database to load data directly.

    Supported databases:
    - PostgreSQL
    - MySQL
    - SQLite
    - SQL Server
    """)
    connection_string = st.text_input("Connection String", "postgresql://user:password@localhost:5432/database")
    query = st.text_area("SQL Query", "SELECT * FROM table_name LIMIT 1000")
    if st.button("Connect to Database"):
        try:
            with st.spinner("Connecting to database..."):
                data = DataLoader.load_sql(connection_string, query)
            st.success(f"Loaded {len(data)} rows and {len(data.columns)} columns")
            if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
                if hasattr(st.session_state, 'reset_state_on_data_change'):
                    st.session_state.reset_state_on_data_change()
            st.session_state.data = data
        except Exception as e:
            st.error(f"Error connecting to database: {e}")

# --- Display & cleaning UI (now directly on st.session_state.data) ---
if 'data' in st.session_state and st.session_state.data is not None:
    st.subheader("Data Preview")
    st.dataframe(st.session_state.data.head(10))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Types")
        st.write(st.session_state.data.dtypes)
    with col2:
        st.subheader("Missing Values")
        st.write(st.session_state.data.isna().sum())

    # Data cleaning options (unchanged)…
    st.subheader("Data Cleaning Options")
    if st.checkbox("Drop columns with too many missing values"):
        threshold = st.slider("Missing value threshold (%)", 0, 100, 50)
        cols_to_drop = [
            col for col in st.session_state.data.columns
            if st.session_state.data[col].isna().mean() * 100 > threshold
        ]
        if cols_to_drop and st.button(f"Drop {len(cols_to_drop)} columns"):
            st.session_state.data = st.session_state.data.drop(columns=cols_to_drop)
            st.success(f"Dropped {len(cols_to_drop)} columns with >={threshold}% missing values")
            st.dataframe(st.session_state.data.head())

    if st.checkbox("Drop duplicate rows"):
        dupes = st.session_state.data.duplicated().sum()
        if dupes and st.button(f"Drop {dupes} duplicate rows"):
            st.session_state.data = st.session_state.data.drop_duplicates()
            st.success(f"Dropped {dupes} duplicate rows")

    # Proceed button
    if st.session_state.is_step_available("Data Analysis"):
        st.success("✅ Data loaded successfully! You can now proceed to the Data Analysis step.")
        if st.button("Proceed to Data Analysis"):
            st.switch_page("pages/2_Data_Analysis.py")
else:
    st.info("Please upload a CSV file, connect to a database, or use a sample dataset to get started.")
