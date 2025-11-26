#!/bin/bash
# Stop existing instances
pkill -f uvicorn
pkill -f paper_trader.py

# Start Dashboard using uv
echo "Starting Dashboard on http://0.0.0.0:8000"
/home/agile/.local/bin/uv run uvicorn dashboard_api:app --host 0.0.0.0 --port 8000 --reload
