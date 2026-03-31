#!/bin/bash
# CEO Command Center — Launch script
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "Warning: .env not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your credentials."
fi

# Initialize database if not exists
if [ ! -f "data/ceo_command_center.db" ]; then
    echo "Initializing database..."
    python scripts/init_db.py
    echo "Generating demo data..."
    python scripts/generate_demo_data.py
fi

# Launch Streamlit
echo "Starting CEO Command Center..."
echo "Login: ceo / admin123"
streamlit run app/Home.py "$@"
