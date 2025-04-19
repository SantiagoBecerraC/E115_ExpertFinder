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
from google_scholar.scholar_data_vectorization import (
    load_google_scholar_data,
    generate_author_id,
    scrape_url_content,
    prepare_documents_for_chromadb,
    load_to_chromadb
)

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

def test_save_to_json(tmp_path, sample_processed_data):
    """Test saving data to JSON file."""
    output_file = tmp_path / "output" / "test_output.json"
    save_to_json(sample_processed_data, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert loaded_data == sample_processed_data

@patch('google_scholar.scholar_data_vectorization.Path')
def test_load_google_scholar_data(mock_path, tmp_path):
    """Test loading Google Scholar data."""
    # Setup mock
    mock_data_dir = tmp_path / "google-scholar-data" / "processed_data"
    mock_data_dir.mkdir(parents=True)
    mock_json_file = mock_data_dir / "data.processed.json"
    with open(mock_json_file, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_JSON_DATA, f)
    
    mock_path.return_value.parent.parent.parent.parent = tmp_path
    
    result = load_google_scholar_data()
    assert isinstance(result, dict)

def test_generate_author_id():
    """Test generation of author IDs."""
    author_id = generate_author_id()
    assert author_id.startswith("author_")
    assert len(author_id) > 10  # UUID hex string length

@patch('google_scholar.scholar_data_vectorization.WebBaseLoader')
def test_scrape_url_content(mock_loader):
    """Test URL content scraping."""
    # Setup mock
    mock_doc = Mock()
    mock_doc.page_content = "Test content"
    mock_loader.return_value.load.return_value = [mock_doc]
    
    result = scrape_url_content("http://test.com")
    assert isinstance(result, list)
    assert len(result) > 0

def test_prepare_documents_for_chromadb(sample_processed_data):
    """Test preparation of documents for ChromaDB."""
    author_name = "Test Author"
    result = prepare_documents_for_chromadb(author_name, sample_processed_data[author_name])
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "id" in result[0]
    assert "content" in result[0]
    assert "metadata" in result[0]

@patch('google_scholar.scholar_data_vectorization.ChromaDBManager')
def test_load_to_chromadb(mock_db_manager):
    """Test loading documents into ChromaDB."""
    # Setup mock
    mock_db_manager.return_value = Mock()
    
    documents = [{
        "id": "test_id",
        "content": "Test content",
        "metadata": {
            "doc_type": "author",
            "author": "Test Author"
        }
    }]
    
    load_to_chromadb(documents, mock_db_manager.return_value)
    mock_db_manager.return_value.add_documents.assert_called_once() 