#!/usr/bin/env python
"""
Run script for Knowledge Graph Builder.
This script provides a simple way to start the application.
"""

import os
import sys
import subprocess
import webbrowser
import time
import platform

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import streamlit
        import pandas
        import neo4j
        import networkx
        import matplotlib
        return True
    except ImportError as e:
        print(f"Missing dependency: {str(e)}")
        print("Please run setup.py first to install all required dependencies.")
        return False

def check_neo4j_running():
    """Check if Neo4j is running."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
        driver.close()
        return True
    except Exception:
        return False

def start_application():
    """Start the Streamlit application."""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    
    if not os.path.exists(app_path):
        print(f"Error: app.py not found at {app_path}")
        return False
    
    print("Starting Knowledge Graph Builder application...")
    
    # Start Streamlit in a new process
    if platform.system() == "Windows":
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path]
        )
    
    # Wait for Streamlit to start
    print("Waiting for application to start...")
    time.sleep(3)
    
    # Open web browser
    webbrowser.open("http://localhost:8501")
    
    print("Application started at http://localhost:8501")
    print("Press Ctrl+C to stop the application.")
    
    try:
        # Keep the script running until user interrupts
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping application...")
        process.terminate()
        print("Application stopped.")
    
    return True

def main():
    """Main run function."""
    print("=" * 60)
    print("Knowledge Graph Builder")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check if Neo4j is running
    if not check_neo4j_running():
        print("Warning: Neo4j database is not running or not accessible.")
        print("Please make sure Neo4j is running before using the application.")
        print("Default connection: bolt://localhost:7687")
        print("Default credentials: username=neo4j, password=password")
        
        # Ask user if they want to continue
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting. Please start Neo4j and try again.")
            return False
    
    # Start application
    return start_application()

if __name__ == "__main__":
    main()
