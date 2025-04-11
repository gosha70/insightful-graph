# Insightful Graph 

A local AI-powered data analysis and knowledge graph system that allows you to:

- Upload datasets or connect to a database
- Analyze and summarize structured data
- Identify entities/relationships and convert them into a Neo4j knowledge graph
- Visualize the knowledge graph via a lightweight UI

## Prerequisites

- Python 3.8+
- Neo4j Database (local installation or cloud instance)
- Anaconda/Miniconda (recommended for environment management)

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

## Usage

1. Start the application:
   ```bash
   cd knowledge_graph_poc
   streamlit run app.py
   ```

2. The application will open in your web browser at `http://localhost:8501`

3. Use the sidebar to navigate between different sections:
   - **Data Upload**: Upload CSV files or use sample datasets
   - **Schema Analysis**: Review and modify the inferred schema
   - **Graph Builder**: Connect to Neo4j and build the knowledge graph
   - **Graph Visualization**: Visualize and explore the knowledge graph

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

### Knowledge Graph Generation

- Automatic creation of nodes and relationships in Neo4j
- Mapping of entities to graph nodes
- Mapping of relationships between entities
- Optimization with database constraints

### Graph Visualization

- Interactive visualization of the knowledge graph
- Filtering by node types
- Node selection and property inspection
- Relationship exploration

## Project Structure

```
knowledge_graph_poc/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── data/                  # Sample datasets
└── src/
    ├── data_loader.py     # Data loading and preprocessing
    ├── graph_builder.py   # Neo4j graph generation
    └── visualization.py   # Graph visualization components
```

## Future Enhancements

- Integration with local LLMs (via Ollama)
- RAG-based question answering with graph exploration
- Advanced data analysis with Pandas/Spark
- Support for unstructured data sources

## Troubleshooting

- **Neo4j Connection Issues**: Ensure Neo4j is running and the connection details (URI, username, password) are correct in the application.
- **Visualization Not Showing**: Check that you have built the knowledge graph before attempting to visualize it.
- **Missing Dependencies**: If you encounter errors about missing packages, try running `pip install -r requirements.txt` again.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
