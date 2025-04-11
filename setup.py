#!/usr/bin/env python
"""
Setup script for Knowledge Graph Builder.
This script helps users set up their environment and install the required dependencies.
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        print(f"Current Python version: {platform.python_version()}")
        return False
    print(f"Python version {platform.python_version()} is compatible.")
    return True

def check_neo4j():
    """Check if Neo4j is installed and accessible."""
    print("Checking Neo4j installation...")
    try:
        # Try to import the Neo4j driver
        import neo4j
        print(f"Neo4j driver version {neo4j.__version__} is installed.")
        
        # Check if Neo4j is running
        from neo4j import GraphDatabase
        try:
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
            with driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            driver.close()
            print("Successfully connected to Neo4j database.")
            return True
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j database: {str(e)}")
            print("Please make sure Neo4j is running and accessible at bolt://localhost:7687")
            print("Default credentials are username: neo4j, password: password")
            print("You can change these in the application settings.")
            return False
    except ImportError:
        print("Neo4j driver is not installed. It will be installed with the requirements.")
        return False

def install_requirements():
    """Install required packages from requirements.txt."""
    print("Installing required packages...")
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Successfully installed required packages.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {str(e)}")
        return False

def create_data_directory():
    """Create data directory if it doesn't exist."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        print("Creating data directory...")
        os.makedirs(data_dir)
        print(f"Created data directory at {data_dir}")
    else:
        print(f"Data directory already exists at {data_dir}")
    return True

def main():
    """Main setup function."""
    print("=" * 60)
    print("Knowledge Graph Builder Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create data directory
    if not create_data_directory():
        return False
    
    # Check Neo4j installation
    check_neo4j()
    
    print("\nSetup completed successfully!")
    print("\nTo start the application, run:")
    print("    streamlit run app.py")
    print("\nMake sure Neo4j is running before starting the application.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    main()
