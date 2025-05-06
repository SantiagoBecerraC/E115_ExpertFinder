"""
Test script for DVC and ChromaDB integration.
"""

import os
import logging
from utils.chroma_db_utils import ChromaDBManager
from utils.dvc_utils import DVCManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dvc_integration():
    """Test DVC integration with ChromaDB."""
    try:
        # Initialize ChromaDB manager
        logger.info("Initializing ChromaDB manager...")
        db_manager = ChromaDBManager(collection_name="test_collection")
        
        # Add some test documents
        logger.info("Adding test documents...")
        documents = ["Test document 1", "Test document 2"]
        ids = ["doc1", "doc2"]
        metadatas = [{"source": "test"}, {"source": "test"}]
        
        # Add documents with versioning
        logger.info("Adding documents with versioning...")
        success = db_manager.add_documents_with_version(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            update_info={"source": "test", "profiles_added": 2},
            version_after_batch=True
        )
        
        if success:
            logger.info("Successfully added documents and created DVC version")
        else:
            logger.error("Failed to add documents or create DVC version")
        
        # Get version history
        logger.info("Getting version history...")
        dvc_manager = DVCManager()
        history = dvc_manager.get_version_history()
        logger.info(f"Version history: {history}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_dvc_integration: {str(e)}")
        return False

if __name__ == "__main__":
    test_dvc_integration() 