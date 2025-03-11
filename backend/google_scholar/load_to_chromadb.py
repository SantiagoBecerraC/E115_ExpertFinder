"""
Script to load normalized Google Scholar data into ChromaDB.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
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

def initialize_chromadb(db_path):
    """
    Initialize ChromaDB and reset collection.
    
    Args:
        db_path: Path to ChromaDB persistence directory
    """
    print("Initializing ChromaDB...")
    
    # Create ChromaDB manager
    db_manager = ChromaDBManager(collection_name="google_scholar")
    
    # Reset collection (delete and recreate)
    print("Resetting existing collection...")
    db_manager.reset_collection()
    
    return db_manager

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
    
    # Keep track of seen IDs to handle duplicates
    seen_ids = set()
    
    for i, doc in enumerate(documents):
        try:
            original_id = doc["id"]
            
            # For articles that appear multiple times (once per author), make the ID unique
            # by appending a counter if needed
            doc_id = original_id
            counter = 1
            while doc_id in seen_ids:
                doc_id = f"{original_id}_{counter}"
                counter += 1
            
            # Get content first
            document_content = None
            if 'content' in doc:
                document_content = doc["content"]
            elif 'document' in doc:
                document_content = doc["document"]
            else:
                print(f"\nDocument {i} missing both 'content' and 'document' keys. Available keys: {list(doc.keys())}")
                print(f"Document ID: {original_id}")
                continue  # Skip this document
                
            # Process metadata
            metadata = {}
            if "metadata" in doc:
                for key, value in doc["metadata"].items():
                    if key == 'citations':  # Skip the citations array, just keep citation_details
                        continue
                        
                    if value is None:
                        # Convert None to appropriate default values based on field type
                        if key in ['year', 'citations_count']:
                            metadata[key] = 0
                        else:
                            metadata[key] = ''
                    elif key == 'citation_details':
                        # Join citation details into a single string
                        if isinstance(value, list):
                            metadata[key] = '; '.join(str(v) for v in value if v)
                        else:
                            metadata[key] = str(value)
                    elif isinstance(value, list):
                        # Handle empty lists
                        if not value:
                            metadata[key] = ''
                        else:
                            metadata[key] = '; '.join(str(v) for v in value if v is not None)
                    else:
                        metadata[key] = str(value)  # Convert all other values to strings
                
                # Add original ID and document type to metadata
                metadata['original_id'] = original_id
                metadata['doc_type'] = 'author' if 'interests' in doc['metadata'] else 'article'
                
                # Only add document if we have all required components
                seen_ids.add(doc_id)
                ids.append(doc_id)
                contents.append(document_content)
                metadatas.append(metadata)
            else:
                print(f"\nDocument {i} missing metadata. Skipping...")
                continue
                
        except Exception as e:
            print(f"\nError processing document {i}: {str(e)}")
            print(f"Document structure: {doc}")
            continue  # Skip problematic documents instead of failing
    
    # Verify lengths match
    if not (len(ids) == len(contents) == len(metadatas)):
        print("\nLength mismatch in processed data:")
        print(f"IDs: {len(ids)}")
        print(f"Contents: {len(contents)}")
        print(f"Metadatas: {len(metadatas)}")
        raise ValueError("Mismatch in processed data lengths")
    
    # Add documents to collection using the correct format
    if ids:  # Only add if we have documents to add
        db_manager.add_documents(
            documents=contents,
            ids=ids,
            metadatas=metadatas
        )
        print(f"Added {len(ids)} documents to ChromaDB collection")
    else:
        print("No valid documents to add to ChromaDB")

def main():
    """
    Main function to load data into ChromaDB.
    """
    try:
        # Find the most recent JSON file in the google-scholar-data directory
        data_dir = Path(__file__).parent.parent.parent.parent / "google-scholar-data" / "processed_data"
        json_files = list(data_dir.glob('data.chroma*.json'))

        if not json_files:
            print(f"No ChromaDB-ready data files found in {data_dir}")
            sys.exit(1)

        latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"Processing file: {latest_json}")

        # Set up ChromaDB directory
        db_path = Path(__file__).parent.parent.parent.parent / "chromadb"
        db_path.mkdir(parents=True, exist_ok=True)
        
        # Verify data file exists
        if not latest_json.exists():
            raise FileNotFoundError(f"Normalized data file not found: {latest_json}")
        
        # Initialize ChromaDB and get collection manager
        db_manager = initialize_chromadb(db_path)
        
        # Load normalized data
        print(f"Loading data from: {latest_json}")
        data = load_normalized_data(latest_json)
        
        # Extract authors and articles from the loaded data
        if isinstance(data, dict) and 'authors' in data and 'articles' in data:
            authors_data = data['authors']
            articles_data = data['articles']
            print(f"\nLoaded {len(authors_data)} authors and {len(articles_data)} articles")
            
            # Combine authors and articles into a single list
            all_documents = authors_data + articles_data
            
            # Load all documents into ChromaDB
            print("\nLoading documents into ChromaDB...")
            load_to_chromadb(all_documents, db_manager)
            
            print("\nData successfully loaded into ChromaDB")
            
            # Example queries to verify loading
            print("\n" + "="*50)
            print("RUNNING TEST QUERIES")
            print("="*50)
            
            # Test query for authors
            print("\n1. Testing Author Search:")
            print("-"*30)
            results = db_manager.query(
                "machine learning", 
                n_results=5
            )
            
            # Debug: Print the structure of results
            if results:
                print("\nResult Structure:")
                print("-"*20)
                for key in results[0].keys():
                    print(f"Key: {key}")
                    if key == 'metadata':
                        print("Metadata fields:")
                        for mkey in results[0]['metadata'].keys():
                            print(f"  - {mkey}")
                
            # Filter and display author results
            author_results = [r for r in results if r['metadata'].get('doc_type') == 'author'][:3]
            for idx, result in enumerate(author_results, 1):
                print(f"\nAuthor Result {idx}:")
                print("-"*20)
                print(f"Author: {result['metadata'].get('author', 'N/A')}")
                print(f"Affiliations: {result['metadata'].get('affiliations', 'N/A')}")
                print(f"Interests: {result['metadata'].get('interests', 'N/A')}")
                print(f"Citations: {result['metadata'].get('citations', 'N/A')}")
                print(f"Number of Articles: {result['metadata'].get('num_articles', 'N/A')}")
                print(f"Content: {result.get('document', result.get('content', 'N/A'))[:200]}...")
            
            # Test query for articles
            print("\n2. Testing Article Search:")
            print("-"*30)
            results = db_manager.query(
                "deep learning applications", 
                n_results=5
            )
            
            # Filter and display article results
            article_results = [r for r in results if r['metadata'].get('doc_type') == 'article'][:3]
            for idx, result in enumerate(article_results, 1):
                print(f"\nArticle Result {idx}:")
                print("-"*20)
                print(f"Title: {result['metadata'].get('title', 'N/A')}")
                print(f"Author: {result['metadata'].get('author_name', 'N/A')}")
                print(f"Year: {result['metadata'].get('year', 'N/A')}")
                print(f"Citations: {result['metadata'].get('citations_count', 'N/A')}")
                print(f"Journal URL: {result['metadata'].get('journal_url', 'N/A')}")
                print(f"Content: {result.get('document', result.get('content', 'N/A'))[:200]}...")
            
            # Test specific field search
            print("\n3. Testing Field-Specific Search:")
            print("-"*30)
            
            # Search for authors with high citations
            high_citation_results = db_manager.query(
                "artificial intelligence", 
                n_results=3
            )
            
            print("\nTop Authors by Citations:")
            print("-"*20)
            author_results = [r for r in high_citation_results if r['metadata'].get('doc_type') == 'author']
            for idx, result in enumerate(sorted(author_results, 
                                             key=lambda x: int(x['metadata'].get('citations', 0)), 
                                             reverse=True)[:3], 1):
                print(f"\nAuthor {idx}:")
                print(f"Name: {result['metadata'].get('author', 'N/A')}")
                print(f"Citations: {result['metadata'].get('citations', 'N/A')}")
                print(f"Interests: {result['metadata'].get('interests', 'N/A')}")
            
            print("\n" + "="*50)
            print("TEST QUERIES COMPLETED")
            print("="*50)
            
        else:
            raise ValueError("Invalid data format: Expected a dictionary with 'authors' and 'articles' keys")
        
    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
        print("Please ensure you have:")
        print("1. Run prepare_chromadb_data.py to generate the normalized data file")
    except Exception as e:
        print(f"\nError loading data into ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 