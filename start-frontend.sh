#!/bin/bash

# PGX Parser - Frontend Startup Script

echo "🚀 Starting PGX Parser Frontend..."
echo ""

# Check if node is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js not found. Please install Node.js 18+."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm not found. Please install npm."
    exit 1
fi

# Navigate to frontend directory
cd "$(dirname "$0")/pgx-parser-ui" || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    npm install
else
    echo "✅ Dependencies already installed"
fi

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "⚠️  Warning: Backend not detected at http://localhost:8000"
    echo "Please start the backend first using: ./start-backend.sh"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the React app
echo ""
echo "✅ Starting React app on http://localhost:3000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

npm start
