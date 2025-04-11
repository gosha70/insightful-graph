from neo4j import GraphDatabase
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Neo4jConnector:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        """Initialize connection to Neo4j"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connect()
    
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            logging.info("Connected to Neo4j successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {str(e)}")
            return False
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def run_query(self, query, parameters=None):
        """Run a Cypher query and return results"""
        if not self.driver:
            if not self.connect():
                raise Exception("Not connected to Neo4j")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return list(result)
        except Exception as e:
            logging.error(f"Error executing query: {str(e)}")
            raise
    
    def clear_database(self):
        """Remove all nodes and relationships from the database"""
        self.run_query("MATCH (n) DETACH DELETE n")
        logging.info("Database cleared")


class GraphBuilder:
    def __init__(self, connector):
        """Initialize with a Neo4j connector"""
        self.connector = connector
    
    def build_graph_from_dataframe(self, df, schema):
        """Build a graph from a dataframe using the provided schema"""
        logging.info("Building graph from dataframe")
        
        # Create constraints for faster lookups
        self._create_constraints(schema)
        
        # Identify entity columns and property columns
        id_columns = [col for col, info in schema["columns"].items() 
                     if info["role"] == "identifier"]
        
        if not id_columns:
            # If no ID columns found, use the first column as ID
            id_columns = [df.columns[0]]
            logging.warning(f"No identifier columns found. Using {id_columns[0]} as identifier.")
        
        # Create nodes for each entity type
        for id_column in id_columns:
            entity_type = id_column.replace("_id", "").title()
            self._create_entity_nodes(df, entity_type, id_column, schema)
        
        # Create relationships based on detected relationships
        for relationship in schema["relationships"]:
            self._create_relationships(df, relationship)
        
        # Return statistics
        return self._get_graph_statistics()
    
    def _create_constraints(self, schema):
        """Create constraints for ID columns"""
        try:
            # For Neo4j 5.x+
            self.connector.run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
            
            # Create constraints for each entity type
            id_columns = [col for col, info in schema["columns"].items() 
                         if info["role"] == "identifier"]
            
            for id_column in id_columns:
                entity_type = id_column.replace("_id", "").title()
                try:
                    # Try Neo4j 5.x+ syntax first
                    self.connector.run_query(
                        f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity_type}) REQUIRE n.id IS UNIQUE"
                    )
                except Exception as e:
                    # Fallback to Neo4j 4.x syntax
                    try:
                        self.connector.run_query(
                            f"CREATE CONSTRAINT IF NOT EXISTS ON (n:{entity_type}) ASSERT n.id IS UNIQUE"
                        )
                    except Exception as e2:
                        logging.warning(f"Could not create constraint for {entity_type}: {str(e2)}")
        except Exception as e:
            # Fallback for if constraints already exist or other issues
            logging.warning(f"Could not create constraints: {str(e)}")
    
    def _create_entity_nodes(self, df, entity_type, id_column, schema):
        """Create nodes for each unique entity"""
        logging.info(f"Creating {entity_type} nodes from column {id_column}")
        
        # Get unique entities
        unique_entities = df[[id_column]].drop_duplicates()
        
        # Get property columns for this entity
        property_columns = []
        for col in df.columns:
            if col != id_column and not col.endswith("_id"):
                property_columns.append(col)
        
        # Create Cypher query
        property_assignments = []
        for col in property_columns:
            if col in df.columns:
                property_assignments.append(f'{col}: row.{col}')
        
        property_string = ", ".join(property_assignments) if property_assignments else ""
        
        cypher = f"""
        UNWIND $rows AS row
        MERGE (e:{entity_type} {{id: row.{id_column}}})
        """
        
        if property_string:
            cypher += f"SET e += {{ {property_string} }}"
        
        # Execute in batches
        batch_size = 500
        total_entities = len(unique_entities)
        
        for i in range(0, total_entities, batch_size):
            end_idx = min(i + batch_size, total_entities)
            batch = df.iloc[i:end_idx].to_dict('records')
            self.connector.run_query(cypher, {"rows": batch})
            
            logging.info(f"Created {end_idx}/{total_entities} {entity_type} nodes")
    
    def _create_relationships(self, df, relationship):
        """Create relationships between nodes"""
        source_col = relationship["source"]
        target_col = relationship["target"]
        rel_type = relationship["type"].upper()
        
        logging.info(f"Creating {rel_type} relationships from {source_col} to {target_col}")
        
        # Determine entity types
        source_type = source_col.replace("_id", "").title()
        target_type = target_col.replace("_id", "").title()
        
        # Create Cypher query
        cypher = f"""
        MATCH (source:{source_type} {{id: $source_id}})
        MATCH (target:{target_type} {{id: $target_id}})
        MERGE (source)-[:{rel_type}]->(target)
        """
        
        # Get unique source-target pairs
        relationships_df = df[[source_col, target_col]].drop_duplicates().dropna()
        
        # Execute in batches
        batch_size = 1000
        total_rels = len(relationships_df)
        
        for i in range(0, total_rels, batch_size):
            end_idx = min(i + batch_size, total_rels)
            batch = relationships_df.iloc[i:end_idx]
            
            for _, row in batch.iterrows():
                try:
                    self.connector.run_query(
                        cypher, 
                        {"source_id": row[source_col], "target_id": row[target_col]}
                    )
                except Exception as e:
                    logging.error(f"Error creating relationship: {str(e)}")
            
            logging.info(f"Created {end_idx}/{total_rels} {rel_type} relationships")
    
    def _get_graph_statistics(self):
        """Get statistics about the graph"""
        logging.info("Retrieving graph statistics")
        
        node_count_query = "MATCH (n) RETURN count(n) as count"
        rel_count_query = "MATCH ()-[r]->() RETURN count(r) as count"
        label_count_query = "MATCH (n) RETURN distinct labels(n) as label, count(*) as count"
        rel_type_query = "MATCH ()-[r]->() RETURN distinct type(r) as type, count(*) as count"
        
        try:
            node_count = self.connector.run_query(node_count_query)[0]["count"]
            rel_count = self.connector.run_query(rel_count_query)[0]["count"]
            label_counts = self.connector.run_query(label_count_query)
            rel_type_counts = self.connector.run_query(rel_type_query)
            
            return {
                "node_count": node_count,
                "relationship_count": rel_count,
                "labels": {record["label"][0]: record["count"] for record in label_counts},
                "relationship_types": {record["type"]: record["count"] for record in rel_type_counts}
            }
        except Exception as e:
            logging.error(f"Error getting graph statistics: {str(e)}")
            return {
                "node_count": 0,
                "relationship_count": 0,
                "labels": {},
                "relationship_types": {}
            }
