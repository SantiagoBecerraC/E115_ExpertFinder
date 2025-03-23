"""
Script to test and demonstrate ChromaDB query capabilities on the Google Scholar collection.
"""

import os
from pathlib import Path
import sys
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to Python path to allow imports from utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.chroma_db_utils import ChromaDBManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_chromadb():
    """
    Initialize ChromaDB manager.
    
    Returns:
        ChromaDBManager instance
    """
    # Load environment variables from the secrets folder at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    env_path = project_root / 'secrets' / '.env'
    
    # Print paths for debugging
    logger.info(f"Current file path: {current_file}")
    logger.info(f"Project root path: {project_root}")
    logger.info(f"Environment file path: {env_path}")
    
    # Print ChromaDB path
    db_path = project_root / 'chromadb'
    logger.info(f"ChromaDB path: {db_path}")
    logger.info(f"ChromaDB path exists: {db_path.exists()}")
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at {env_path}. Please create a .env file in the secrets directory.")
    
    load_dotenv(dotenv_path=env_path)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize ChromaDB manager
    db_manager = ChromaDBManager(collection_name="google_scholar", n_results=10)
    
    # Print detailed collection info
    try:
        collection = db_manager.collection
        logger.info(f"Collection name: {collection.name}")
        logger.info(f"Collection metadata: {collection.metadata}")
        count = collection.count()
        logger.info(f"Collection document count: {count}")
        
        # Get a sample of documents to verify metadata structure
        if count > 0:
            logger.info("\nVerifying collection metadata structure...")
            results = collection.get(limit=5)
            
            if results and results['metadatas']:
                logger.info("\nSample document metadata:")
                for i, metadata in enumerate(results['metadatas'][:5]):
                    logger.info(f"\nDocument {i + 1}:")
                    logger.info(f"Document type: {metadata.get('doc_type', 'Missing doc_type')}")
                    logger.info(f"Available fields: {list(metadata.keys())}")
                    
                    # Check expected fields based on document type
                    if metadata.get('doc_type') == 'author':
                        expected_fields = ['author', 'affiliations', 'interests', 'citations', 'website']
                    else:  # website_content or journal_content
                        expected_fields = ['author', 'url', 'chunk_index', 'doc_type']
                        
                    missing_fields = [field for field in expected_fields if field not in metadata]
                    if missing_fields:
                        logger.warning(f"Missing expected fields for {metadata.get('doc_type', 'unknown type')}: {missing_fields}")
                    
                    # Check field types
                    for key, value in metadata.items():
                        logger.info(f"Field '{key}' type: {type(value).__name__}")
                        
            else:
                logger.error("Could not retrieve sample documents from collection")
                
    except Exception as e:
        logger.error(f"Error inspecting collection: {str(e)}")
    
    return db_manager

def query_collection(db_manager: ChromaDBManager, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Query the collection using ChromaDBManager.
    
    Args:
        db_manager: ChromaDBManager instance
        query_text: Text to search for
        n_results: Number of results to return
        
    Returns:
        List of query results with processed metadata
    """
    try:
        logger.info(f"Querying ChromaDB with: {query_text}")
        results = db_manager.query(query_text, n_results=n_results)
        logger.info(f"Got {len(results)} results from ChromaDB")
        if not results:
            logger.warning("No results returned from query")
        return results
    except Exception as e:
        logger.error(f"Error querying collection: {str(e)}")
        return []

def print_author_result(result: Dict[str, Any], index: int):
    """Print formatted author result."""
    print(f"\nAuthor Result {index}:")
    print("-"*40)
    print(f"Author: {result['metadata'].get('author', 'N/A')}")
    print(f"Affiliations: {result['metadata'].get('affiliations', 'N/A')}")
    print(f"Interests: {result['metadata'].get('interests', 'N/A')}")
    print(f"Citations: {result['metadata'].get('citations', '0')}")
    if result['metadata'].get('website'):
        print(f"Website: {result['metadata']['website']}")
    print(f"\nContent Preview:")
    print(f"{result['content'][:200]}...")

def print_content_result(result: Dict[str, Any], index: int):
    """Print formatted content result."""
    print(f"\nContent Result {index}:")
    print("-"*40)
    print(f"Type: {result['metadata'].get('doc_type', 'N/A')}")
    print(f"Author: {result['metadata'].get('author', 'N/A')}")
    print(f"URL: {result['metadata'].get('url', 'N/A')}")
    print(f"Chunk Index: {result['metadata'].get('chunk_index', 'N/A')}")
    print(f"\nContent Preview:")
    print(f"{result['content'][:200]}...")

def run_test_queries(db_manager: ChromaDBManager):
    """
    Run various test queries using ChromaDBManager.
    
    Args:
        db_manager: ChromaDBManager instance
    """
    # First, verify the collection exists and has documents
    try:
        count = db_manager.collection.count()
        logger.info(f"Collection has {count} documents")
        if count == 0:
            logger.error("Collection is empty! Please run scrape_and_store.py first")
            return
    except Exception as e:
        logger.error(f"Error accessing collection: {str(e)}")
        return

    test_queries = [
        {
            "title": "Author Search - Machine Learning Experts",
            "query": "machine learning artificial intelligence",
            "filter": lambda x: x['metadata'].get('doc_type') == 'author'
        },
        {
            "title": "Website Content Search",
            "query": "research projects and publications",
            "filter": lambda x: x['metadata'].get('doc_type') == 'website_content'
        },
        {
            "title": "Journal Content Search",
            "query": "deep learning neural networks",
            "filter": lambda x: x['metadata'].get('doc_type') == 'journal_content'
        }
    ]
    
    print("\nRunning Test Queries:")
    print("="*50)
    
    for query_info in test_queries:
        print(f"\n{query_info['title']}")
        print("-"*40)
        
        # Get results
        results = query_collection(db_manager, query_info['query'], n_results=10)
        logger.info(f"Total results before filtering: {len(results)}")
        
        # Filter results by type
        filtered_results = [r for r in results if query_info['filter'](r)]
        logger.info(f"Results after filtering by doc_type: {len(filtered_results)}")
        
        if results and not filtered_results:
            # Log the document types we got to help debug filtering
            doc_types = [r['metadata'].get('doc_type') for r in results]
            logger.info(f"Document types in results: {set(doc_types)}")
        
        # Sort by citations
        try:
            filtered_results.sort(
                key=lambda x: int(x['metadata'].get('citations', '0')), 
                reverse=True
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not sort by citations - {str(e)}")
            if filtered_results:
                # Log some citation values to help debug
                citations = [r['metadata'].get('citations') for r in filtered_results[:3]]
                logger.warning(f"Sample citation values: {citations}")
        
        # Print results
        if not filtered_results:
            print("No matching results found.")
            continue
            
        for i, result in enumerate(filtered_results[:3], 1):
            if result['metadata'].get('doc_type') == 'author':
                print_author_result(result, i)
            else:
                print_content_result(result, i)
        
        print("\n" + "="*50)

def main():
    """
    Main function to run ChromaDB tests.
    """
    try:
        logger.info("Initializing ChromaDB...")
        db_manager = initialize_chromadb()
        
        # Get collection stats and verify database setup
        try:
            count = db_manager.collection.count()
            logger.info(f"Total documents in collection: {count}")
            if count == 0:
                logger.error("ChromaDB collection is empty! Please run scrape_and_store.py first")
                return
                
            # Try to get a sample document to verify data structure
            results = db_manager.query("test", n_results=1)
            if results:
                logger.info("Sample document metadata structure:")
                logger.info(f"Metadata keys: {list(results[0]['metadata'].keys())}")
                logger.info(f"Document type: {results[0]['metadata'].get('doc_type')}")
            
        except Exception as e:
            logger.error(f"Error verifying database setup: {str(e)}")
            return
        
        # Run test queries
        run_test_queries(db_manager)
        
        logger.info("All tests completed successfully!")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        logger.error("Please ensure you have:")
        logger.error("1. Created a .env file with your OPENAI_API_KEY")
        logger.error("2. Run scrape_and_store.py first to create and populate the database")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        logger.error("Please set your OPENAI_API_KEY in the .env file")
    except Exception as e:
        logger.error(f"Error testing ChromaDB: {str(e)}")
        logger.error("If this is an OpenAI API error, please check your API key configuration.")

if __name__ == "__main__":
    main() 