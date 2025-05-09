"""Basic unit tests for current scholar_data_processor functions.
These replace legacy tests that targeted removed helpers.
"""
from pathlib import Path
import json
import tempfile
import os
from typing import Dict, Any

import pytest

from google_scholar.scholar_data_processor import (
    process_scholar_data,
    prepare_chroma_data,
)


@pytest.fixture()
def minimal_article_data() -> Dict[str, Any]:
    """Return minimal processed data structure expected by prepare_chroma_data."""
    return {
        "author_info": {
            "author": "Jane Doe",
            "affiliations": "Example University",
            "website": "https://janedoe.example.com",
            "interests": "Software Testing, QA",
        },
        "articles": [
            {
                "title": "A Study on Testing",
                "snippet": "Abstract ...",
                "year": "2025",
                "journal_url": "https://example.com/journal",
                "citations_count": 10,
                "publication_summary": "Journal, 2025",
                "citations": [],
            }
        ],
    }


@pytest.fixture()
def tmp_json_file(minimal_article_data):
    """Write minimal data to a temporary file and yield its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        # Create JSON structure expected by process_scholar_data
        json.dump({"Articles": [
            {
                "Article Title": "A Study on Testing",
                "Article Snippet": "Abstract ...",
                "Publication Year": "2025",
                "Journal URL": "https://example.com/journal",
                "Number of Citations": 10,
                "Publication Summary": "Journal, 2025",
                "Citations": [],
                "Authors": [
                    {
                        "Author Name": "Jane Doe",
                        "Affiliations": "Example University",
                        "Website": "https://janedoe.example.com",
                        "Interests": "Software Testing, QA"
                    }
                ]
            }
        ]}, f)
    yield path
    os.remove(path)


def test_process_scholar_data_basic(tmp_json_file):
    """process_scholar_data should return dict keyed by author name with articles."""
    result = process_scholar_data(tmp_json_file)
    assert isinstance(result, dict)
    assert "Jane Doe" in result
    author_block = result["Jane Doe"]
    assert "author_info" in author_block and "articles" in author_block
    assert author_block["author_info"]["affiliations"] == "Example University"
    assert len(author_block["articles"]) == 1


def test_prepare_chroma_data_shapes(minimal_article_data):
    """prepare_chroma_data returns authors & articles lists with expected lengths."""
    data_by_author = {
        "Jane Doe": minimal_article_data  # Already in processed format
    }
    chroma_dict = prepare_chroma_data(data_by_author)
    assert set(chroma_dict.keys()) == {"authors", "articles"}
    assert len(chroma_dict["authors"]) == 1
    assert len(chroma_dict["articles"]) >= 1  # may include zero if no title
