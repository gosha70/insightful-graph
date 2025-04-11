import requests
import json
import logging
from typing import List, Dict, Any, Optional, Union
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        """Initialize Ollama client
        
        Args:
            base_url: URL of the Ollama API
            model: Name of the model to use
        """
        self.base_url = base_url
        self.model = model
        self.api_generate = f"{base_url}/api/generate"
        self.api_embeddings = f"{base_url}/api/embeddings"
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to Ollama API"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                
                if not available_models:
                    logging.warning("No models found in Ollama")
                    return False
                
                if self.model not in available_models:
                    logging.warning(f"Model {self.model} not found in Ollama. Available models: {available_models}")
                    # Set model to first available model
                    if available_models:
                        self.model = available_models[0]
                        logging.info(f"Using model {self.model} instead")
                
                logging.info(f"Connected to Ollama. Available models: {available_models}")
                return True
            else:
                logging.error(f"Failed to connect to Ollama: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logging.error(f"Error connecting to Ollama: {str(e)}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using Ollama
        
        Args:
            prompt: The prompt to generate text from
            system_prompt: Optional system prompt to guide the model
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(self.api_generate, json=payload)
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logging.error(f"Error generating text: {response.status_code} {response.text}")
                return f"Error: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error generating text: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for text
        
        Args:
            text: Text to get embeddings for
            
        Returns:
            List of embedding values
        """
        try:
            payload = {
                "model": self.model,
                "prompt": text
            }
            
            response = requests.post(self.api_embeddings, json=payload)
            
            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                logging.error(f"Error getting embeddings: {response.status_code} {response.text}")
                return []
        except Exception as e:
            logging.error(f"Error getting embeddings: {str(e)}")
            return []


class GraphQASystem:
    """System for answering questions about a knowledge graph using LLMs"""
    
    def __init__(self, neo4j_connector, ollama_client: Optional[OllamaClient] = None):
        """Initialize Graph QA System
        
        Args:
            neo4j_connector: Connector to Neo4j database
            ollama_client: Client for Ollama API
        """
        self.neo4j = neo4j_connector
        
        # Initialize Ollama client if not provided
        if ollama_client is None:
            try:
                self.ollama = OllamaClient()
            except Exception as e:
                logging.error(f"Error initializing Ollama client: {str(e)}")
                self.ollama = None
        else:
            self.ollama = ollama_client
    
    def get_graph_schema(self) -> str:
        """Get schema of the graph as a string
        
        Returns:
            String representation of the graph schema
        """
        try:
            # Get node labels
            labels_query = "CALL db.labels() YIELD label RETURN collect(label) as labels"
            labels_result = self.neo4j.run_query(labels_query)
            labels = labels_result[0]["labels"] if labels_result else []
            
            # Get relationship types
            rel_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types"
            rel_result = self.neo4j.run_query(rel_query)
            rel_types = rel_result[0]["types"] if rel_result else []
            
            # Get property keys for each node label
            schema = []
            for label in labels:
                prop_query = f"""
                MATCH (n:{label}) 
                WITH n LIMIT 1 
                RETURN keys(n) as properties
                """
                prop_result = self.neo4j.run_query(prop_query)
                properties = prop_result[0]["properties"] if prop_result else []
                
                schema.append(f"Node Label: {label}")
                schema.append(f"Properties: {', '.join(properties)}")
                schema.append("")
            
            # Add relationship information
            schema.append("Relationships:")
            for rel_type in rel_types:
                rel_info_query = f"""
                MATCH (a)-[r:{rel_type}]->(b)
                WITH labels(a)[0] as source_label, labels(b)[0] as target_label, r
                LIMIT 1
                RETURN source_label, target_label, keys(r) as properties
                """
                rel_info = self.neo4j.run_query(rel_info_query)
                
                if rel_info:
                    source = rel_info[0]["source_label"]
                    target = rel_info[0]["target_label"]
                    props = rel_info[0]["properties"]
                    
                    schema.append(f"({source})-[:{rel_type}]->({target})")
                    if props:
                        schema.append(f"Properties: {', '.join(props)}")
                    schema.append("")
            
            return "\n".join(schema)
        except Exception as e:
            logging.error(f"Error getting graph schema: {str(e)}")
            return "Error retrieving schema"
    
    def generate_cypher_query(self, question: str) -> str:
        """Generate Cypher query from natural language question
        
        Args:
            question: Natural language question
            
        Returns:
            Cypher query
        """
        if not self.ollama:
            return "Error: Ollama client not available"
        
        # Get graph schema
        schema = self.get_graph_schema()
        
        # Create prompt for query generation
        system_prompt = """
        You are an expert in translating natural language questions into Cypher queries for Neo4j.
        Given a graph schema and a question, generate a Cypher query that answers the question.
        Only return the Cypher query, nothing else.
        """
        
        prompt = f"""
        Graph Schema:
        {schema}
        
        Question: {question}
        
        Cypher Query:
        """
        
        # Generate query
        cypher_query = self.ollama.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,  # Lower temperature for more deterministic output
            max_tokens=500
        )
        
        # Clean up the query
        cypher_query = cypher_query.strip()
        
        return cypher_query
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question about the knowledge graph
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with answer and metadata
        """
        if not self.ollama:
            return {"answer": "Error: Ollama client not available", "success": False}
        
        try:
            # Generate Cypher query
            cypher_query = self.generate_cypher_query(question)
            
            # Execute query
            results = self.neo4j.run_query(cypher_query)
            
            # Format results as text
            result_text = self._format_results(results)
            
            # Generate answer
            system_prompt = """
            You are a helpful assistant that answers questions based on database query results.
            Provide a clear, concise answer based on the data provided.
            If the data doesn't answer the question, say so clearly.
            """
            
            prompt = f"""
            Question: {question}
            
            Query Results:
            {result_text}
            
            Answer:
            """
            
            answer = self.ollama.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "answer": answer,
                "cypher_query": cypher_query,
                "query_results": results,
                "success": True
            }
        except Exception as e:
            logging.error(f"Error answering question: {str(e)}")
            return {
                "answer": f"Error: {str(e)}",
                "success": False
            }
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format query results as text
        
        Args:
            results: List of result records
            
        Returns:
            Formatted text
        """
        if not results:
            return "No results found."
        
        lines = []
        
        # Get all keys from all results
        all_keys = set()
        for record in results:
            all_keys.update(record.keys())
        
        # Format as table
        header = " | ".join(all_keys)
        lines.append(header)
        lines.append("-" * len(header))
        
        for record in results:
            row = []
            for key in all_keys:
                value = record.get(key, "")
                
                # Handle nodes and relationships
                if hasattr(value, "items"):
                    # It's a node or relationship, extract properties
                    props = dict(value)
                    value_str = ", ".join(f"{k}: {v}" for k, v in props.items())
                    row.append(value_str)
                else:
                    row.append(str(value))
            
            lines.append(" | ".join(row))
        
        return "\n".join(lines)
