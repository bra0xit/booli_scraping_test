#!/bin/bash

echo "=================================="
echo "Booli Apartment Scraper - Quick Start"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "SETUP_GUIDE.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check Node
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

echo "✓ Node found: $(node --version)"

# Setup backend
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✓ Backend setup complete!"
echo ""
echo "=================================="
echo "Starting servers..."
echo "=================================="
echo ""
echo "Backend will run on: http://localhost:5002"
echo "Frontend will run on: http://localhost:3002"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start backend in background
python app.py &
BACKEND_PID=$!

# Setup and start frontend
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (this may take a minute)..."
    npm install
fi

# Start frontend (this will open the browser)
npm start &
FRONTEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Wait for both processes
wait
