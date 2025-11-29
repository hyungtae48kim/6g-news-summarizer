#!/bin/bash
# Setup script for 6G News Summarizer virtual environment

echo "======================================"
echo "6G News Summarizer - Environment Setup"
echo "======================================"

# Check if venv exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        echo "✅ Removed existing venv"
    else
        echo "ℹ️  Using existing venv"
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."

    # Try python3 -m venv first
    if python3 -m venv venv 2>/dev/null; then
        echo "✅ Virtual environment created with python3 -m venv"
    # Try virtualenv
    elif virtualenv venv 2>/dev/null; then
        echo "✅ Virtual environment created with virtualenv"
    else
        echo "❌ Failed to create virtual environment"
        echo ""
        echo "Please install python3-venv or virtualenv:"
        echo "  Ubuntu/Debian: sudo apt install python3-venv"
        echo "  Or: pip3 install virtualenv"
        exit 1
    fi
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing required packages..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "✅ Setup complete!"
echo "======================================"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the script:"
echo "  python scripts/fetch_6g_professional.py"
echo ""
echo "To deactivate:"
echo "  deactivate"
echo ""
