#!/bin/bash

# Exit on error
set -e

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
status() {
    echo -e "${GREEN}[*]${NC} $1"
}

# Function to print warnings
warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if we're in the script's directory.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Change to the script's directory to ensure relative paths work correctly.
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    status "Creating virtual environment..."
    python3 -m venv venv
    
    # Activate the virtual environment
    source venv/bin/activate
    
    # Install requirements
    status "Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    # Activate the virtual environment
    source venv/bin/activate
fi

# Clean up previous files
status "Cleaning up previous files..."
rm -f heart_rate_analysis.png synthetic_device1.tcx synthetic_device2.tcx

# Generate synthetic TCX files with a random seed
status "Generating synthetic TCX files..."
python generate_synthetic_tcx.py

# Run analysis
status "Running analysis..."
python analyze.py synthetic_device1.tcx synthetic_device2.tcx

# Open the generated plot
if command -v xdg-open &> /dev/null; then
    status "Opening heart_rate_analysis.png..."
    xdg-open heart_rate_analysis.png
else
    warning "xdg-open not found. Please open heart_rate_analysis.png manually."
fi

status "Done!"
