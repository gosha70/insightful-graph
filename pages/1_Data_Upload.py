import streamlit as st
import pandas as pd
import numpy as np
import os
from src.data_loader import DataLoader

# Initialize session state variables if not already set
if "is_step_available" not in st.session_state:
    st.session_state.is_step_available = lambda step: False  # Default function or logic

st.title("Data Upload")
st.markdown("Upload your data or use a sample dataset to get started.")

# Sample data option
use_sample = st.checkbox("Use sample dataset")

def load_orders_csv():
    try:
        customer_orders_path = os.path.join("data", "sample_customer_orders.csv")
        data = pd.read_csv(customer_orders_path)
        st.success(f"Loaded sample customer orders dataset with {len(data)} rows")
            
        # Reset dependent state when data changes
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
            
        st.session_state.data = data
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
            
        # Fallback to generated data if file not found
        st.warning("Using generated sample data instead")
            
        # Create sample customer orders data
        customers = pd.DataFrame({
                "customer_id": range(1, 11),
                "customer_name": [f"Customer {i}" for i in range(1, 11)],
                "customer_email": [f"customer{i}@example.com" for i in range(1, 11)]
            })
            
        products = pd.DataFrame({
                "product_id": range(1, 6),
                "product_name": [f"Product {i}" for i in range(1, 6)],
                "price": np.random.uniform(10, 100, 5).round(2),
                "product_category": np.random.choice(["Electronics", "Clothing", "Books"], 5)
            })
            
        orders = pd.DataFrame({
                "order_id": range(1, 21),
                "customer_id": np.random.choice(range(1, 11), 20),
                "order_date": pd.date_range(start="2023-01-01", periods=20),
                "total_amount": np.random.uniform(20, 200, 20).round(2)
            })
            
        # Merge data
        merged_data = orders.merge(customers, on="customer_id", how="left")
            
         # Reset dependent state when data changes
        if 'data' in st.session_state and st.session_state.data is not None and not merged_data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
                
        st.session_state.data = merged_data

def load_movies_csv():
    try:
        movies_path = os.path.join("data", "sample_movies.csv")
        data = pd.read_csv(movies_path)
        st.success(f"Loaded sample movie dataset with {len(data)} rows")
            
            # Reset dependent state when data changes
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
                
        st.session_state.data = data
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
            
            # Fallback to generated data if file not found
        st.warning("Using generated sample data instead")
            
        # Create sample movie data
        data = pd.DataFrame({
                "movie_id": np.repeat(range(1, 6), 3),
                "title": np.repeat(["Movie A", "Movie B", "Movie C", "Movie D", "Movie E"], 3),
                "release_year": np.repeat([2020, 2019, 2021, 2018, 2022], 3),
                "genre": np.repeat(["Action", "Comedy", "Drama", "Sci-Fi", "Horror"], 3),
                "actor_id": range(101, 116),
                "actor_name": [f"Actor {i}" for i in range(1, 16)],
                "character": [f"Character {i}" for i in range(1, 16)]
            })
            
            # Reset dependent state when data changes
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
                
        st.session_state.data = data

def load_incidents_csv():
    try:
        movies_path = os.path.join("data", "sample_event_log.csv")
        data = pd.read_csv(movies_path)
        st.success(f"Loaded sample incidents event log dataset with {len(data)} rows")
            
            # Reset dependent state when data changes
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
                
        st.session_state.data = data
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
            
            # Fallback to generated data if file not found
        st.warning("Using generated sample data instead")
            
        # Create sample incident event log data
        data = pd.DataFrame({
            "incident_id": range(1, 21),
            "timestamp": pd.date_range(start="2023-01-01", periods=20, freq="H"),
            "event_type": np.random.choice(["Error", "Warning", "Info", "Critical"], 20),
            "user_id": np.random.randint(1001, 1021, 20),
            "description": [f"Event description {i}" for i in range(1, 21)],
            "severity": np.random.choice(["Low", "Medium", "High", "Critical"], 20)
            })
            
            # Reset dependent state when data changes
        if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
            if hasattr(st.session_state, 'reset_state_on_data_change'):
                st.session_state.reset_state_on_data_change()
                
        st.session_state.data = data       

if use_sample:
    sample_option = st.selectbox(
        "Select sample dataset:",
        ["Customer Orders", "Movie Database", "Incident Reports"]
    )
    
    if sample_option == "Customer Orders":
        # Load sample customer orders data
        load_orders_csv()
    
    elif sample_option == "Movie Database":
        # Load sample movie data
        load_movies_csv()
    elif sample_option == "Incident Reports":
        # Load sample movie data
        load_incidents_csv()    
else:
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Load and preview data
        try:
            data = DataLoader.load_csv(uploaded_file)
            st.success(f"Loaded {len(data)} rows and {len(data.columns)} columns")
            
            # Reset dependent state when data changes
            if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
                if hasattr(st.session_state, 'reset_state_on_data_change'):
                    st.session_state.reset_state_on_data_change()
                
            st.session_state.data = data
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

# Database connection option
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
                
                # Reset dependent state when data changes
                if 'data' in st.session_state and st.session_state.data is not None and not data.equals(st.session_state.data):
                    if hasattr(st.session_state, 'reset_state_on_data_change'):
                        st.session_state.reset_state_on_data_change()
                    
                st.session_state.data = data
        except Exception as e:
            st.error(f"Error connecting to database: {str(e)}")

# Apply the fix before displaying the DataFrame
if 'data' in st.session_state and st.session_state.data is not None:
    st.dataframe(st.session_state.data.head(10))

# Display data preview if available
if 'data' in st.session_state and st.session_state.data is not None:
    st.subheader("Data Preview")
    st.dataframe(st.session_state.data.head(10))
    
    # Show data info
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Types")
        st.write(st.session_state.data.dtypes)
    
    with col2:
        st.subheader("Missing Values")
        st.write(st.session_state.data.isna().sum())
    
    # Data cleaning options
    st.subheader("Data Cleaning Options")
    
    if st.checkbox("Drop columns with too many missing values"):
        threshold = st.slider("Missing value threshold (%)", 0, 100, 50)
        cols_to_drop = [
            col for col in st.session_state.data.columns 
            if st.session_state.data[col].isna().mean() * 100 > threshold
        ]
        
        if cols_to_drop:
            if st.button(f"Drop {len(cols_to_drop)} columns"):
                st.session_state.data = st.session_state.data.drop(columns=cols_to_drop)
                st.success(f"Dropped {len(cols_to_drop)} columns with >={threshold}% missing values")
                st.dataframe(st.session_state.data.head())
        else:
            st.info(f"No columns with >={threshold}% missing values")
    
    if st.checkbox("Drop duplicate rows"):
        dupes = st.session_state.data.duplicated().sum()
        if dupes > 0:
            if st.button(f"Drop {dupes} duplicate rows"):
                st.session_state.data = st.session_state.data.drop_duplicates()
                st.success(f"Dropped {dupes} duplicate rows")
        else:
            st.info("No duplicate rows found")
    
    # Next step button
    if 'is_step_available' in st.session_state and st.session_state.is_step_available("Data Analysis"):
        st.success("✅ Data loaded successfully! You can now proceed to the Data Analysis step.")
        if st.button("Proceed to Data Analysis"):
            st.switch_page("pages/2_Data_Analysis.py")
    else:
        st.error("There was an issue with the data. Please check the errors above.")
else:
    st.info("Please upload a CSV file, connect to a database, or use a sample dataset to get started.")
