import streamlit as st
from src.graph_builder import Neo4jConnector, GraphBuilder

st.title("Graph Builder")
st.markdown("Connect to Neo4j and build the knowledge graph.")

# Initialize session state variables if not already set
if "is_step_available" not in st.session_state:
    st.session_state.is_step_available = lambda step: False  # Default function or logic

# Check if data and schema are available
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("Please upload data first!")
    if st.button("Go to Data Upload"):
        st.switch_page("pages/1_Data_Upload.py")
elif 'schema' not in st.session_state or st.session_state.schema is None:
    st.warning("Please analyze schema first!")
    if st.button("Go to Data Analysis"):
        st.switch_page("pages/2_Data_Analysis.py")
else:
    # Neo4j connection status
    try:
        if 'neo4j' not in st.session_state or st.session_state.neo4j is None:
            if hasattr(st.session_state, 'init_neo4j'):
                st.session_state.neo4j = st.session_state.init_neo4j()
                st.session_state.graph_builder = GraphBuilder(st.session_state.neo4j)
        
        st.session_state.neo4j.run_query("RETURN 1")
        st.success("✅ Connected to Neo4j")
    except Exception as e:
        st.error("❌ Not connected to Neo4j. Please check your connection settings.")
        
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
    
    # Display schema summary
    st.subheader("Schema Summary")
    
    # Show entity summary
    id_columns = [col for col, info in st.session_state.schema["columns"].items() 
                 if info["role"] == "identifier"]
    
    if id_columns:
        st.write("**Entities to be created:**")
        for id_col in id_columns:
            entity_name = id_col.replace("_id", "").title()
            st.write(f"- **{entity_name}** nodes (from {id_col})")
    
    # Show relationship summary
    if st.session_state.schema["relationships"]:
        st.write("**Relationships to be created:**")
        for rel in st.session_state.schema["relationships"]:
            source_entity = rel["source"].replace("_id", "").title()
            target_entity = rel["target"].replace("_id", "").title()
            st.write(f"- **{source_entity}** → **{target_entity}** ({rel['type']})")
    
    # Graph building options
    st.subheader("Build Graph")
    
    # Option to clear existing graph
    clear_graph = st.checkbox("Clear existing graph data", value=True, 
                             help="If checked, all existing nodes and relationships will be deleted before building the new graph.")
    
    # Advanced options
    with st.expander("Advanced Options"):
        batch_size = st.slider("Batch size", 100, 5000, 1000, 
                              help="Number of records to process in each batch. Larger values may be faster but require more memory.")
        
        create_constraints = st.checkbox("Create database constraints", value=True,
                                       help="Create uniqueness constraints for entity IDs. This improves performance but requires admin privileges.")
    
    # Build graph button
    if st.button("Build Knowledge Graph"):
        try:
            with st.spinner("Building knowledge graph..."):
                # Clear database if selected
                if clear_graph:
                    st.session_state.neo4j.clear_database()
                    st.info("Cleared existing graph data.")
                
                # Build graph
                stats = st.session_state.graph_builder.build_graph_from_dataframe(
                    st.session_state.data,
                    st.session_state.schema
                )
                
                st.session_state.graph_built = True
                st.session_state.graph_stats = stats
                
                st.success("✅ Knowledge graph built successfully!")
                
                # Display statistics
                st.subheader("Graph Statistics")
                
                # Create metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Nodes", stats['node_count'])
                with col2:
                    st.metric("Total Relationships", stats['relationship_count'])
                
                # Node labels
                st.write("**Node Labels:**")
                for label, count in stats['labels'].items():
                    st.write(f"- {label}: {count} nodes")
                
                # Relationship types
                st.write("**Relationship Types:**")
                for rel_type, count in stats['relationship_types'].items():
                    st.write(f"- {rel_type}: {count} relationships")
                
                # Next step button
                if 'is_step_available' in st.session_state and st.session_state.is_step_available("Graph Analysis"):
                    st.success("✅ Graph built successfully! You can now proceed to the Graph Analysis step.")
                    if st.button("Proceed to Graph Analysis"):
                        st.switch_page("pages/4_Graph_Analysis.py")
        
        except Exception as e:
            st.error(f"Error building graph: {str(e)}")
            st.info("Please check your Neo4j connection and try again.")
    
    # Show existing graph stats if already built
    elif 'graph_built' in st.session_state and st.session_state.graph_built and 'graph_stats' in st.session_state and st.session_state.graph_stats:
        st.info("A knowledge graph has already been built.")
        
        # Display statistics
        st.subheader("Current Graph Statistics")
        
        # Create metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Nodes", st.session_state.graph_stats['node_count'])
        with col2:
            st.metric("Total Relationships", st.session_state.graph_stats['relationship_count'])
        
        # Node labels
        st.write("**Node Labels:**")
        for label, count in st.session_state.graph_stats['labels'].items():
            st.write(f"- {label}: {count} nodes")
        
        # Relationship types
        st.write("**Relationship Types:**")
        for rel_type, count in st.session_state.graph_stats['relationship_types'].items():
            st.write(f"- {rel_type}: {count} relationships")
        
        # Next step button
        if 'is_step_available' in st.session_state and st.session_state.is_step_available("Graph Analysis"):
            st.success("✅ Graph is ready! You can proceed to the Graph Analysis step.")
            if st.button("Proceed to Graph Analysis"):
                st.switch_page("pages/4_Graph_Analysis.py")
