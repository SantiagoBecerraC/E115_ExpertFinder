"""
Script to test and demonstrate ChromaDB query capabilities on the Google Scholar collection.
"""

import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

def initialize_chromadb():
    """
    Initialize ChromaDB client and get the collection with embedding function.
    
    Returns:
        tuple: (ChromaDB collection, embedding function)
    """
    # Load environment variables from the secrets folder at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
    env_path = project_root / 'secrets' / '.env'
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at {env_path}. Please create a .env file in the secrets directory.")
    
    load_dotenv(dotenv_path=env_path)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize ChromaDB client
    db_path = project_root / 'chromadb'
    client = chromadb.PersistentClient(path=str(db_path))
    
    # Create embedding function
    embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-ada-002"
    )
    
    # Get collection with embedding function
    collection = client.get_collection(
        name="google_scholar",
        embedding_function=embedding_function
    )
    
    return collection, embedding_function

def query_collection(collection, query_text, n_results=5):
    """
    Query the collection with proper embedding handling.
    
    Args:
        collection: ChromaDB collection
        query_text: Text to search for
        n_results: Number of results to return
        
    Returns:
        Query results
    """
    return collection.query(
        query_texts=[query_text],
        n_results=n_results
    )

def sort_results_by_citations(results):
    """
    Sort results by citation count in descending order.
    
    Args:
        results: ChromaDB query results
        
    Returns:
        Sorted results as list of tuples (document, metadata)
    """
    # Create list of (doc, metadata) tuples
    result_pairs = list(zip(results['documents'][0], results['metadatas'][0]))
    
    # Sort by citations (convert to int, default to 0 if not available)
    return sorted(
        result_pairs,
        key=lambda x: int(x[1].get('citations', '0')),
        reverse=True
    )

def print_results(results, query=None, sort_by_citations=True):
    """
    Print search results in a formatted way.
    
    Args:
        results: ChromaDB query results
        query: Search query used (optional)
        sort_by_citations: Whether to sort results by citation count
    """
    if query:
        print(f"\nResults for query: '{query}'")
    print(f"Found {len(results['ids'][0])} matches\n")
    
    # Sort results if requested
    if sort_by_citations:
        result_pairs = sort_results_by_citations(results)
        print("Results sorted by citation count (highest to lowest):")
    else:
        result_pairs = list(zip(results['documents'][0], results['metadatas'][0]))
        print("Results in relevance order:")
    
    for idx, (doc, metadata) in enumerate(result_pairs):
        print(f"\nResult {idx + 1}:")
        print(f"Title: {metadata.get('title', 'N/A')}")
        print(f"Year: {metadata.get('year', 'N/A')}")
        print(f"Citations: {metadata.get('citations', 'N/A')}")
        authors = metadata.get('authors', '').split('; ') if metadata.get('authors') else []
        print(f"Authors: {', '.join(authors)}")
        print(f"Query: {metadata.get('query', 'N/A')}")
        print("\nContent Preview:")
        print(doc[:300] + "..." if len(doc) > 300 else doc)
        print("-" * 80)

def test_queries(collection):
    """
    Run various test queries on the collection.
    
    Args:
        collection: ChromaDB collection
    """
    queries = [
        {
            "title": "Basic Semantic Search - Machine Learning Research",
            "query": "recent advances in machine learning and artificial intelligence",
            "description": "recent advances in machine learning and AI"
        },
        {
            "title": "Specific Topic Search - Deep Learning Neural Networks",
            "query": "deep learning neural networks for computer vision",
            "description": "deep learning neural networks for computer vision"
        },
        {
            "title": "Research Methodology Search",
            "query": "experimental research methodology and empirical studies",
            "description": "research methodology and empirical studies"
        },
        {
            "title": "Application Domain Search - Healthcare",
            "query": "machine learning applications in healthcare and medical diagnosis",
            "description": "ML in healthcare and medical diagnosis"
        },
        {
            "title": "Interdisciplinary Research",
            "query": "intersection of machine learning with other scientific fields",
            "description": "ML intersection with other sciences"
        }
    ]
    
    for idx, query_info in enumerate(queries, 1):
        print(f"\n{idx}. {query_info['title']}")
        results = query_collection(
            collection,
            query_info['query']
        )
        print_results(results, query_info['description'])

def main():
    """
    Main function to run ChromaDB tests.
    """
    try:
        print("Initializing ChromaDB...")
        collection, _ = initialize_chromadb()
        
        # Get collection stats
        print("\nCollection Information:")
        count = collection.count()
        print(f"Total documents in collection: {count}")
        
        # Run test queries
        test_queries(collection)
        
        print("\nAll tests completed successfully!")
        
    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
        print("Please ensure you have:")
        print("1. Created a .env file with your OPENAI_API_KEY")
        print("2. Run load_to_chromadb.py first to create and populate the database")
    except ValueError as e:
        print(f"\nError: {str(e)}")
        print("Please set your OPENAI_API_KEY in the .env file")
    except Exception as e:
        print(f"\nError testing ChromaDB: {str(e)}")
        print("If this is an OpenAI API error, please check your API key configuration.")

if __name__ == "__main__":
    main() 