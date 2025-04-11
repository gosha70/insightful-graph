# Insightful Graph 

A local AI-powered data analysis and knowledge graph system that allows you to:

- Upload datasets or connect to a database
- Analyze and summarize structured data
- Identify entities/relationships and convert them into a Neo4j knowledge graph
- Visualize and query the knowledge graph via a lightweight UI
- Ask natural language questions about your data using LLM integration

## Prerequisites

- Python 3.8+
- Neo4j Database (local installation or cloud instance)
- Anaconda/Miniconda (recommended for environment management)
- Ollama (for LLM-powered Q&A features)

## Installation

1. Clone this repository or download the source code.

2. Create a new conda environment:
   ```bash
   conda create -n insightful-graph python=3.11
   conda activate insightful-graph
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install and start Neo4j:
   - Download and install [Neo4j Desktop](https://neo4j.com/download/)
   - Create a new database with a password (default username is "neo4j")
   - Start the database

5. Install Ollama (for LLM features):
   - Download and install [Ollama](https://ollama.ai/download)
   - Run a model: `ollama run llama2` (or any other model you prefer)

## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. The application will open in your web browser at `http://localhost:8501`

3. Follow the guided workflow:
   - **Data Upload**: Upload CSV files, connect to a database, or use sample datasets
   - **Data Analysis**: Review and modify the inferred schema and entity relationships
   - **Graph Builder**: Connect to Neo4j and build the knowledge graph
   - **Graph Analysis**: Visualize, query, and ask questions about your knowledge graph

## Features

### Data Ingestion

- Upload CSV files
- Connect to SQL databases (requires connection string)
- Use built-in sample datasets
- Automatic data cleaning and preprocessing

### Schema Analysis

- Automatic detection of column types and roles
- Identification of potential entity identifiers
- Discovery of relationships between entities
- Manual adjustment of schema
- Entity detection and property mapping

### Knowledge Graph Generation

- Automatic creation of nodes and relationships in Neo4j
- Mapping of entities to graph nodes
- Mapping of relationships between entities
- Optimization with database constraints
- Detailed statistics and feedback

### Graph Analysis

- Interactive visualization of the knowledge graph
- Filtering by node types and properties
- Node selection and property inspection
- Relationship exploration
- Custom Cypher query execution
- Natural language Q&A using LLM integration

## Project Structure

```
insightful-graph/
├── app.py                 # Main Streamlit application entry point
├── pages/                 # Multi-page Streamlit application
│   ├── 1_Data_Upload.py   # Data ingestion page
│   ├── 2_Data_Analysis.py # Schema analysis page
│   ├── 3_Graph_Builder.py # Graph building page
│   └── 4_Graph_Analysis.py # Visualization and Q&A page
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── data/                  # Sample datasets
└── src/
    ├── data_loader.py     # Data loading and preprocessing
    ├── graph_builder.py   # Neo4j graph generation
    ├── visualization.py   # Graph visualization components
    └── llm_integration.py # LLM integration for Q&A
```

## LLM Integration

The application integrates with Ollama to provide natural language question answering capabilities:

1. **Schema-aware queries**: The system extracts the graph schema and uses it to guide the LLM in generating accurate Cypher queries.
2. **RAG approach**: The system retrieves relevant data from the graph database and uses it to generate accurate answers.
3. **Transparent results**: You can view the generated Cypher queries and raw results alongside the natural language answers.

## Troubleshooting

- **Neo4j Connection Issues**: Ensure Neo4j is running and the connection details (URI, username, password) are correct in the application.
- **Visualization Not Showing**: Check that you have built the knowledge graph before attempting to visualize it.
- **Missing Dependencies**: If you encounter errors about missing packages, try running `pip install -r requirements.txt` again.
- **Ollama Connection Issues**: Ensure Ollama is running and a model is loaded. Check the logs for connection errors.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
