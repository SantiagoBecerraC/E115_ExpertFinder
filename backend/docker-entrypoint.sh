#!/bin/bash

# Start the FastAPI application using uvicorn through pipenv
pipenv run uvicorn main:app --host 0.0.0.0 --port 8000
