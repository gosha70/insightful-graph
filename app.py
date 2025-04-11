import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
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
def init_neo4j():
    return Neo4jConnector(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )

# App title
st.title("Knowledge Graph Builder")

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Knowledge Graph Builder",
    ["Data Upload", "Data Analysis", "Graph Builder", "Graph Analysis"]
)

# Data Upload Page
if page == "Data Upload":
    st.header("Upload and Preview Data")
    
    # Sample data option
    use_sample = st.checkbox("Use sample dataset")
    
    if use_sample:
        sample_option = st.selectbox(
            "Select sample dataset:",
            ["Customer Orders", "Movie Database"]
        )
        
        if sample_option == "Customer Orders":
            # Load sample customer orders data
            try:
                customer_orders_path = os.path.join("data", "sample_customer_orders.csv")
                st.session_state.data = pd.read_csv(customer_orders_path)
                st.success(f"Loaded sample customer orders dataset with {len(st.session_state.data)} rows")
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
                st.session_state.data = merged_data
        
        elif sample_option == "Movie Database":
            # Load sample movie data
            try:
                movies_path = os.path.join("data", "sample_movies.csv")
                st.session_state.data = pd.read_csv(movies_path)
                st.success(f"Loaded sample movie database with {len(st.session_state.data)} rows")
            except Exception as e:
                st.error(f"Error loading sample data: {str(e)}")
                
                # Fallback to generated data if file not found
                st.warning("Using generated sample data instead")
                
                # Create sample movie data
                st.session_state.data = pd.DataFrame({
                    "movie_id": np.repeat(range(1, 6), 3),
                    "title": np.repeat(["Movie A", "Movie B", "Movie C", "Movie D", "Movie E"], 3),
                    "release_year": np.repeat([2020, 2019, 2021, 2018, 2022], 3),
                    "genre": np.repeat(["Action", "Comedy", "Drama", "Sci-Fi", "Horror"], 3),
                    "actor_id": range(101, 116),
                    "actor_name": [f"Actor {i}" for i in range(1, 16)],
                    "character": [f"Character {i}" for i in range(1, 16)]
                })
            
            st.dataframe(st.session_state.data)
    else:
        # File upload
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            # Load and preview data
            try:
                st.session_state.data = DataLoader.load_csv(uploaded_file)
                st.success(f"Loaded {len(st.session_state.data)} rows and {len(st.session_state.data.columns)} columns")
                st.dataframe(st.session_state.data.head(10))
                
                # Show data info
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Data Types")
                    st.write(st.session_state.data.dtypes)
                
                with col2:
                    st.subheader("Missing Values")
                    st.write(st.session_state.data.isna().sum())
            
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
    
    # Data cleaning options
    if st.session_state.data is not None:
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

# Schema Analysis Page
elif page == "Data Analysis":
    st.header("Entity & Relationship Detection")
    
    if st.session_state.data is None:
        st.warning("Please upload data first!")
    else:
        # Infer schema if not already done
        if st.session_state.schema is None or st.button("Re-analyze Schema"):
            st.session_state.schema = SchemaDetector.infer_schema(st.session_state.data)
            st.success("Schema analysis complete!")
        
        # Display schema information
        st.subheader("Column Analysis")
        
        # Create tabs for different schema views
        tab1, tab2, tab3 = st.tabs(["Column Roles", "Data Types", "Relationships"])
        
        with tab1:
            # Group columns by role
            roles = {}
            for col, info in st.session_state.schema["columns"].items():
                role = info["role"]
                if role not in roles:
                    roles[role] = []
                roles[role].append(col)
            
            # Display columns by role with ability to change
            for role, columns in roles.items():
                st.write(f"**{role.title()} Columns:**")
                for col in columns:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"- {col} ({st.session_state.schema['columns'][col]['type']})")
                    with col2:
                        new_role = st.selectbox(
                            f"Change {col}",
                            ["identifier", "categorical", "property"],
                            index=["identifier", "categorical", "property"].index(role),
                            key=f"role_{col}"
                        )
                        if new_role != role:
                            st.session_state.schema["columns"][col]["role"] = new_role
                            st.rerun()
        
        with tab2:
            # Group columns by data type
            types = {}
            for col, info in st.session_state.schema["columns"].items():
                col_type = info["type"]
                if col_type not in types:
                    types[col_type] = []
                types[col_type].append(col)
            
            # Display columns by type
            for col_type, columns in types.items():
                st.write(f"**{col_type.title()} Columns:**")
                for col in columns:
                    st.write(f"- {col} ({st.session_state.schema['columns'][col]['role']})")
                    # Show sample values
                    if "sample_values" in st.session_state.schema["columns"][col]:
                        samples = st.session_state.schema["columns"][col]["sample_values"]
                        st.write(f"  Sample values: {', '.join(str(x) for x in samples)}")
        
        with tab3:
            # Display detected relationships
            if st.session_state.schema["relationships"]:
                st.write("**Detected Relationships:**")
                for rel in st.session_state.schema["relationships"]:
                    st.write(f"- {rel['source']} → {rel['target']} ({rel['type']})")
                    
                    # Option to remove relationship
                    if st.button(f"Remove {rel['source']} → {rel['target']} relationship", key=f"remove_{rel['source']}_{rel['target']}"):
                        st.session_state.schema["relationships"].remove(rel)
                        st.rerun()
            else:
                st.info("No relationships detected automatically")
            
            # Add custom relationship
            st.subheader("Add Custom Relationship")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                source = st.selectbox("Source Column", st.session_state.data.columns)
            with col2:
                target = st.selectbox("Target Column", st.session_state.data.columns)
            with col3:
                rel_type = st.text_input("Relationship Type", "RELATES_TO")
            
            if st.button("Add Relationship"):
                new_rel = {
                    "source": source,
                    "target": target,
                    "type": rel_type
                }
                
                # Check if relationship already exists
                exists = False
                for rel in st.session_state.schema["relationships"]:
                    if rel["source"] == source and rel["target"] == target:
                        exists = True
                        break
                
                if not exists:
                    st.session_state.schema["relationships"].append(new_rel)
                    st.success(f"Added relationship: {source} → {target} ({rel_type})")
                else:
                    st.warning("This relationship already exists!")

# Graph Builder Page
elif page == "Graph Builder":
    st.header("Build Knowledge Graph")
    
    if st.session_state.data is None:
        st.warning("Please upload data first!")
    elif st.session_state.schema is None:
        st.warning("Please analyze schema first!")
    else:
        # Neo4j connection status
        try:
            if st.session_state.neo4j is None:
                st.session_state.neo4j = init_neo4j()
                st.session_state.graph_builder = GraphBuilder(st.session_state.neo4j)
            
            st.session_state.neo4j.run_query("RETURN 1")
            st.success("Connected to Neo4j")
        except:
            st.error("Not connected to Neo4j. Please check your connection settings.")
            
            # Connection settings
            with st.expander("Neo4j Connection Settings"):
                uri = st.text_input("Neo4j URI", "bolt://localhost:7687")
                user = st.text_input("Username", "neo4j")
                password = st.text_input("Password", "password", type="password")
                
                if st.button("Connect"):
                    try:
                        st.session_state.neo4j = Neo4jConnector(uri, user, password)
                        st.session_state.graph_builder = GraphBuilder(st.session_state.neo4j)
                        st.success("Connected to Neo4j successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Connection failed: {str(e)}")
        
        # Graph building options
        st.subheader("Build Graph")
        
        # Option to clear existing graph
        clear_graph = st.checkbox("Clear existing graph data", value=True)
        
        # Build graph button
        if st.button("Build Knowledge Graph"):
            try:
                with st.spinner("Building knowledge graph..."):
                    # Clear database if selected
                    if clear_graph:
                        st.session_state.neo4j.clear_database()
                    
                    # Build graph
                    stats = st.session_state.graph_builder.build_graph_from_dataframe(
                        st.session_state.data,
                        st.session_state.schema
                    )
                    
                    st.session_state.graph_built = True
                    st.session_state.graph_stats = stats
                    
                    st.success("Knowledge graph built successfully!")
                    
                    # Display statistics
                    st.subheader("Graph Statistics")
                    st.write(f"- Total nodes: {stats['node_count']}")
                    st.write(f"- Total relationships: {stats['relationship_count']}")
                    
                    st.write("**Node Labels:**")
                    for label, count in stats['labels'].items():
                        st.write(f"- {label}: {count} nodes")
                    
                    st.write("**Relationship Types:**")
                    for rel_type, count in stats['relationship_types'].items():
                        st.write(f"- {rel_type}: {count} relationships")
            
            except Exception as e:
                st.error(f"Error building graph: {str(e)}")

# Graph Visualization Page
elif page == "Graph Analysis":
    st.header("Knowledge Graph Visualization")
    
    if not st.session_state.graph_built:
        st.warning("Please build the knowledge graph first!")
    else:
        # Initialize visualizer if needed
        if 'visualizer' not in st.session_state:
            st.session_state.visualizer = GraphVisualizer(st.session_state.neo4j)
        
        # Query options
        st.subheader("Visualization Options")
        
        # Limit number of nodes to display
        limit = st.slider("Max nodes to display", 10, 200, 50)
        
        # Filter by node label
        label_query = "MATCH (n) RETURN DISTINCT labels(n)[0] as label"
        try:
            labels = [record["label"] for record in st.session_state.neo4j.run_query(label_query)]
            selected_labels = st.multiselect("Filter by node type", labels, default=labels[:2] if len(labels) > 1 else labels)
        except:
            st.error("Error querying Neo4j for labels")
            selected_labels = []
        
        # Visualization
        if st.button("Visualize Graph"):
            with st.spinner("Loading graph visualization..."):
                # Get graph data
                graph_data = st.session_state.visualizer.get_graph_data(
                    limit=limit,
                    labels=selected_labels
                )
                
                # Display graph
                st.session_state.visualizer.display_graph(graph_data)
                
                # Display node details in sidebar
                if graph_data["nodes"]:
                    st.sidebar.subheader("Node Details")
                    node_id = st.sidebar.selectbox(
                        "Select a node to view details",
                        [f"{node['label']}: {node['properties'].get('name', node['properties'].get('id', node['id']))}" 
                         for node in graph_data["nodes"]]
                    )
                    
                    # Find selected node
                    selected_node = None
                    for node in graph_data["nodes"]:
                        node_label = f"{node['label']}: {node['properties'].get('name', node['properties'].get('id', node['id']))}"
                        if node_label == node_id:
                            selected_node = node
                            break
                    
                    if selected_node:
                        st.sidebar.write("**Properties:**")
                        for key, value in selected_node["properties"].items():
                            st.sidebar.write(f"- {key}: {value}")
