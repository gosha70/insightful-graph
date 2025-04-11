import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from streamlit_agraph import agraph, Node, Edge, Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GraphVisualizer:
    def __init__(self, neo4j_connector):
        """Initialize with a Neo4j connector"""
        self.neo4j = neo4j_connector
        
        # Color map for different node types
        self.color_map = {
            "Customer": "#6baed6",  # blue
            "Product": "#fd8d3c",   # orange
            "Order": "#74c476",     # green
            "User": "#9e9ac8",      # purple
            "Movie": "#ff9896",     # red
            "Actor": "#c5b0d5",     # lavender
            "Entity": "#c7c7c7"     # gray (default)
        }
    
    def get_graph_data(self, limit=50, labels=None):
        """Query Neo4j for graph data to visualize"""
        logging.info(f"Getting graph data with limit {limit} and labels {labels}")
        
        # Build query based on filters
        if labels and len(labels) > 0:
            label_conditions = " OR ".join([f"n:{label}" for label in labels])
            nodes_query = f"MATCH (n) WHERE {label_conditions} RETURN n, labels(n) as labels LIMIT {limit}"
            edges_query = f"""
            MATCH (a)-[r]->(b) 
            WHERE ({label_conditions}) AND ({' OR '.join([f"b:{label}" for label in labels])})
            RETURN a, type(r) as type, b, labels(a) as a_labels, labels(b) as b_labels LIMIT {limit * 2}
            """
        else:
            nodes_query = f"MATCH (n) RETURN n, labels(n) as labels LIMIT {limit}"
            edges_query = f"MATCH (a)-[r]->(b) RETURN a, type(r) as type, b, labels(a) as a_labels, labels(b) as b_labels LIMIT {limit * 2}"
        
        # Execute queries
        try:
            nodes_result = self.neo4j.run_query(nodes_query)
            edges_result = self.neo4j.run_query(edges_query)
            
            # Process nodes
            nodes = []
            node_ids = {}  # Map Neo4j IDs to our node IDs
            
            for i, record in enumerate(nodes_result):
                node = record["n"]
                label = record["labels"][0] if record["labels"] else "Entity"
                
                # Get node properties
                props = dict(node)
                
                # Create a readable label
                if "name" in props:
                    node_label = f"{label}: {props['name']}"
                elif "id" in props:
                    node_label = f"{label}: {props['id']}"
                else:
                    # Use first property as label
                    first_prop = list(props.keys())[0] if props else "unknown"
                    node_label = f"{label}: {props.get(first_prop, node.id)}"
                
                # Store node
                node_id = f"n{i}"
                node_ids[node.id] = node_id
                
                nodes.append({
                    "id": node_id,
                    "neo4j_id": node.id,
                    "label": label,
                    "title": node_label,
                    "properties": props
                })
            
            # Process edges
            edges = []
            for record in edges_result:
                source_node = record["a"]
                target_node = record["b"]
                rel_type = record["type"]
                
                # Skip if we don't have both nodes
                if source_node.id not in node_ids or target_node.id not in node_ids:
                    continue
                
                # Create edge
                edges.append({
                    "source": node_ids[source_node.id],
                    "target": node_ids[target_node.id],
                    "label": rel_type
                })
            
            return {
                "nodes": nodes,
                "edges": edges
            }
        
        except Exception as e:
            logging.error(f"Error getting graph data: {str(e)}")
            return {"nodes": [], "edges": []}
    
    def display_graph(self, graph_data):
        """Display the graph using streamlit-agraph"""
        if not graph_data["nodes"]:
            st.warning("No nodes to display. Try adjusting your filters.")
            return
        
        # Convert to agraph format
        nodes = []
        edges = []
        
        for node in graph_data["nodes"]:
            # Get color for node type
            color = self.color_map.get(node["label"], "#c7c7c7")
            
            nodes.append(Node(
                id=node["id"],
                label=node["title"],
                size=25,
                color=color
            ))
        
        for edge in graph_data["edges"]:
            edges.append(Edge(
                source=edge["source"],
                target=edge["target"],
                label=edge["label"]
            ))
        
        # Configure visualization
        config = Config(
            width=800,
            height=600,
            directed=True,
            physics=True,
            hierarchical=False,
            node_size=1000,
            node_color="#1f77b4",
            node_opacity=0.9,
            node_label_property="label",
            edge_color="#7c7c7c",
            edge_width=2,
            edge_curved=0.1
        )
        
        # Display graph
        st.subheader("Knowledge Graph Visualization")
        agraph(nodes=nodes, edges=edges, config=config)
        
        # Display stats
        st.caption(f"Displaying {len(nodes)} nodes and {len(edges)} relationships")
    
    def display_networkx_graph(self, graph_data):
        """Alternative visualization using NetworkX and matplotlib"""
        if not graph_data["nodes"]:
            st.warning("No nodes to display. Try adjusting your filters.")
            return
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_data["nodes"]:
            G.add_node(node["id"], label=node["title"], node_type=node["label"])
        
        # Add edges
        for edge in graph_data["edges"]:
            G.add_edge(edge["source"], edge["target"], label=edge["label"])
        
        # Create plot
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G, seed=42)
        
        # Draw nodes with colors based on type
        node_colors = [self.color_map.get(G.nodes[n]["node_type"], "#c7c7c7") for n in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, arrows=True, arrowsize=15)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, labels={n: G.nodes[n]["label"] for n in G.nodes()}, font_size=8)
        
        plt.axis("off")
        plt.tight_layout()
        
        # Display in Streamlit
        st.subheader("Knowledge Graph Visualization (NetworkX)")
        st.pyplot(plt)
        
        # Display stats
        st.caption(f"Displaying {len(G.nodes)} nodes and {len(G.edges)} relationships")
