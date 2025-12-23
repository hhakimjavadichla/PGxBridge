#!/bin/bash

# PGX Parser - Migration Script to Miniforge3
# This script creates a new conda environment in Miniforge3

set -e  # Exit on error

echo "🔄 PGX Parser Environment Migration"
echo "===================================="
echo ""
echo "This will create a new 'pgx_parser' environment in Miniforge3"
echo "Your current 'pgxbridge_env' will remain untouched as backup"
echo ""

# Confirm
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")"

echo ""
echo "📦 Step 1: Creating backup..."
if [ -f "pgxbridge_env_backup.yml" ]; then
    echo "✅ Backup already exists: pgxbridge_env_backup.yml"
else
    conda env export > pgxbridge_env_backup.yml
    pip list > pgxbridge_env_packages.txt
    echo "✅ Backup created: pgxbridge_env_backup.yml"
fi

echo ""
echo "🆕 Step 2: Creating new environment 'pgx_parser'..."
if conda env list | grep -q "^pgx_parser "; then
    echo "⚠️  Environment 'pgx_parser' already exists"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        conda env remove -n pgx_parser -y
        echo "✅ Old environment removed"
    else
        echo "❌ Keeping existing environment"
        exit 1
    fi
fi

conda create -n pgx_parser python=3.11 -y
echo "✅ Environment created"

echo ""
echo "📥 Step 3: Installing dependencies..."
eval "$(conda shell.bash hook)"
conda activate pgx_parser

cd pgx-parser-backend-py
pip install -r requirements.txt
echo "✅ Dependencies installed"

echo ""
echo "🔍 Step 4: Verifying installation..."
echo "Python version: $(python --version)"
echo ""
echo "Installed packages:"
pip list | grep -E "fastapi|uvicorn|pypdf|azure|openai"

echo ""
echo "✅ Migration complete!"
echo ""
echo "📝 Next steps:"
echo "1. Test the backend: conda activate pgx_parser && cd pgx-parser-backend-py && uvicorn main:app --reload --port 8000"
echo "2. Test with a sample PDF"
echo "3. If everything works, update your scripts to use 'pgx_parser'"
echo ""
echo "🔄 To rollback: conda env create -f pgxbridge_env_backup.yml"
echo ""
