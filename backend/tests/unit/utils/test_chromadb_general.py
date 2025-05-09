"""
Test script for Expert Finder ChromaDB functionality.
Tests the initialization, data import, querying, and versioning features.
"""

import os
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import ChromaDB manager
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
        Dictionary with test configuration
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
    
    # Set environment variable for ChromaDB path
    os.environ['CHROMA_DIR'] = str(chroma_dir)
    
    return {
        "chroma_dir": str(chroma_dir),
        "linkedin_data_path": linkedin_data_path,
        "scholar_data_path": scholar_data_path
    }

def test_initialization():
    """Test ChromaDB initialization with different collection names."""
    logger.info("===== Testing ChromaDB Initialization =====")
    
    # Initialize LinkedIn collection
    linkedin_db = ChromaDBManager(collection_name="linkedin_profiles", n_results=5)
    linkedin_stats = linkedin_db.get_collection_stats()
    logger.info(f"LinkedIn collection stats: {linkedin_stats}")
    
    # Initialize Google Scholar collection
    scholar_db = ChromaDBManager(collection_name="google_scholar", n_results=5)
    scholar_stats = scholar_db.get_collection_stats()
    logger.info(f"Google Scholar collection stats: {scholar_stats}")
    
    return linkedin_db, scholar_db

def test_linkedin_data_import(db_manager, data_path):
    """
    Test importing LinkedIn data into ChromaDB.
    
    Args:
        db_manager: ChromaDBManager instance for LinkedIn
        data_path: Path to LinkedIn data directory
    """
    logger.info("===== Testing LinkedIn Data Import =====")
    
    try:
        count = db_manager.import_linkedin_profiles(
            data_path=data_path,
            create_version=True
        )
        logger.info(f"Successfully imported {count} LinkedIn profiles")
        
        # Get collection stats after import
        stats = db_manager.get_collection_stats()
        logger.info(f"LinkedIn collection stats after import: {stats}")
        
        # Try a simple query to verify imports
        test_query = "machine learning expert"
        results = db_manager.query(test_query, n_results=3)
        logger.info(f"LinkedIn query returned {len(results)} results")
        
        # Get version history
        history = db_manager.get_version_history(max_entries=5)
        logger.info(f"LinkedIn version history: {history}")
        
        return count
    except Exception as e:
        logger.error(f"Error importing LinkedIn data: {e}")
        raise

def test_google_scholar_data_import(db_manager, data_path):
    """
    Test importing Google Scholar data into ChromaDB.
    
    Args:
        db_manager: ChromaDBManager instance for Google Scholar
        data_path: Path to Google Scholar data directory
    """
    logger.info("===== Testing Google Scholar Data Import =====")
    
    try:
        authors_count, articles_count = db_manager.import_google_scholar_data(
            data_path=data_path,
            create_version=True
        )
        logger.info(f"Successfully imported {authors_count} authors and {articles_count} articles")
        
        # Get collection stats after import
        stats = db_manager.get_collection_stats()
        logger.info(f"Google Scholar collection stats after import: {stats}")
        
        # Try a simple query to verify imports
        test_query = "neural networks research"
        results = db_manager.query(test_query, n_results=3)
        logger.info(f"Google Scholar query returned {len(results)} results")
        
        # Get version history
        history = db_manager.get_version_history(max_entries=5)
        logger.info(f"Google Scholar version history: {history}")
        
        return authors_count, articles_count
    except Exception as e:
        logger.error(f"Error importing Google Scholar data: {e}")
        raise

def test_versioning(db_manager):
    """
    Test DVC versioning functionality.
    
    Args:
        db_manager: ChromaDBManager instance
    """
    logger.info("===== Testing DVC Versioning =====")
    
    try:
        # Get version history
        history = db_manager.get_version_history(max_entries=5)
        
        if not history:
            logger.warning("No version history found. Skipping restore test.")
            return
        
        # Test restoring the most recent version
        latest_version = history[0]["commit_hash"]
        logger.info(f"Attempting to restore version: {latest_version}")
        
        success = db_manager.restore_database_version(latest_version)
        if success:
            logger.info(f"Successfully restored version: {latest_version}")
        else:
            logger.error(f"Failed to restore version: {latest_version}")
    
    except Exception as e:
        logger.error(f"Error testing versioning: {e}")
        raise

def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description="Test Expert Finder ChromaDB functionality")
    parser.add_argument("--linkedin", action="store_true", help="Test LinkedIn data import")
    parser.add_argument("--scholar", action="store_true", help="Test Google Scholar data import")
    parser.add_argument("--versioning", action="store_true", help="Test DVC versioning")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--chroma-dir", help="Override ChromaDB directory")
    parser.add_argument("--linkedin-data", help="Override LinkedIn data directory")
    parser.add_argument("--scholar-data", help="Override Google Scholar data directory")
    
    args = parser.parse_args()
    
    # If no specific test is specified, run all tests
    run_all = args.all or not (args.linkedin or args.scholar or args.versioning)
    
    try:
        # Setup environment and paths
        config = setup_environment()
        
        # Override with command line arguments if provided
        if args.chroma_dir:
            config["chroma_dir"] = args.chroma_dir
            os.environ['CHROMA_DIR'] = args.chroma_dir
        if args.linkedin_data:
            config["linkedin_data_path"] = Path(args.linkedin_data)
        if args.scholar_data:
            config["scholar_data_path"] = Path(args.scholar_data)
        
        logger.info(f"Using ChromaDB directory: {config['chroma_dir']}")
        logger.info(f"Using LinkedIn data path: {config['linkedin_data_path']}")
        logger.info(f"Using Google Scholar data path: {config['scholar_data_path']}")
        
        # Initialize ChromaDB managers for both collections
        linkedin_db, scholar_db = test_initialization()
        
        # Run LinkedIn tests if requested
        if args.linkedin or run_all:
            test_linkedin_data_import(linkedin_db, config["linkedin_data_path"])
        
        # Run Google Scholar tests if requested
        if args.scholar or run_all:
            test_google_scholar_data_import(scholar_db, config["scholar_data_path"])
        
        # Run versioning tests if requested
        if args.versioning or run_all:
            test_versioning(scholar_db)
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 