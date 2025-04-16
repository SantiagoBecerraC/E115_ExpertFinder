#!/usr/bin/env python3
"""
Command-line interface for Google Scholar data extraction and processing.

USAGE:
    python cli.py download --query "your search query" [options]
    python cli.py process [options]
    python cli.py vectorize [options]
    python cli.py test --query "your search query" [options]
    python cli.py pipeline --query "your search query" [options]

OPTIONS:
    --query TEXT           (Required for download/test/pipeline) The search query for Google Scholar
    --start-year TEXT     Start year for filtering (default: "2022")
    --end-year TEXT       End year for filtering (default: "2025")
    --num-results INT     Total number of results to fetch (default: 20)
    --results-per-page INT Results per page (default: 10, max: 20)
    --input-file TEXT     (Optional for process) Specific JSON file to process
    --collection TEXT     (Optional for vectorize/test) ChromaDB collection name (default: "google_scholar")
    --n-results INT       (Optional for test) Number of results to return (default: 5)
    --doc-type TEXT       (Optional for test) Filter results by document type (author, website_content, journal_content)
    --skip-test           (Optional for pipeline) Skip the test step after vectorization

EXAMPLES:
    # Basic usage with just a query
    python cli.py download --query "machine learning"
    
    # With custom year range
    python cli.py download --query "deep learning" --start-year 2020 --end-year 2023
    
    # With custom number of results
    python cli.py download --query "artificial intelligence" --num-results 50 --results-per-page 20
    
    # Process all downloaded files
    python cli.py process
    
    # Process a specific file
    python cli.py process --input-file path/to/your/file.json
    
    # Vectorize processed data
    python cli.py vectorize
    
    # Vectorize with custom collection name
    python cli.py vectorize --collection "my_collection"
    
    # Test query on vectorized data
    python cli.py test --query "machine learning"
    
    # Test query with custom options
    python cli.py test --query "deep learning" --n-results 10 --doc-type author
    
    # Run the entire pipeline
    python cli.py pipeline --query "machine learning"
    
    # Run the pipeline with custom options
    python cli.py pipeline --query "deep learning" --start-year 2020 --end-year 2023 --num-results 50 --collection "my_collection"
"""

import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_file = Path(__file__)
parent_dir = current_file.parent.parent
sys.path.append(str(parent_dir))

# Import the necessary modules
from google_scholar.download_scholar_data import extract_data, save_to_json
from google_scholar.SerpAPI_GoogleScholar import GoogleScholar
from google_scholar.scholar_data_processor import process_scholar_data, prepare_chroma_data, save_to_json as save_processed_json
from google_scholar.scholar_data_vectorization import load_google_scholar_data, prepare_documents_for_chromadb, load_to_chromadb
from utils.chroma_db_utils import ChromaDBManager
from dotenv import load_dotenv

# Load environment variables
project_root = current_file.parent.parent.parent.parent
env_path = project_root / 'secrets' / '.env'
load_dotenv(dotenv_path=env_path)

# Get API key from environment variables
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY not found in environment variables")

def download_data(query, start_year, end_year, num_results, results_per_page):
    """Download data from Google Scholar for the given query."""
    print(f"Downloading data for query: {query}")
    
    # Initialize Google Scholar client
    scholar_client = GoogleScholar(SERPAPI_API_KEY)
    
    # Extract data from Google Scholar
    articles_data = extract_data(
        query, start_year, end_year, num_results, results_per_page, scholar_client=scholar_client
    )
    
    # Save extracted data to JSON
    save_to_json(articles_data, query, start_year, end_year, num_results)
    
    print(f"Data downloaded and saved for query: {query}")

def process_data(input_file=None):
    """Process downloaded Google Scholar data and prepare it for ChromaDB."""
    try:
        # Find JSON files to process
        data_dir = project_root / "google-scholar-data"
        if input_file:
            json_files = [Path(input_file)]
        else:
            json_files = list(data_dir.glob('Google_Scholar_Data_*.json'))
        
        if not json_files:
            print(f"No Google Scholar data files found in {data_dir}")
            return
            
        print(f"Found {len(json_files)} files to process")
        
        # Initialize combined data structure
        combined_authors_data = {}
        
        # Process each JSON file
        for json_file in json_files:
            print(f"\nProcessing file: {json_file}")
            
            # Process the data from this file
            authors_data = process_scholar_data(json_file)
            
            if not authors_data:
                print("No data was processed from this file. Skipping...")
                continue
            
            # Merge the data into combined_authors_data
            for author_name, author_data in authors_data.items():
                if author_name not in combined_authors_data:
                    combined_authors_data[author_name] = author_data
                else:
                    # Merge articles lists, avoiding duplicates based on title
                    existing_titles = {article['title'] for article in combined_authors_data[author_name]['articles']}
                    new_articles = [article for article in author_data['articles'] 
                                  if article['title'] not in existing_titles]
                    combined_authors_data[author_name]['articles'].extend(new_articles)
        
        if not combined_authors_data:
            print("No data was processed from any file. Please check the input file format.")
            return
        
        # Prepare data for ChromaDB
        print("\nPreparing combined data for ChromaDB...")
        chroma_ready_data = prepare_chroma_data(combined_authors_data)
        
        # Create output directory and save processed data
        output_dir = data_dir / "processed_data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save files inside the processed_data directory
        save_processed_json(combined_authors_data, output_dir / "data.processed.json")
        save_processed_json(chroma_ready_data, output_dir / "data.chroma.json")
        
        print(f"\nOriginal processed data saved to: {output_dir / 'data.processed.json'}")
        print(f"ChromaDB-ready data saved to: {output_dir / 'data.chroma.json'}")
        print(f"Total authors: {len(chroma_ready_data['authors'])}")
        print(f"Total articles: {len(chroma_ready_data['articles'])}")
        print("\nSummary of processed files:")
        for json_file in json_files:
            print(f"- {json_file.name}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def vectorize_data(collection_name="google_scholar"):
    """Vectorize processed data and store it in ChromaDB."""
    try:
        print("Loading Google Scholar data...")
        input_data = load_google_scholar_data()
        
        # Initialize ChromaDB manager
        print(f"Initializing ChromaDB with collection: {collection_name}")
        db_manager = ChromaDBManager(collection_name=collection_name)
        
        # Process each author and store in ChromaDB
        all_documents = []
        for author_name, data in input_data.items():
            print(f"Processing author: {author_name}")
            documents = prepare_documents_for_chromadb(author_name, data)
            all_documents.extend(documents)
        
        # Store all documents in ChromaDB
        print(f"Storing {len(all_documents)} documents in ChromaDB...")
        load_to_chromadb(all_documents, db_manager)
        
        print("\nVectorization complete!")
        print(f"Total documents stored: {len(all_documents)}")
        
    except Exception as e:
        print(f"An error occurred during vectorization: {e}")
        import traceback
        traceback.print_exc()

def print_author_result(result, index):
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

def print_content_result(result, index):
    """Print formatted content result."""
    print(f"\nContent Result {index}:")
    print("-"*40)
    print(f"Type: {result['metadata'].get('doc_type', 'N/A')}")
    print(f"Author: {result['metadata'].get('author', 'N/A')}")
    print(f"URL: {result['metadata'].get('url', 'N/A')}")
    print(f"Chunk Index: {result['metadata'].get('chunk_index', 'N/A')}")
    print(f"\nContent Preview:")
    print(f"{result['content'][:200]}...")

def test_data(query, collection_name="google_scholar", n_results=5, doc_type=None):
    """Test query on vectorized data in ChromaDB."""
    try:
        print(f"Initializing ChromaDB with collection: {collection_name}")
        db_manager = ChromaDBManager(collection_name=collection_name)
        
        # Verify the collection exists and has documents
        try:
            count = db_manager.collection.count()
            print(f"Collection has {count} documents")
            if count == 0:
                print("Collection is empty! Please run vectorize command first")
                return
        except Exception as e:
            print(f"Error accessing collection: {str(e)}")
            return
        
        print(f"\nQuerying ChromaDB with: {query}")
        results = db_manager.query(query, n_results=n_results)
        print(f"Got {len(results)} results from ChromaDB")
        
        if not results:
            print("No results returned from query")
            return
        
        # Filter results by document type if specified
        if doc_type:
            filtered_results = [r for r in results if r['metadata'].get('doc_type') == doc_type]
            print(f"Results after filtering by doc_type '{doc_type}': {len(filtered_results)}")
            results = filtered_results
        
        # Sort by citations if available
        try:
            results.sort(
                key=lambda x: int(x['metadata'].get('citations', '0')), 
                reverse=True
            )
        except (ValueError, TypeError) as e:
            print(f"Could not sort by citations - {str(e)}")
        
        # Print results
        if not results:
            print("No matching results found.")
            return
            
        for i, result in enumerate(results, 1):
            if result['metadata'].get('doc_type') == 'author':
                print_author_result(result, i)
            else:
                print_content_result(result, i)
        
    except Exception as e:
        print(f"An error occurred during testing: {e}")
        import traceback
        traceback.print_exc()

def pipeline(query, start_year, end_year, num_results, results_per_page, collection_name="google_scholar", n_results=5, doc_type=None, skip_test=False):
    """Run the entire pipeline: download, process, vectorize, and test."""
    try:
        print("\n" + "="*50)
        print("STARTING EXPERT FINDER PIPELINE")
        print("="*50)
        
        # Step 1: Download data
        print("\n" + "-"*50)
        print("STEP 1: DOWNLOADING DATA")
        print("-"*50)
        download_data(query, start_year, end_year, num_results, results_per_page)
        
        # Step 2: Process data
        print("\n" + "-"*50)
        print("STEP 2: PROCESSING DATA")
        print("-"*50)
        process_data()
        
        # Step 3: Vectorize data
        print("\n" + "-"*50)
        print("STEP 3: VECTORIZING DATA")
        print("-"*50)
        vectorize_data(collection_name)
        
        # Step 4: Test query (optional)
        if not skip_test:
            print("\n" + "-"*50)
            print("STEP 4: TESTING QUERY")
            print("-"*50)
            test_data(query, collection_name, n_results, doc_type)
        
        print("\n" + "="*50)
        print("EXPERT FINDER PIPELINE COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"\nAn error occurred during the pipeline: {e}")
        import traceback
        traceback.print_exc()
        print("\nPipeline failed. Please check the error messages above.")

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Google Scholar data extraction and processing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download data from Google Scholar")
    download_parser.add_argument("--query", type=str, required=True, help="Search query")
    download_parser.add_argument("--start-year", type=str, default="2022", help="Start year for filtering")
    download_parser.add_argument("--end-year", type=str, default="2025", help="End year for filtering")
    download_parser.add_argument("--num-results", type=int, default=20, help="Total results to fetch")
    download_parser.add_argument("--results-per-page", type=int, default=10, help="Results per page (max 20)")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process downloaded Google Scholar data")
    process_parser.add_argument("--input-file", type=str, help="Specific JSON file to process")
    
    # Vectorize command
    vectorize_parser = subparsers.add_parser("vectorize", help="Vectorize processed data and store in ChromaDB")
    vectorize_parser.add_argument("--collection", type=str, default="google_scholar", help="ChromaDB collection name")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test query on vectorized data in ChromaDB")
    test_parser.add_argument("--query", type=str, required=True, help="Search query")
    test_parser.add_argument("--collection", type=str, default="google_scholar", help="ChromaDB collection name")
    test_parser.add_argument("--n-results", type=int, default=5, help="Number of results to return")
    test_parser.add_argument("--doc-type", type=str, choices=["author", "website_content", "journal_content"], help="Filter results by document type")
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run the entire pipeline: download, process, vectorize, and test")
    pipeline_parser.add_argument("--query", type=str, required=True, help="Search query")
    pipeline_parser.add_argument("--start-year", type=str, default="2022", help="Start year for filtering")
    pipeline_parser.add_argument("--end-year", type=str, default="2025", help="End year for filtering")
    pipeline_parser.add_argument("--num-results", type=int, default=20, help="Total results to fetch")
    pipeline_parser.add_argument("--results-per-page", type=int, default=10, help="Results per page (max 20)")
    pipeline_parser.add_argument("--collection", type=str, default="google_scholar", help="ChromaDB collection name")
    pipeline_parser.add_argument("--n-results", type=int, default=5, help="Number of results to return for test")
    pipeline_parser.add_argument("--doc-type", type=str, choices=["author", "website_content", "journal_content"], help="Filter results by document type")
    pipeline_parser.add_argument("--skip-test", action="store_true", help="Skip the test step after vectorization")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == "download":
        download_data(
            args.query, 
            args.start_year, 
            args.end_year, 
            args.num_results, 
            args.results_per_page
        )
    elif args.command == "process":
        process_data(args.input_file)
    elif args.command == "vectorize":
        vectorize_data(args.collection)
    elif args.command == "test":
        test_data(args.query, args.collection, args.n_results, args.doc_type)
    elif args.command == "pipeline":
        pipeline(
            args.query,
            args.start_year,
            args.end_year,
            args.num_results,
            args.results_per_page,
            args.collection,
            args.n_results,
            args.doc_type,
            args.skip_test
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 