#!/bin/bash
# Start the FastAPI server

echo "Starting Hospital Readmission Prediction API..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
