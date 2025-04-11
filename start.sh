#!/bin/bash
# Start script for Knowledge Graph Builder
# This script helps users set up and run the application in one step

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}Knowledge Graph Builder - Quick Start${NC}"
echo -e "${GREEN}=================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.8 or higher and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_VERSION_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_VERSION_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_VERSION_MAJOR" -lt 3 ] || ([ "$PYTHON_VERSION_MAJOR" -eq 3 ] && [ "$PYTHON_VERSION_MINOR" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8 or higher is required${NC}"
    echo "Current Python version: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}Python version:${NC} $PYTHON_VERSION"

# Check if Neo4j is running
echo -e "\n${GREEN}Checking Neo4j status...${NC}"
if python3 -c "
import sys
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
    with driver.session() as session:
        result = session.run('RETURN 1 AS test')
        result.single()
    driver.close()
    sys.exit(0)
except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit(1)
" &> /dev/null; then
    echo -e "${GREEN}Neo4j is running${NC}"
    NEO4J_RUNNING=true
else
    echo -e "${YELLOW}Warning: Neo4j is not running or not accessible${NC}"
    echo "You can still use the application, but you won't be able to build or visualize graphs"
    echo "Please make sure Neo4j is running and accessible at bolt://localhost:7687"
    echo "Default credentials: username=neo4j, password=password"
    NEO4J_RUNNING=false
    
    # Ask user if they want to continue
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please start Neo4j and try again."
        exit 1
    fi
fi

# Check if dependencies are installed
echo -e "\n${GREEN}Checking dependencies...${NC}"
if ! python3 -c "
import sys
try:
    import streamlit
    import pandas
    import neo4j
    import networkx
    import matplotlib
    sys.exit(0)
except ImportError as e:
    print(f'Missing dependency: {str(e)}')
    sys.exit(1)
"; then
    echo -e "${YELLOW}Some dependencies are missing. Running setup...${NC}"
    
    # Run setup script
    python3 setup.py
    
    # Check if setup was successful
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Setup failed${NC}"
        echo "Please run setup.py manually and check for errors"
        exit 1
    fi
else
    echo -e "${GREEN}All dependencies are installed${NC}"
fi

# Start the application
echo -e "\n${GREEN}Starting Knowledge Graph Builder...${NC}"
python3 run.py

# Exit with the status of the run script
exit $?
