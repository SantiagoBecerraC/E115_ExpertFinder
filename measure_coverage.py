#!/usr/bin/env python
"""
Custom coverage measurement script that ensures all modules are properly loaded and measured.
"""
import importlib
import os
import sys

import coverage
import pytest

# Configure coverage
cov = coverage.Coverage(
    source=["backend"],
    omit=[
        "*/tests/*",
        "*/venv/*",
        "*/site-packages/*",
        "*/__pycache__/*",
    ],
)

# Start coverage measurement
cov.start()

# Explicitly import all modules to ensure they're tracked
modules_to_import = [
    "backend.linkedin_data_processing.dynamic_credibility",
    "backend.linkedin_data_processing.expert_finder_linkedin",
    "backend.linkedin_data_processing.credibility_stats",
    "backend.linkedin_data_processing.credibility_system",
    "backend.linkedin_data_processing.cli",
    "backend.utils.chroma_db_utils",
    "backend.utils.dvc_utils",
]

# Try to import each module
for module_name in modules_to_import:
    try:
        importlib.import_module(module_name)
        print(f"Successfully imported {module_name}")
    except ImportError as e:
        print(f"Could not import {module_name}: {e}")

# Run tests using pytest
print("\nRunning LinkedIn module tests...")
test_modules = [
    "backend/tests/unit/test_dynamic_credibility.py",
    "backend/tests/unit/test_expert_finder_linkedin.py",
    "backend/tests/unit/test_linkedin_finder.py",
    "backend/tests/unit/test_linkedin_profile_processor.py",
    "backend/tests/unit/test_linkedin_vectorizer.py",
]
pytest.main(test_modules)

# Stop coverage measurement
cov.stop()
cov.save()

# Report coverage
print("\nCoverage Report:")
cov.report()

# Generate HTML report
cov.html_report(directory="reports/linkedin-coverage")
print("\nHTML report generated in reports/linkedin-coverage")
