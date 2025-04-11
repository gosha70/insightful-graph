import streamlit as st
import pandas as pd
import numpy as np
import os
from src.data_loader import DataLoader, SchemaDetector
from src.graph_builder import Neo4jConnector, GraphBuilder
from src.visualization import GraphVisualizer

# Page configuration
st.set_page_config(
    page_title="Knowledge Graph Builder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'schema' not in st.session_state:
    st.session_state.schema = None
if 'graph_built' not in st.session_state:
    st.session_state.graph_built = False
if 'neo4j' not in st.session_state:
    st.session_state.neo4j = None
if 'graph_builder' not in st.session_state:
    st.session_state.graph_builder = None
if 'graph_stats' not in st.session_state:
    st.session_state.graph_stats = None

# Initialize Neo4j connection
@st.cache_resource
def init_neo4j(uri="bolt://localhost:7687", user="neo4j", password="password"):
    return Neo4jConnector(uri=uri, user=user, password=password)

# App title and introduction
st.title("Knowledge Graph Builder")
st.markdown("""
This application helps you analyze structured data and convert it into a knowledge graph.

### How to use:
1. **Data Upload**: Start by uploading a CSV file or using a sample dataset
2. **Data Analysis**: Analyze the data structure and identify entities and relationships
3. **Graph Builder**: Connect to Neo4j and build the knowledge graph
4. **Graph Analysis**: Visualize and explore the knowledge graph

### Navigation:
Use the sidebar to navigate between the different steps of the process.
""")

# Display current data status
if st.session_state.data is not None:
    st.success(f"✅ Data loaded: {len(st.session_state.data)} rows, {len(st.session_state.data.columns)} columns")
    
    if st.session_state.schema is not None:
        st.success(f"✅ Schema analyzed: {len(st.session_state.schema['columns'])} columns, {len(st.session_state.schema['relationships'])} relationships")
        
        if st.session_state.graph_built:
            st.success(f"✅ Graph built: {st.session_state.graph_stats['node_count']} nodes, {st.session_state.graph_stats['relationship_count']} relationships")
else:
    st.info("👈 Please start by uploading data using the 'Data Upload' page in the sidebar.")

# Function to reset dependent state when data changes
def reset_state_on_data_change():
    st.session_state.schema = None
    st.session_state.graph_built = False
    st.session_state.graph_stats = None

# Function to check if a step is available
def is_step_available(step_name):
    if step_name == "Data Upload":
        return True
    elif step_name == "Data Analysis":
        return st.session_state.data is not None
    elif step_name == "Graph Builder":
        return st.session_state.data is not None and st.session_state.schema is not None
    elif step_name == "Graph Analysis":
        return st.session_state.graph_built
    return False

# Add this to session state for use in other pages
st.session_state.reset_state_on_data_change = reset_state_on_data_change
st.session_state.is_step_available = is_step_available
st.session_state.init_neo4j = init_neo4j
