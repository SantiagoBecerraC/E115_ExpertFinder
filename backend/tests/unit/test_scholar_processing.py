import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys
from os.path import dirname, abspath, join

# Add the project root directory to the Python path
root_dir = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(root_dir)

from google_scholar.scholar_data_processor import process_scholar_data, prepare_chroma_data, save_to_json

# Test data
SAMPLE_ARTICLE = {
    "Article Title": "Test Article",
    "Article Snippet": "This is a test article snippet",
    "Publication Year": "2023",
    "Journal URL": "http://test-journal.com",
    "Number of Citations": 10,
    "Publication Summary": "Test publication summary",
    "Citations": [{"Citation Details": "Test citation"}],
    "Authors": [{
        "Author Name": "Test Author",
        "Affiliations": "Test University",
        "Website": "http://test-author.com",
        "Interests": "AI, Machine Learning"
    }]
}

SAMPLE_JSON_DATA = {
    "Articles": [SAMPLE_ARTICLE]
}

@pytest.fixture
def sample_json_file(tmp_path):
    """Create a temporary JSON file with sample data."""
    json_file = tmp_path / "test_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_JSON_DATA, f)
    return json_file

@pytest.fixture
def sample_processed_data():
    """Return sample processed data."""
    return {
        "Test Author": {
            "author_info": {
                "author": "Test Author",
                "affiliations": "Test University",
                "website": "http://test-author.com",
                "interests": "AI, Machine Learning"
            },
            "articles": [{
                "title": "Test Article",
                "snippet": "This is a test article snippet",
                "year": "2023",
                "journal_url": "http://test-journal.com",
                "citations_count": 10,
                "publication_summary": "Test publication summary",
                "citations": [{"Citation Details": "Test citation"}]
            }]
        }
    }

def test_process_scholar_data(sample_json_file):
    """Test processing of scholar data from JSON file."""
    result = process_scholar_data(sample_json_file)
    
    assert "Test Author" in result
    assert result["Test Author"]["author_info"]["author"] == "Test Author"
    assert len(result["Test Author"]["articles"]) == 1
    assert result["Test Author"]["articles"][0]["title"] == "Test Article"

def test_process_scholar_data_empty_file(tmp_path):
    """Test processing of empty JSON file."""
    empty_file = tmp_path / "empty.json"
    with open(empty_file, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    
    result = process_scholar_data(empty_file)
    assert result == {}

def test_process_scholar_data_invalid_structure(tmp_path):
    """Test processing of JSON file with invalid structure."""
    invalid_file = tmp_path / "invalid.json"
    with open(invalid_file, 'w', encoding='utf-8') as f:
        json.dump({"InvalidKey": []}, f)
    
    result = process_scholar_data(invalid_file)
    assert result == {}

def test_process_scholar_data_missing_fields(tmp_path):
    """Test processing of articles with missing fields."""
    data = {
        "Articles": [{
            "Article Title": "Test Article",
            "Authors": [{
                "Author Name": "Test Author"
                # Missing other fields
            }]
        }]
    }
    
    json_file = tmp_path / "missing_fields.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    result = process_scholar_data(json_file)
    assert "Test Author" in result
    assert result["Test Author"]["author_info"]["author"] == "Test Author"
    assert result["Test Author"]["author_info"]["affiliations"] == ""
    assert result["Test Author"]["author_info"]["website"] == ""
    assert result["Test Author"]["author_info"]["interests"] == ""

def test_prepare_chroma_data(sample_processed_data):
    """Test preparation of data for ChromaDB."""
    result = prepare_chroma_data(sample_processed_data)
    
    assert "authors" in result
    assert "articles" in result
    assert len(result["authors"]) == 1
    assert len(result["articles"]) == 1
    
    author_data = result["authors"][0]
    assert "id" in author_data
    assert "content" in author_data
    assert "metadata" in author_data
    assert author_data["metadata"]["author"] == "Test Author"

def test_prepare_chroma_data_empty():
    """Test preparation of empty data for ChromaDB."""
    result = prepare_chroma_data({})
    assert result == {"authors": [], "articles": []}

def test_prepare_chroma_data_no_articles():
    """Test preparation of data with authors but no articles."""
    data = {
        "Test Author": {
            "author_info": {
                "author": "Test Author",
                "affiliations": "Test University",
                "website": "http://test-author.com",
                "interests": "AI, Machine Learning"
            },
            "articles": []
        }
    }
    
    result = prepare_chroma_data(data)
    assert len(result["authors"]) == 1
    assert len(result["articles"]) == 0
    assert "Test Author" in result["authors"][0]["content"]
    assert result["authors"][0]["metadata"]["num_articles"] == 0

def test_prepare_chroma_data_missing_fields():
    """Test preparation of data with missing fields."""
    data = {
        "Test Author": {
            "author_info": {
                "author": "Test Author",
                "affiliations": "",
                "website": "",
                "interests": ""
            },
            "articles": [{
                "title": "Test Article",
                "snippet": "Test snippet",
                "year": "2023",
                "journal_url": "http://test-journal.com",
                "citations_count": 0,  
                "publication_summary": "Test summary"
            }]
        }
    }
    
    result = prepare_chroma_data(data)
    
    assert len(result["authors"]) == 1
    author_data = result["authors"][0]
    assert author_data["metadata"]["author"] == "Test Author"
    assert author_data["metadata"]["affiliations"] == ""  
    assert author_data["metadata"]["website"] == ""  
    assert author_data["metadata"]["interests"] == ""  
    
    assert len(result["articles"]) == 1
    article_data = result["articles"][0]
    assert article_data["metadata"]["title"] == "Test Article"
    assert article_data["metadata"]["year"] == "2023"
    assert article_data["metadata"]["journal_url"] == "http://test-journal.com"
    assert article_data["metadata"]["citations_count"] == 0
    assert article_data["metadata"]["author_name"] == "Test Author"

def test_save_to_json(tmp_path, sample_processed_data):
    """Test saving data to JSON file."""
    output_file = tmp_path / "output" / "test_output.json"
    save_to_json(sample_processed_data, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert loaded_data == sample_processed_data 