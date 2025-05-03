#!/bin/bash

# Print current environment for debugging
echo "==== Environment Information ===="
echo "Python version: $(python --version)"
echo "NumPy version: $(python -c 'import numpy; print(numpy.__version__)')"
echo "System Python path: $PYTHONPATH"
echo "Installed packages:"
pip list | grep -v torch | grep -v transformers
echo "================================="

# Check if we need to downgrade NumPy
NUMPY_VERSION=$(python -c 'import numpy; print(numpy.__version__)')
if [[ $NUMPY_VERSION == 2* ]]; then
    echo "NumPy 2.x detected, downgrading to 1.24.3..."
    pip install numpy==1.24.3 --force-reinstall
fi

# Check if core modules can be imported
echo "Checking if core application modules can be imported..."
python -c "import fastapi; import uvicorn; print('Core modules imported successfully')" || echo "Failed to import core modules"

# Start FastAPI application with Uvicorn directly
echo "Starting application with Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
