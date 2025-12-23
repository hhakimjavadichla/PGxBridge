#!/bin/bash

# PGX Parser - Backend Startup Script

echo "🚀 Starting PGX Parser Backend..."
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda not found. Please install Anaconda or Miniconda."
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")/pgx-parser-backend-py" || exit 1

# Check if pgxbridge_env exists
if ! conda env list | grep -q "pgxbridge_env"; then
    echo "⚠️  pgxbridge_env not found. Creating it..."
    conda create -n pgxbridge_env python=3.11 -y
fi

# Activate environment
echo "📦 Activating pgxbridge_env..."
eval "$(conda shell.bash hook)"
# Use full path to handle multiple conda installations
conda activate /Users/hhakimjavadi/opt/anaconda3/envs/pgxbridge_env 2>/dev/null || conda activate pgxbridge_env

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file with your Azure credentials."
    echo "Required variables:"
    echo "  - AZURE_DI_ENDPOINT"
    echo "  - AZURE_DI_KEY"
    echo "  - AZURE_OPENAI_API_KEY"
    echo "  - AZURE_OPENAI_ENDPOINT"
    echo "  - AZURE_OPENAI_DEPLOYMENT_NAME"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the server
echo ""
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn main:app --reload --port 8000
