#!/bin/bash
 
# Exit immediately if a command exits with a non-zero status
set -e
 
echo "Creating/activating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
 
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
 
echo "Installing Playwright browsers and system dependencies..."
playwright install chromium --with-deps
 
echo "Setup complete! Run your app with: .venv/bin/python scripts/app.py"