#!/bin/bash
# File: setup_env.sh
# Sets up StoryCheck's Python environment using uv and Node.js for mock wallet

set -e

echo "Checking for Python 3.10..."
if ! command -v python3.10 &> /dev/null; then
    echo "Python 3.10 not found. Please install it (e.g., 'sudo apt install python3.10 python3.10-venv')."
    exit 1
fi

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Creating virtual environment with Python 3.10..."
uv venv --python python3.10 .venv

if [ ! -d ".venv" ]; then
    echo "Failed to create virtual environment. Check Python 3.10 installation."
    exit 1
fi

echo "Activating virtual environment..."
source .venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

echo "Installing Python dependencies..."
uv pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install
playwright install-deps

echo "Setting up mock wallet..."
cd interpreter/browser/mock_wallet
yarn install --non-interactive
yarn bundle
cd ../../..

echo "Environment setup complete!"
echo "To activate the environment, run: source .venv/bin/activate"
echo "Then run tests with: pytest tests/"