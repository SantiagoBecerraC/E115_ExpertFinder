"""
Script to load normalized Google Scholar data into ChromaDB.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to Python path to allow imports from utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.chroma_db_utils import ChromaDBManager

def load_normalized_data(data_path):
    """
    Load normalized data from JSON file.
    
    Args:
        data_path: Path to the normalized data JSON file
        
    Returns:
        List of normalized documents
    """
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_to_chromadb(documents, db_manager):
    """
    Load documents into ChromaDB collection.
    
    Args:
        documents: List of normalized documents
        db_manager: ChromaDBManager instance
    """
    # Prepare data for batch loading
    ids = []
    contents = []
    metadatas = []
    
    for doc in documents:
        ids.append(doc["id"])
        contents.append(doc["content"])
        
        # Convert lists to strings and handle None values in metadata
        metadata = {}
        for key, value in doc["metadata"].items():
            if value is None:
                # Convert None to appropriate default values based on field type
                if key in ['year', 'citations']:
                    metadata[key] = 0
                else:
                    metadata[key] = ''
            elif isinstance(value, list):
                # Handle empty lists
                if not value:
                    metadata[key] = ''
                else:
                    metadata[key] = '; '.join(str(v) for v in value if v is not None)
            else:
                metadata[key] = str(value)  # Convert all other values to strings
        
        metadatas.append(metadata)
    
    # Add documents to collection using the correct format
    db_manager.add_documents(
        documents=contents,
        ids=ids,
        metadatas=metadatas
    )
    
    print(f"Added {len(ids)} documents to ChromaDB collection")

def main():
    """
    Main function to load data into ChromaDB.
    """
    try:
        # Setup directory structure
        # Load environment variables from the secrets folder at project root
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
        data_path = project_root / 'google-scholar-data' / 'normalized_data_for_chroma.json'
        
        # Verify data file exists
        if not data_path.exists():
            raise FileNotFoundError(f"Normalized data file not found: {data_path}")
        
        # Initialize ChromaDB manager
        print("Initializing ChromaDB...")
        db_manager = ChromaDBManager(collection_name="google_scholar")
        
        # Load normalized data
        print(f"Loading data from: {data_path}")
        documents = load_normalized_data(data_path)
        print(f"Loaded {len(documents)} documents")
        
        # Load documents into ChromaDB
        print("Loading documents into ChromaDB...")
        load_to_chromadb(documents, db_manager)
        
        print("\nData successfully loaded into ChromaDB")
        
        # Example query to verify loading
        print("\nRunning test query...")
        results = db_manager.query("machine learning", n_results=2)
        print("\nExample query results:")
        for idx, result in enumerate(results, 1):
            print(f"\nResult {idx}:")
            print(f"Title: {result['metadata'].get('title', 'N/A')}")
            print(f"Year: {result['metadata'].get('year', 'N/A')}")
            print(f"Citations: {result['metadata'].get('citations', 'N/A')}")
            # Split authors string back into list for display
            authors = result['metadata'].get('authors', '').split('; ') if result['metadata'].get('authors') else []
            print(f"Authors: {', '.join(authors)}")
        
    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
        print("Please ensure you have:")
        print("1. Run prepare_chromadb_data.py to generate the normalized data file")
    except Exception as e:
        print(f"\nError loading data into ChromaDB: {str(e)}")
        print("If this is an OpenAI API error, please check your API key configuration.")

if __name__ == "__main__":
    main() 