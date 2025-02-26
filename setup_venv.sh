#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dark Web Intelligence Scanner Virtual Environment Setup ===${NC}"
echo -e "${BLUE}Creating Python virtual environment...${NC}"

# Create virtual environment
python -m venv venv

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${BLUE}Installing dependencies from requirements.txt...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}To activate the virtual environment in the future, run:${NC}"
echo -e "    source venv/bin/activate"
echo -e "${GREEN}To deactivate the virtual environment, simply run:${NC}"
echo -e "    deactivate"
echo -e "${GREEN}To run the application, use:${NC}"
echo -e "    python app.py"
