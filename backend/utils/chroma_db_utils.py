"""
Utility class for ChromaDB operations.
Handles database initialization, querying, and management.
"""

import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class ChromaDBManager:
    """Manages all ChromaDB operations including initialization, querying, and data management."""
    
    def __init__(self, collection_name: str = "google_scholar", n_results: int = 5):
        """
        Initialize ChromaDB manager.
        
        Args:
            collection_name: Name of the ChromaDB collection
            n_results: Default number of results to return from queries
        """
        self.collection_name = collection_name
        self.n_results = n_results
        self.client = None
        self.collection = None
        self.embedding_function = None
        self._initialize_chromadb()
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from environment variables."""
        # Load environment variables from the secrets folder at project root
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
        env_path = project_root / 'secrets' / '.env'
        print(env_path)

        load_dotenv(dotenv_path=env_path)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it in your environment or in a .env file."
            )
        return api_key
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Get absolute path to database directory from backend root
            # Load environment variables from the secrets folder at project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
            db_path = project_root / 'chromadb'
            
            # Create the database directory if it doesn't exist
            db_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize client
            self.client = chromadb.PersistentClient(path=str(db_path))
            
            # Setup embedding function
            api_key = self._get_api_key()
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-ada-002"
            )
            
            # Try to get existing collection or create a new one
            try:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                print(f"Successfully initialized collection: {self.collection_name}")
            except Exception as e:
                print(f"Error with collection: {str(e)}")
                print("Attempting to create new collection...")
                # If get_or_create fails, try explicit creation
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                print(f"Created new collection: {self.collection_name}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB: {str(e)}")
    
    def query(self, query_text: str, n_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query the ChromaDB collection.
        
        Args:
            query_text: Text to search for
            n_results: Number of results to return (uses instance default if not specified)
            
        Returns:
            List of dictionaries containing search results sorted by citations
        """
        try:
            # Use instance default if n_results not specified
            n_results = n_results or self.n_results
            
            # Query collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Process and sort results
            sorted_results = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                citations = int(meta.get('citations', '0'))
                sorted_results.append({
                    'content': doc,
                    'metadata': meta,
                    'citations': citations
                })
            
            # Sort by citations (highest first)
            sorted_results.sort(key=lambda x: x['citations'], reverse=True)
            return sorted_results
            
        except Exception as e:
            raise RuntimeError(f"Failed to query ChromaDB: {str(e)}")
    
    def add_documents(self, documents: List[str], ids: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Add documents to the ChromaDB collection.
        
        Args:
            documents: List of document contents
            ids: List of unique IDs for the documents
            metadatas: Optional list of metadata dictionaries for each document
        """
        try:
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to ChromaDB: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current collection.
        
        Returns:
            Dictionary containing collection statistics
        """
        try:
            count = self.collection.count()
            
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
            db_path = project_root / 'chromadb'
            
            return {
                "name": self.collection_name,
                "document_count": count,
                "location": str(db_path)
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get collection stats: {str(e)}")
    
    def delete_collection(self):
        """Delete the current collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = None
        except Exception as e:
            raise RuntimeError(f"Failed to delete collection: {str(e)}")
    
    def reset_collection(self):
        """Reset the collection by deleting and recreating it."""
        try:
            self.delete_collection()
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            raise RuntimeError(f"Failed to reset collection: {str(e)}") 