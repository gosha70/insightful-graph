import streamlit as st
import pandas as pd
from src.visualization import GraphVisualizer
from src.llm_integration import OllamaClient, GraphQASystem

st.title("Graph Analysis")
st.markdown("Visualize and explore the knowledge graph.")

# Initialize session state variables if not already set
if "is_step_available" not in st.session_state:
    st.session_state.is_step_available = lambda step: False  # Default function or logic

# Check if graph is built
if 'graph_built' not in st.session_state or not st.session_state.graph_built:
    st.warning("Please build the knowledge graph first!")
    if st.button("Go to Graph Builder"):
        st.switch_page("pages/3_Graph_Builder.py")
else:
    # Initialize visualizer if needed
    if 'visualizer' not in st.session_state:
        if 'neo4j' in st.session_state and st.session_state.neo4j is not None:
            st.session_state.visualizer = GraphVisualizer(st.session_state.neo4j)
    
    # Create tabs for different analysis features
    tab1, tab2, tab3 = st.tabs(["Graph Visualization", "Cypher Query", "Q&A (Coming Soon)"])
    
    with tab1:
        st.subheader("Visualization Options")
        
        # Limit number of nodes to display
        limit = st.slider("Max nodes to display", 10, 200, 50)
        
        # Filter by node label
        label_query = "MATCH (n) RETURN DISTINCT labels(n)[0] as label"
        try:
            labels = [record["label"] for record in st.session_state.neo4j.run_query(label_query)]
            selected_labels = st.multiselect("Filter by node type", labels, default=labels[:2] if len(labels) > 1 else labels)
        except Exception as e:
            st.error(f"Error querying Neo4j for labels: {str(e)}")
            selected_labels = []
        
        # Node search
        search_term = st.text_input("Search nodes (by name or property)", "")
        
        # Visualization
        if st.button("Visualize Graph"):
            with st.spinner("Loading graph visualization..."):
                # Get graph data
                graph_data = st.session_state.visualizer.get_graph_data(
                    limit=limit,
                    labels=selected_labels
                )
                
                # Filter by search term if provided
                if search_term and graph_data["nodes"]:
                    # Filter nodes that contain the search term in any property
                    filtered_nodes = []
                    for node in graph_data["nodes"]:
                        for prop_value in node["properties"].values():
                            if search_term.lower() in str(prop_value).lower():
                                filtered_nodes.append(node)
                                break
                    
                    # Filter edges to only include those connected to filtered nodes
                    node_ids = [node["id"] for node in filtered_nodes]
                    filtered_edges = [
                        edge for edge in graph_data["edges"]
                        if edge["source"] in node_ids or edge["target"] in node_ids
                    ]
                    
                    graph_data["nodes"] = filtered_nodes
                    graph_data["edges"] = filtered_edges
                    
                    if not filtered_nodes:
                        st.warning(f"No nodes found matching '{search_term}'")
                
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
                        
                        # Show connected nodes
                        connected_nodes = []
                        for edge in graph_data["edges"]:
                            if edge["source"] == selected_node["id"]:
                                # Find target node
                                for node in graph_data["nodes"]:
                                    if node["id"] == edge["target"]:
                                        connected_nodes.append((node, edge["label"], "outgoing"))
                                        break
                            elif edge["target"] == selected_node["id"]:
                                # Find source node
                                for node in graph_data["nodes"]:
                                    if node["id"] == edge["source"]:
                                        connected_nodes.append((node, edge["label"], "incoming"))
                                        break
                        
                        if connected_nodes:
                            st.sidebar.write("**Connected Nodes:**")
                            for node, rel_type, direction in connected_nodes:
                                node_name = node["properties"].get("name", node["properties"].get("id", node["id"]))
                                if direction == "outgoing":
                                    st.sidebar.write(f"→ {node['label']}: {node_name} ({rel_type})")
                                else:
                                    st.sidebar.write(f"← {node['label']}: {node_name} ({rel_type})")
    
    with tab2:
        st.subheader("Cypher Query")
        st.markdown("""
        Run custom Cypher queries against the Neo4j database.
        
        **Example queries:**
        ```cypher
        // Get all nodes
        MATCH (n) RETURN n LIMIT 10
        
        // Get specific node type
        MATCH (n:Customer) RETURN n LIMIT 10
        
        // Get relationships
        MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10
        ```
        """)
        
        # Query input
        cypher_query = st.text_area("Enter Cypher Query", "MATCH (n) RETURN n LIMIT 10")
        
        # Execute query
        if st.button("Run Query"):
            try:
                with st.spinner("Executing query..."):
                    results = st.session_state.neo4j.run_query(cypher_query)
                    
                    # Display results
                    if results:
                        # Convert to DataFrame if possible
                        try:
                            # Extract first 10 properties for each node/relationship
                            rows = []
                            for record in results:
                                row = {}
                                for key, value in record.items():
                                    if hasattr(value, 'items'):  # If it's a node or relationship
                                        # Extract properties
                                        props = dict(value)
                                        for prop_key, prop_value in list(props.items())[:10]:
                                            row[f"{key}.{prop_key}"] = prop_value
                                    else:
                                        row[key] = value
                                rows.append(row)
                            
                            if rows:
                                df = pd.DataFrame(rows)
                                st.dataframe(df)
                            else:
                                st.info("Query returned no rows.")
                        except Exception as e:
                            # Fallback to raw display
                            st.json([dict(record) for record in results])
                    else:
                        st.info("Query returned no results.")
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
    
    with tab3:
        st.subheader("Q&A with Knowledge Graph")
        st.markdown("""
        Ask questions about your data in natural language. The system will:
        1. Translate your question into a Cypher query
        2. Execute the query against the Neo4j database
        3. Format the results into a natural language answer
        """)
        
        # Initialize QA system if needed
        if 'qa_system' not in st.session_state:
            try:
                # Initialize Ollama client
                ollama_client = OllamaClient()
                st.session_state.qa_system = GraphQASystem(st.session_state.neo4j, ollama_client)
                st.success("✅ Connected to Ollama LLM service")
            except Exception as e:
                st.error(f"❌ Could not connect to Ollama: {str(e)}")
                st.info("Make sure Ollama is running locally with a model loaded.")
                st.session_state.qa_system = None
        
        # Question input
        question = st.text_input("Ask a question about your data", 
                                placeholder="e.g., Which customer placed the most orders?")
        
        show_details = st.checkbox("Show query details", value=False)
        
        if st.button("Ask Question"):
            if st.session_state.qa_system:
                with st.spinner("Thinking..."):
                    # Get answer
                    result = st.session_state.qa_system.answer_question(question)
                    
                    if result["success"]:
                        # Display answer
                        st.markdown("### Answer")
                        st.markdown(result["answer"])
                        
                        # Show query details if requested
                        if show_details:
                            with st.expander("Query Details"):
                                st.markdown("**Generated Cypher Query:**")
                                st.code(result["cypher_query"], language="cypher")
                                
                                st.markdown("**Query Results:**")
                                # Convert to DataFrame if possible
                                try:
                                    rows = []
                                    for record in result["query_results"]:
                                        row = {}
                                        for key, value in record.items():
                                            if hasattr(value, 'items'):  # If it's a node or relationship
                                                # Extract properties
                                                props = dict(value)
                                                for prop_key, prop_value in list(props.items())[:10]:
                                                    row[f"{key}.{prop_key}"] = prop_value
                                            else:
                                                row[key] = value
                                        rows.append(row)
                                    
                                    if rows:
                                        df = pd.DataFrame(rows)
                                        st.dataframe(df)
                                    else:
                                        st.info("Query returned no rows.")
                                except Exception as e:
                                    # Fallback to raw display
                                    st.json([dict(record) for record in result["query_results"]])
                    else:
                        st.error(result["answer"])
            else:
                st.error("LLM service not available. Please check Ollama connection.")
