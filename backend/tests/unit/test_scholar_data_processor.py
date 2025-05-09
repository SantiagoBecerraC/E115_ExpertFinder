"""
Unit tests for the scholar_data_processor.py module.
(LEGACY) -- full module is now skipped. See test_scholar_data_processor_basic.py for current tests.
"""

import pytest

pytest.skip("Skipping legacy scholar_data_processor tests – implementation has changed", allow_module_level=True)

"""
Unit tests for the scholar_data_processor.py module.

Tests the functions for processing Google Scholar data, including:
- Processing data from files
- Preparing data for ChromaDB
- Saving results to JSON files
- Main workflow operation
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from collections import defaultdict

from google_scholar.scholar_data_processor import (
    process_scholar_data,
    prepare_chroma_data,
    save_to_json,
    main
)


@pytest.fixture
def sample_articles_data():
    """Fixture providing sample Google Scholar articles data."""
    return {
        "Articles": [
            {
                "Article Title": "Test Paper 1",
                "Article Snippet": "This is a test paper abstract about machine learning.",
                "Publication Year": "2025",
                "Journal URL": "https://test.com/journal1",
                "Number of Citations": 150,
                "Publication Summary": "Journal of Testing, 2025",
                "Citations": [
                    {"Citation Details": "Test Citation 1"}
                ],
                "Authors": [
                    {
                        "Author Name": "Test Author 1",
                        "Affiliations": "Test University",
                        "Website": "https://test-author1.edu",
                        "Interests": "Machine Learning, Artificial Intelligence"
                    },
                    {
                        "Author Name": "Test Author 2",
                        "Affiliations": "Test Institute",
                        "Website": "https://test-author2.org",
                        "Interests": "NLP, Machine Learning"
                    }
                ]
            },
            {
                "Article Title": "Test Paper 2",
                "Article Snippet": "This is a test paper abstract about deep learning.",
                "Publication Year": "2024",
                "Journal URL": "https://test.com/journal2",
                "Number of Citations": 75,
                "Publication Summary": "Conference on Testing, 2024",
                "Citations": [
                    {"Citation Details": "Test Citation 2"}
                ],
                "Authors": [
                    {
                        "Author Name": "Test Author 1",
                        "Affiliations": "Test University",
                        "Website": "https://test-author1.edu",
                        "Interests": "Machine Learning, Artificial Intelligence"
                    },
                    {
                        "Author Name": "Test Author 3",
                        "Affiliations": "Research Lab",
                        "Website": "https://test-author3.org",
                        "Interests": "Computer Vision, Machine Learning"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_json_file(sample_articles_data):
    """Creates a temporary JSON file with sample article data."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        tmp.write(json.dumps(sample_articles_data).encode('utf-8'))
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


def test_read_json_file(sample_json_file):
    """Test reading a JSON file."""
    result = read_json_file(sample_json_file)
    
    assert isinstance(result, dict)
    assert "profiles" in result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["name"] == "Test Author"


def test_read_json_file_nonexistent():
    """Test reading a non-existent JSON file."""
    with pytest.raises(FileNotFoundError):
        read_json_file("nonexistent_file.json")


def test_process_scholar_data(sample_json_file):
    """Test processing Scholar data from a JSON file."""
    authors = process_scholar_data(sample_json_file)
    
    assert isinstance(authors, list)
    assert len(authors) == 1
    assert authors[0]["author_id"] == "test_id"
    assert authors[0]["name"] == "Test Author"
    assert authors[0]["affiliations"] == "Test University"


def test_process_scholar_data_empty_file(tmp_path):
    """Test processing an empty JSON file."""
    empty_file = tmp_path / "empty.json"
    with open(empty_file, 'w') as f:
        f.write("{}")
    
    authors = process_scholar_data(str(empty_file))
    assert authors == []


def test_extract_author_data(sample_scholar_data):
    """Test extracting author data from Scholar data."""
    authors = extract_author_data(sample_scholar_data)
    
    assert isinstance(authors, list)
    assert len(authors) == 2  # Should have 2 unique authors
    
    # Check first author
    author1 = [a for a in authors if a["author_id"] == "auth1"][0]
    assert author1["name"] == "Test Author 1"
    assert author1["affiliations"] == "Test University"
    assert author1["cited_by"] == 500
    assert len(author1["interests"]) == 2
    
    # Check second author
    author2 = [a for a in authors if a["author_id"] == "auth2"][0]
    assert author2["name"] == "Test Author 2"
    assert author2["cited_by"] == 250


def test_extract_author_data_no_profiles():
    """Test extracting author data when no profiles exist."""
    data = {"organic_results": [], "search_metadata": {}}
    authors = extract_author_data(data)
    assert authors == []


def test_process_author_data():
    """Test processing a single author's data."""
    author_data = {
        "name": "Test Author",
        "author_id": "test_id",
        "affiliations": "Test University",
        "email": "test@example.com",
        "cited_by": 100,
        "interests": [
            {"title": "Machine Learning"},
            {"title": "Artificial Intelligence"}
        ]
    }
    
    processed = process_author_data(author_data)
    
    assert processed["author_id"] == "test_id"
    assert processed["name"] == "Test Author"
    assert processed["affiliations"] == "Test University"
    assert processed["email"] == "test@example.com"
    assert processed["citations"] == 100
    assert processed["interests"] == ["Machine Learning", "Artificial Intelligence"]


def test_process_author_data_missing_fields():
    """Test processing author data with missing fields."""
    # Missing email and interests
    author_data = {
        "name": "Test Author",
        "author_id": "test_id",
        "affiliations": "Test University",
        "cited_by": 100
    }
    
    processed = process_author_data(author_data)
    
    assert processed["author_id"] == "test_id"
    assert processed["email"] == ""
    assert processed["interests"] == []


def test_process_author_data_empty():
    """Test processing empty author data."""
    processed = process_author_data({})
    
    assert processed["author_id"] == ""
    assert processed["name"] == ""
    assert processed["affiliations"] == ""
    assert processed["email"] == ""
    assert processed["citations"] == 0
    assert processed["interests"] == []


def test_get_merged_fields():
    """Test merging fields from multiple authors."""
    authors = [
        {
            "author_id": "auth1",
            "name": "Test Author",
            "affiliations": "University 1",
            "interests": ["AI", "ML"]
        },
        {
            "author_id": "auth1",  # Same author_id
            "name": "Test Author",
            "affiliations": "University 2",  # Different affiliation
            "interests": ["ML", "NLP"]  # Different interests
        }
    ]
    
    merged = get_merged_fields(authors, "auth1")
    
    assert merged["name"] == "Test Author"
    assert merged["affiliations"] in ["University 1", "University 2"]  # Should take one of the values
    assert set(merged["interests"]) == set(["AI", "ML", "NLP"])  # Should combine interests


def test_get_merged_fields_no_matching():
    """Test merging when no matching author is found."""
    authors = [
        {"author_id": "auth1", "name": "Author 1"},
        {"author_id": "auth2", "name": "Author 2"}
    ]
    
    with pytest.raises(ValueError):
        get_merged_fields(authors, "auth3")


@patch('google_scholar.scholar_data_processor.find_scholar_json_files')
@patch('google_scholar.scholar_data_processor.process_scholar_data')
@patch('google_scholar.scholar_data_processor.write_json_file')
def test_main(mock_write, mock_process, mock_find):
    """Test the main function."""
    # Setup mocks
    mock_find.return_value = ["file1.json", "file2.json"]
    mock_process.side_effect = [
        [{"author_id": "auth1", "name": "Author 1"}],
        [{"author_id": "auth2", "name": "Author 2"}]
    ]
    
    # Call main function
    main()
    
    # Verify called twice (once for each file)
    assert mock_process.call_count == 2
    
    # Verify write_json_file was called with combined results
    mock_write.assert_called_once()
    # The call should have a list of 2 authors
    args, _ = mock_write.call_args
    assert len(args[0]) == 2
    assert {"author_id": "auth1", "name": "Author 1"} in args[0]
    assert {"author_id": "auth2", "name": "Author 2"} in args[0]


@patch('google_scholar.scholar_data_processor.find_scholar_json_files')
def test_main_no_files(mock_find):
    """Test main function when no files are found."""
    mock_find.return_value = []
    
    with patch('builtins.print') as mock_print:
        main()
        mock_print.assert_called_with("No JSON files found")
