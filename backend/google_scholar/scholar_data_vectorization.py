"""
Script to scrape Google Scholar data and store it in ChromaDB.
"""

import json
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.chroma_db_utils import ChromaDBManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_google_scholar_data() -> Dict[str, Any]:
    """Load and combine all Google Scholar JSON files."""
    # Get the path to the google-scholar-data directory
    data_dir = Path(__file__).parent.parent.parent.parent / "google-scholar-data" / "processed_data"
    if not data_dir.exists():
        raise FileNotFoundError("Could not find processed data directory")
    # Find all Google Scholar JSON files
    json_files = list(data_dir.glob("data.processed*.json"))
    if not json_files:
        raise FileNotFoundError("No processed data files found")

    # Combine all JSON files into one dictionary
    combined_data = {}
    for json_file in json_files:
        logger.info(f"Loading data from {json_file}")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            combined_data.update(data)

    return combined_data


def generate_author_id():
    """Generate a unique author ID."""
    return f"author_{uuid.uuid4().hex}"


def scrape_url_content(url: str, max_retries: int = 3) -> Optional[List[str]]:
    """
    Scrape content from a given URL using LangChain's WebBaseLoader.
    Returns None if the URL cannot be accessed.
    Returns a list of content chunks if successful.
    """
    if not url:
        return None

    for attempt in range(max_retries):
        try:
            # Set a user agent to identify our application
            headers = {
                "User-Agent": "ExpertFinder/1.0 (Research Data Collection Tool; https://github.com/yourusername/ExpertFinder)"
            }
            loader = WebBaseLoader(url, header_template=headers)
            docs = loader.load()

            # Combine all document content
            content = " ".join(doc.page_content for doc in docs)

            # Split content into manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            chunks = text_splitter.split_text(content)

            # Return all chunks
            return chunks if chunks else None

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for URL {url}: {str(e)}")
            time.sleep(1)

    logger.error(f"Failed to scrape URL after {max_retries} attempts: {url}")
    return None


def prepare_documents_for_chromadb(author_name: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare documents for ChromaDB storage.
    Returns a list of documents in the format expected by ChromaDBManager.
    """
    documents = []
    author_info = data["author_info"]
    articles = data["articles"]

    # Generate unique ID for the author
    author_id = generate_author_id()

    # Scrape website content
    logger.info(f"Scraping website for author: {author_name}")
    website_content = scrape_url_content(author_info.get("website", ""))

    # Scrape journal content from the first article if available
    first_article = articles[0] if articles else None
    journal_content = None
    if first_article and "journal_url" in first_article:
        logger.info(f"Scraping journal URL for article: {first_article['title']}")
        journal_content = scrape_url_content(first_article.get("journal_url", ""))

    # Create author document with sanitized metadata
    author_doc = {
        "id": author_id,
        "content": f"{author_info.get('author', '')}. {author_info.get('affiliations', '')}. Interests: {author_info.get('interests', '')}. Publications: {', '.join(article.get('title', '') for article in articles)}",
        "metadata": {
            "doc_type": "author",
            "author": str(author_info.get("author", "")),
            "affiliations": str(author_info.get("affiliations", "")),
            "interests": str(author_info.get("interests", "")),
            "citations": str(first_article.get("citations_count", 0) if first_article else 0),
            "num_articles": str(len(articles)),
            "website": str(author_info.get("website", "")),
            "original_id": str(author_id),
        },
    }
    documents.append(author_doc)

    # Add website content documents
    if website_content:
        for i, chunk in enumerate(website_content):
            if chunk:  # Only add non-empty chunks
                doc = {
                    "id": f"{author_id}_website_{i}",
                    "content": str(chunk),
                    "metadata": {
                        "doc_type": "website_content",
                        "author": str(author_info.get("author", "")),
                        "url": str(author_info.get("website", "")),
                        "chunk_index": str(i),
                        "original_id": str(author_id),
                    },
                }
                documents.append(doc)

    # Add journal content documents
    if journal_content:
        for i, chunk in enumerate(journal_content):
            if chunk:  # Only add non-empty chunks
                doc = {
                    "id": f"{author_id}_journal_{i}",
                    "content": str(chunk),
                    "metadata": {
                        "doc_type": "journal_content",
                        "author": str(author_info.get("author", "")),
                        "url": (str(first_article.get("journal_url", "")) if first_article else ""),
                        "chunk_index": str(i),
                        "original_id": str(author_id),
                    },
                }
                documents.append(doc)

    return documents


def load_to_chromadb(documents: List[Dict[str, Any]], db_manager: ChromaDBManager):
    """
    Load documents into ChromaDB collection.
    """
    # Prepare data for batch loading
    ids = []
    contents = []
    metadatas = []

    # Keep track of seen IDs to handle duplicates
    seen_ids = set()

    for doc in documents:
        try:
            doc_id = doc["id"]

            # Handle duplicate IDs
            counter = 1
            while doc_id in seen_ids:
                doc_id = f"{doc['id']}_{counter}"
                counter += 1

            # Ensure content is not None
            content = str(doc.get("content", ""))
            if not content.strip():
                logger.warning(f"Skipping document {doc_id} due to empty content")
                continue

            # Ensure all metadata values are strings
            metadata = {}
            for key, value in doc["metadata"].items():
                if value is None:
                    metadata[key] = ""
                else:
                    metadata[key] = str(value)

            seen_ids.add(doc_id)
            ids.append(doc_id)
            contents.append(content)
            metadatas.append(metadata)

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            continue

    # Add documents to collection
    if ids:
        db_manager.add_documents(documents=contents, ids=ids, metadatas=metadatas)
        logger.info(f"Added {len(ids)} documents to ChromaDB collection")
    else:
        logger.warning("No valid documents to add to ChromaDB")


def main():
    """Main function to scrape and store data in ChromaDB."""
    try:
        # Load Google Scholar data
        logger.info("Loading Google Scholar data...")
        input_data = load_google_scholar_data()

        # Initialize ChromaDB manager
        db_manager = ChromaDBManager(collection_name="google_scholar")

        # Process each author and store in ChromaDB
        all_documents = []
        for author_name, data in input_data.items():
            logger.info(f"Processing author: {author_name}")
            documents = prepare_documents_for_chromadb(author_name, data)
            all_documents.extend(documents)

        # Store all documents in ChromaDB
        logger.info(f"Storing {len(all_documents)} documents in ChromaDB...")
        load_to_chromadb(all_documents, db_manager)

        # Run test queries
        print("\n" + "=" * 50)
        print("RUNNING TEST QUERIES")
        print("=" * 50)

        # Test author search
        print("\n1. Testing Author Search:")
        print("-" * 30)
        results = db_manager.query("machine learning", n_results=5)

        # Filter and display author results
        author_results = [r for r in results if r["metadata"].get("doc_type") == "author"][:3]
        for idx, result in enumerate(author_results, 1):
            print(f"\nAuthor Result {idx}:")
            print("-" * 20)
            print(f"Author: {result['metadata'].get('author', 'N/A')}")
            print(f"Affiliations: {result['metadata'].get('affiliations', 'N/A')}")
            print(f"Interests: {result['metadata'].get('interests', 'N/A')}")
            print(f"Citations: {result['metadata'].get('citations', 'N/A')}")
            print(f"Content: {result.get('content', 'N/A')[:200]}...")

        # Test content search
        print("\n2. Testing Content Search:")
        print("-" * 30)
        results = db_manager.query("deep learning applications", n_results=5)

        # Filter and display content results
        content_results = [
            r for r in results if r["metadata"].get("doc_type") in ["website_content", "journal_content"]
        ][:3]
        for idx, result in enumerate(content_results, 1):
            print(f"\nContent Result {idx}:")
            print("-" * 20)
            print(f"Type: {result['metadata'].get('doc_type', 'N/A')}")
            print(f"Author: {result['metadata'].get('author', 'N/A')}")
            print(f"URL: {result['metadata'].get('url', 'N/A')}")
            print(f"Content: {result.get('content', 'N/A')[:200]}...")

        print("\n" + "=" * 50)
        print("TEST QUERIES COMPLETED")
        print("=" * 50)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
