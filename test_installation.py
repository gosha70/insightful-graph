#!/usr/bin/env python
"""
Test script for Knowledge Graph Builder.
This script verifies that all components are working correctly.
"""

import os
import sys
import importlib
import platform
from neo4j import GraphDatabase
        
NEO4J_URL = "bolt://localhost:7687"

def print_status(component, status, message=""):
    """Print the status of a component."""
    status_str = "✓" if status else "✗"
    print(f"{status_str} {component:<30} {message}")

def test_python_version():
    """Test Python version."""
    version = platform.python_version()
    status = sys.version_info >= (3, 8)
    message = f"Version: {version}" + (" (3.8+ required)" if not status else "")
    print_status("Python Version", status, message)
    return status

def test_dependency(name):
    """Test if a dependency is installed."""
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "unknown")
        print_status(name, True, f"Version: {version}")
        return True
    except ImportError:
        print_status(name, False, "Not installed")
        return False

def test_neo4j_connection():
    """Test connection to Neo4j."""
    try:
        driver = GraphDatabase.driver(NEO4J_URL, auth=("neo4j", "password"))
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
        driver.close()
        print_status("Neo4j Connection", True, "Connected to " + NEO4J_URL)
        return True
    except Exception as e:
        print_status("Neo4j Connection", False, f"Error: {str(e)}")
        return False

def test_file_exists(path, name):
    """Test if a file exists."""
    full_path = os.path.join(os.path.dirname(__file__), path)
    status = os.path.exists(full_path)
    message = f"Path: {full_path}"
    print_status(name, status, message)
    return status

def main():
    """Main test function."""
    print("=" * 60)
    print("Knowledge Graph Builder - Installation Test")
    print("=" * 60)
    
    # Test Python version
    python_status = test_python_version()
    
    # Test dependencies
    print("\nTesting dependencies:")
    pandas_status = test_dependency("pandas")
    numpy_status = test_dependency("numpy")
    streamlit_status = test_dependency("streamlit")
    neo4j_status = test_dependency("neo4j")
    matplotlib_status = test_dependency("matplotlib")
    networkx_status = test_dependency("networkx")
    
    # Test Neo4j connection
    print("\nTesting Neo4j connection:")
    neo4j_conn_status = test_neo4j_connection()
    
    # Test file structure
    print("\nTesting file structure:")
    app_status = test_file_exists("app.py", "Main Application")
    data_loader_status = test_file_exists("src/data_loader.py", "Data Loader Module")
    graph_builder_status = test_file_exists("src/graph_builder.py", "Graph Builder Module")
    visualization_status = test_file_exists("src/visualization.py", "Visualization Module")
    requirements_status = test_file_exists("requirements.txt", "Requirements File")
    readme_status = test_file_exists("README.md", "README File")
    
    # Test sample data
    print("\nTesting sample data:")
    sample1_status = test_file_exists("data/sample_customer_orders.csv", "Customer Orders Sample")
    sample2_status = test_file_exists("data/sample_movies.csv", "Movies Sample")
    
    # Calculate overall status
    dependency_status = all([
        pandas_status, numpy_status, streamlit_status, 
        neo4j_status, matplotlib_status, networkx_status
    ])
    
    file_status = all([
        app_status, data_loader_status, graph_builder_status, 
        visualization_status, requirements_status, readme_status
    ])
    
    sample_status = any([sample1_status, sample2_status])
    
    overall_status = python_status and dependency_status and file_status
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Python Version: {'OK' if python_status else 'FAILED'}")
    print(f"Dependencies: {'OK' if dependency_status else 'FAILED'}")
    print(f"Neo4j Connection: {'OK' if neo4j_conn_status else 'WARNING'}")
    print(f"File Structure: {'OK' if file_status else 'FAILED'}")
    print(f"Sample Data: {'OK' if sample_status else 'WARNING'}")
    print("-" * 60)
    print(f"Overall Status: {'OK' if overall_status else 'FAILED'}")
    
    if not neo4j_conn_status:
        print("\nWarning: Neo4j connection failed. Make sure Neo4j is running.")
        print("You can still use the application, but you won't be able to build or visualize graphs.")
    
    if not sample_status:
        print("\nWarning: Sample data files not found.")
        print("You can still use the application with your own data.")
    
    if not overall_status:
        print("\nSome tests failed. Please fix the issues before using the application.")
        print("You can run setup.py to install dependencies and create the required directories.")
    else:
        print("\nAll critical tests passed! You can now run the application.")
        print("To start the application, run: python run.py")
    
    print("=" * 60)
    
    return overall_status

if __name__ == "__main__":
    main()
