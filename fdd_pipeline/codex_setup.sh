#!/bin/bash
# Setup script for Codex agent environment for the fdd_pipeline project

set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Starting Codex Setup Script for fdd_pipeline ---"

# 1. Install system dependencies
# Update package list and install tesseract-ocr (for pytesseract) and other common utilities
echo "--- Installing system dependencies (sudo access might be required by Codex environment) ---"
sudo apt-get update -y
sudo apt-get install -y tesseract-ocr git curl gcc g++ # Add other system deps if needed

# 2. Setup Python virtual environment using uv
echo "--- Setting up Python virtual environment using uv ---"
# Ensure uv is available (expected to be in codex-universal image or installable)
if ! command -v uv &> /dev/null
then
    echo "uv could not be found. Attempting to install uv."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the environment to make uv available in this script session
    # Adjust path if uv installs to a different location
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    elif [ -f "/root/.cargo/env" ]; then # Common in Docker containers running as root
        source "/root/.cargo/env"
    else
        echo "Warning: Could not automatically source uv environment. Assuming uv is in PATH."
    fi
    # Verify again
    if ! command -v uv &> /dev/null
    then
        echo "Error: uv installation failed or uv is not in PATH. Exiting."
        exit 1
    fi
fi

# Assuming the working directory is fdd_pipeline
# Create a virtual environment in .venv
uv venv .venv --python $(which python3) # Explicitly use python3 if available

echo "--- Virtual environment created (or already existed) ---"

# 3. Install Python dependencies
echo "--- Installing Python dependencies from requirements.txt using uv ---"
# Activate the virtual environment for this script session to ensure pip install targets it.
# Alternatively, use uv pip install directly if it handles context correctly.
# For robustness, we'll ensure uv uses the created venv.
uv pip install -r requirements.txt --python .venv/bin/python

echo "--- Python dependencies installed ---"

# 4. Final checks (optional)
echo "--- Verifying key tools ---"
uv run --python .venv/bin/python -- --version
uv run --python .venv/bin/python -m ruff --version
uv run --python .venv/bin/python -m black --version
uv run --python .venv/bin/python -m mypy --version
uv run --python .venv/bin/python -m pytest --version || echo "Pytest not found or not installed, which is fine if no tests yet."


echo "--- Codex Setup Script for fdd_pipeline finished successfully ---" 