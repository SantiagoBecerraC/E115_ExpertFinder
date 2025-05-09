"""
Integrated test script for Expert Finder data management.
Tests the functionality of loading both LinkedIn and Google Scholar data
into ChromaDB with DVC version control.
"""

import os
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import our data integration utilities
from utils.data_integration_utils import DataIntegrationManager, import_linkedin_profiles, import_google_scholar_data
from utils.chroma_db_utils import ChromaDBManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """
    Setup environment variables and directories for testing.
    
    Returns:
        Tuple of (chroma_dir, linkedin_data_path, scholar_data_path)
    """
    # Load environment variables
    load_dotenv()
    
    # Set up paths for testing
    test_dir = Path("chromaDBtest")
    chroma_dir = test_dir / "chromadb"
    linkedin_data_path = test_dir / "linkedin_raw_data" / "processed_profiles"
    scholar_data_path = Path("google_scholar")
    
    # Create directories if they don't exist
    chroma_dir.mkdir(parents=True, exist_ok=True)
    linkedin_data_path.mkdir(parents=True, exist_ok=True)
    
    return str(chroma_dir), linkedin_data_path, scholar_data_path

def test_linkedin_data_import(chroma_dir, data_path):
    """
    Test importing LinkedIn data into ChromaDB.
    
    Args:
        chroma_dir: Path to ChromaDB directory
        data_path: Path to LinkedIn data directory
    """
    logger.info("===== Testing LinkedIn Data Import =====")
    
    # Use the simplified import function
    try:
        count = import_linkedin_profiles(
            data_path=data_path,
            chroma_dir=chroma_dir,
            create_version=True
        )
        logger.info(f"Successfully imported {count} LinkedIn profiles")
    except Exception as e:
        logger.error(f"Error importing LinkedIn data: {e}")
        raise

def test_google_scholar_data_import(chroma_dir, data_path):
    """
    Test importing Google Scholar data into ChromaDB.
    
    Args:
        chroma_dir: Path to ChromaDB directory
        data_path: Path to Google Scholar data directory
    """
    logger.info("===== Testing Google Scholar Data Import =====")
    
    # Use the simplified import function
    try:
        authors_count, articles_count = import_google_scholar_data(
            data_path=data_path,
            chroma_dir=chroma_dir,
            create_version=True
        )
        logger.info(f"Successfully imported {authors_count} authors and {articles_count} articles")
    except Exception as e:
        logger.error(f"Error importing Google Scholar data: {e}")
        raise

def test_integration_manager(chroma_dir, linkedin_path, scholar_path):
    """
    Test the DataIntegrationManager directly.
    
    Args:
        chroma_dir: Path to ChromaDB directory
        linkedin_path: Path to LinkedIn data directory
        scholar_path: Path to Google Scholar data directory
    """
    logger.info("===== Testing DataIntegrationManager =====")
    
    try:
        # Initialize the integration manager
        manager = DataIntegrationManager(chroma_dir=chroma_dir)
        
        # Get version histories for both collections
        histories = manager.get_version_histories()
        
        logger.info("Version histories:")
        for collection, history in histories.items():
            logger.info(f"{collection} history: {history}")
        
        # Test query functionality for both collections
        test_query = "machine learning expert with experience in neural networks"
        
        # Query LinkedIn collection
        logger.info("\nTesting LinkedIn collection query:")
        linkedin_results = manager.linkedin_db.query(test_query, n_results=3)
        logger.info(f"Found {len(linkedin_results)} LinkedIn results")
        
        # Query Google Scholar collection
        logger.info("\nTesting Google Scholar collection query:")
        scholar_results = manager.scholar_db.query(test_query, n_results=3)
        logger.info(f"Found {len(scholar_results)} Google Scholar results")
        
    except Exception as e:
        logger.error(f"Error testing integration manager: {e}")
        raise

def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description="Test Expert Finder data integration")
    parser.add_argument("--linkedin", action="store_true", help="Test LinkedIn data import")
    parser.add_argument("--scholar", action="store_true", help="Test Google Scholar data import")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--chroma-dir", help="Override ChromaDB directory")
    parser.add_argument("--linkedin-data", help="Override LinkedIn data directory")
    parser.add_argument("--scholar-data", help="Override Google Scholar data directory")
    
    args = parser.parse_args()
    
    # If no specific test is specified, run all tests
    run_all = args.all or not (args.linkedin or args.scholar)
    
    try:
        # Setup environment and paths
        chroma_dir, linkedin_path, scholar_path = setup_environment()
        
        # Override with command line arguments if provided
        if args.chroma_dir:
            chroma_dir = args.chroma_dir
        if args.linkedin_data:
            linkedin_path = Path(args.linkedin_data)
        if args.scholar_data:
            scholar_path = Path(args.scholar_data)
        
        logger.info(f"Using ChromaDB directory: {chroma_dir}")
        logger.info(f"Using LinkedIn data path: {linkedin_path}")
        logger.info(f"Using Google Scholar data path: {scholar_path}")
        
        # Run tests based on arguments
        if args.linkedin or run_all:
            test_linkedin_data_import(chroma_dir, linkedin_path)
        
        if args.scholar or run_all:
            test_google_scholar_data_import(chroma_dir, scholar_path)
        
        # Always run integration manager test
        test_integration_manager(chroma_dir, linkedin_path, scholar_path)
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 