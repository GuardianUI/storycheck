#!/bin/bash
# File: setup_env.sh
# Sets up StoryCheck's Python environment using uv and Node.js for mock wallet

echo "Installing Foundry (for anvil)..."
if ! command -v foundryup &> /dev/null; then
    # Run and source the Foundry installer to update PATH immediately
    curl -L https://foundry.paradigm.xyz | bash
    export PATH="$HOME/.foundry/bin:$PATH"
    foundryup
    if ! command -v foundryup &> /dev/null; then
        echo "Failed to install foundryup. Ensure ~/.foundry/bin is in PATH and try running 'foundryup' manually."
        exit 1
    fi
else
    echo "Foundry already installed."
fi
if ! command -v anvil &> /dev/null; then
    echo "Anvil installation failed."
    exit 1
fi

echo "Activating anvil environment..."
source ~/.bashrc || { echo "Failed to activate anvil environment"; exit 1; }


echo "Checking for Node.js and npm..."
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "Installing Node.js and npm..."
    sudo apt update && sudo apt install -y nodejs npm
else
    echo "Node.js and npm already installed."
fi

echo "Checking for pnpm..."
if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    npm install -g pnpm
else
    echo "pnpm already installed. If outdated, update with 'npm install -g pnpm'."
fi

set -e

echo "Checking for Python 3.10..."
if ! command -v python3.10 &> /dev/null; then
    echo "Python 3.10 not found. Please install it (e.g., 'sudo apt install python3.10 python3.10-venv')."
    exit 1
fi

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Creating virtual environment with Python 3.10..."
uv venv --python python3.10 .venv --clear

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
pnpm install --silent
pnpm bundle  # Note: If package.json "build" uses yarn, update it to pnpm for consistency
cd ../../..

echo "Environment setup complete!"
echo "To activate the environment, run: source .venv/bin/activate"
echo "Then run tests with: pytest tests/"
echo ""
echo "You can run story checks with: ./storycheck.sh <example_file.md>"

