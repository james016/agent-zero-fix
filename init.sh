#!/bin/bash

# pip install
pip install -r requirements.txt

# Define source and destination paths
# Assuming the python files and sources.list are in the same directory as init.sh
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PYTHON_DEST_DIR="/opt/venv/lib/python3.11/site-packages/langchain_openai/embeddings"
APT_SOURCES_DIR="/etc/apt"
APT_SOURCES_FILE="sources.list"

# Create destination directory if it doesn't exist
echo "Creating destination directory if it doesn't exist: ${PYTHON_DEST_DIR}"
mkdir -p "${PYTHON_DEST_DIR}"

# Copy Python files
echo "Copying Python files to ${PYTHON_DEST_DIR}..."
cp "${SCRIPT_DIR}/auto_split.py" "${PYTHON_DEST_DIR}/"
cp "${SCRIPT_DIR}/base.py" "${PYTHON_DEST_DIR}/"
echo "Python files copied."

# Copy sources.list
echo "Copying ${APT_SOURCES_FILE} to ${APT_SOURCES_DIR}..."
cp "${SCRIPT_DIR}/${APT_SOURCES_FILE}" "${APT_SOURCES_DIR}/${APT_SOURCES_FILE}"
# Check if copy failed
if [ $? -ne 0 ]; then
    echo "Error: Failed to copy ${APT_SOURCES_FILE}." >&2
    exit 1
fi
echo "${APT_SOURCES_FILE} copied."

# Update apt package list
echo "Updating apt package list..."
apt update
# Check if update failed
if [ $? -ne 0 ]; then
    echo "Error: Failed to update apt." >&2
    exit 1
fi
echo "Apt package list updated."

echo "Initialization complete."

exit 0