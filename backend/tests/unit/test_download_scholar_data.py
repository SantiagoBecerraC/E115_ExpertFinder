"""
Test cases for Google Scholar data download functionality.
"""

import pytest
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from google_scholar.download_scholar_data import (
    extract_data,
    save_to_json,
    DATA_DIR
)

# Sample data for testing
SAMPLE_ARTICLE = {
    "title": "Test Article",
    "snippet": "This is a test article snippet",
    "publication_info": {
        "summary": "Published in 2023",
        "authors": [{"author_id": "author123"}]
    },
    "link": "http://test-journal.com",
    "inline_links": {
        "cited_by": {"total": 10}
    },
    "result_id": "result123"
}

SAMPLE_AUTHOR = {
    "author": {
        "name": "Test Author",
        "affiliations": "Test University",
        "website": "http://test-author.com",
        "interests": [{"title": "AI"}, {"title": "Machine Learning"}]
    }
}

SAMPLE_CITATION = {
    "citations": [
        {
            "title": "MLA",
            "snippet": "Test citation details"
        }
    ]
}

@pytest.fixture
def mock_scholar_client():
    """Create a mock Google Scholar client."""
    client = Mock()
    client.search_articles.return_value = {
        "organic_results": [SAMPLE_ARTICLE],
        "serpapi_pagination": {"next": "next_page"}
    }
    client.get_author_details.return_value = SAMPLE_AUTHOR
    client.get_citations.return_value = SAMPLE_CITATION
    return client

def test_extract_data_basic(mock_scholar_client):
    """Test basic data extraction."""
    # Mock the scholar client to return our sample data
    mock_scholar_client.search_articles.return_value = {
        "organic_results": [SAMPLE_ARTICLE],
        "serpapi_pagination": {"next": "next_page"}
    }
    mock_scholar_client.get_author_details.return_value = SAMPLE_AUTHOR
    mock_scholar_client.get_citations.return_value = SAMPLE_CITATION
    
    result = extract_data(
        query="test query",
        start_year="2020",
        end_year="2023",
        num_results=1,
        results_per_page=1,
        scholar_client=mock_scholar_client
    )
    
    # Verify the result structure
    assert len(result) == 1
    article = result[0]
    assert article["Article Title"] == "Test Article"
    assert article["Article Snippet"] == "This is a test article snippet"
    assert article["Publication Year"] == "2023"
    assert article["Journal URL"] == "http://test-journal.com"
    assert article["Number of Citations"] == 10
    assert article["Publication Summary"] == "Published in 2023"
    assert len(article["Authors"]) == 1
    assert article["Authors"][0]["Author Name"] == "Test Author"
    assert article["Authors"][0]["Affiliations"] == "Test University"
    assert article["Authors"][0]["Website"] == "http://test-author.com"
    assert article["Authors"][0]["Interests"] == "AI, Machine Learning"
    assert len(article["Citations"]) == 1
    assert article["Citations"][0]["Citation"] == "MLA"
    assert article["Citations"][0]["Citation Details"] == "Test citation details"

def test_extract_data_author_details(mock_scholar_client):
    """Test extraction of author details."""
    result = extract_data(
        query="test query",
        start_year="2020",
        end_year="2023",
        num_results=10,
        results_per_page=10,
        scholar_client=mock_scholar_client
    )
    
    article = result[0]
    assert len(article["Authors"]) == 1
    author = article["Authors"][0]
    assert author["Author Name"] == "Test Author"
    assert author["Affiliations"] == "Test University"
    assert author["Website"] == "http://test-author.com"
    assert author["Interests"] == "AI, Machine Learning"

def test_extract_data_citations(mock_scholar_client):
    """Test extraction of citations."""
    result = extract_data(
        query="test query",
        start_year="2020",
        end_year="2023",
        num_results=10,
        results_per_page=10,
        scholar_client=mock_scholar_client
    )
    
    article = result[0]
    assert len(article["Citations"]) == 1
    citation = article["Citations"][0]
    assert citation["Citation"] == "MLA"
    assert citation["Citation Details"] == "Test citation details"

def test_extract_data_pagination(mock_scholar_client):
    """Test pagination handling."""
    # Mock multiple pages of results
    mock_scholar_client.search_articles.side_effect = [
        {
            "organic_results": [SAMPLE_ARTICLE],
            "serpapi_pagination": {"next": "next_page"}
        },
        {
            "organic_results": [SAMPLE_ARTICLE],
            "serpapi_pagination": {}  # No more pages
        }
    ]
    
    result = extract_data(
        query="test query",
        start_year="2020",
        end_year="2023",
        num_results=20,
        results_per_page=10,
        scholar_client=mock_scholar_client
    )
    
    assert len(result) == 2
    assert mock_scholar_client.search_articles.call_count == 2

def test_extract_data_error_handling(mock_scholar_client):
    """Test error handling during data extraction."""
    # Mock the scholar client to return our sample data
    mock_scholar_client.search_articles.return_value = {
        "organic_results": [SAMPLE_ARTICLE],
        "serpapi_pagination": {"next": None}  # No pagination to avoid additional searches
    }
    
    # Instead of causing an exception, mock get_author_details to return empty author details
    mock_scholar_client.get_author_details.return_value = {
        "author": {}  # Empty author details will result in empty author info
    }
    
    mock_scholar_client.get_citations.return_value = SAMPLE_CITATION
    
    # Call the function
    result = extract_data(
        query="test query",
        start_year="2020",
        end_year="2023",
        num_results=1,
        results_per_page=1,
        scholar_client=mock_scholar_client
    )
    
    # Verify the basic structure
    assert len(result) == 1
    article = result[0]
    assert article["Article Title"] == "Test Article"
    assert article["Article Snippet"] == "This is a test article snippet"
    assert article["Publication Year"] == "2023"
    assert article["Journal URL"] == "http://test-journal.com"
    assert article["Number of Citations"] == 10
    assert article["Publication Summary"] == "Published in 2023"

def test_save_to_json(tmp_path):
    """Test saving data to JSON."""
    articles_data = [{
        "Article Title": "Test Article",
        "Article Snippet": "Test snippet",
        "Publication Year": "2023",
        "Journal URL": "http://test.com",
        "Number of Citations": 10,
        "Authors": [{
            "Author Name": "Test Author",
            "Affiliations": "Test University"
        }],
        "Citations": []
    }]
    
    # Mock DATA_DIR to use temporary directory
    with patch('google_scholar.download_scholar_data.DATA_DIR', tmp_path):
        save_to_json(
            articles_data,
            query="test query",
            start_year="2020",
            end_year="2023",
            num_results=10
        )
        
        # Check if JSON file was created
        json_files = list(tmp_path.glob("Google_Scholar_Data_*.json"))
        assert len(json_files) == 1
        
        # Check file contents
        with open(json_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data["Query"] == "test query"
            assert data["Publication_Year_From"] == "2020"
            assert data["Publication_Year_To"] == "2023"
            assert data["Results_Fetched"] == 10
            assert len(data["Articles"]) == 1
            assert data["Articles"][0]["Article Title"] == "Test Article" 