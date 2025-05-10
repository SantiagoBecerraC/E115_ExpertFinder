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
import logging

from sentence_transformers import SentenceTransformer
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from .dvc_utils import DVCManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages all ChromaDB operations including initialization, querying, and data management."""

    def __init__(self, collection_name: str = "google_scholar", n_results: int = 100):
        """
        Initialize ChromaDB manager.

        Args:
            collection_name: Name of the ChromaDB collection
            n_results: Default number of results to return from queries
        """
        self.collection_name = collection_name
        self.n_results = max(1, n_results)  # Ensure n_results is at least 1
        self.client = None
        self.collection = None
        self.embedding_function = None
        self._initialize_chromadb()

    def _create_embedding_function(self):
        """Create embedding function using SentenceTransformer."""
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Get absolute path to database directory
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            db_path = project_root / "chromadb"

            # Create the database directory if it doesn't exist
            db_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using ChromaDB path: {db_path}")

            # Initialize client
            self.client = chromadb.PersistentClient(path=str(db_path))
            logger.info("ChromaDB client initialized")

            # Create embedding function
            self.embedding_function = self._create_embedding_function()
            logger.info("Embedding function created")

            # Try to get or create collection
            try:
                # List all collections (in v0.6.0+ this returns just the names)
                collection_names = self.client.list_collections()
                logger.info(f"Existing collections: {collection_names}")

                if self.collection_name in collection_names:
                    # Get existing collection
                    logger.info(f"Getting existing collection: {self.collection_name}")
                    self.collection = self.client.get_collection(
                        name=self.collection_name, embedding_function=self.embedding_function
                    )

                    # Get collection info
                    count = self.collection.count()
                    logger.info(f"Collection has {count} documents")

                    # Test the collection with a simple query
                    try:
                        self.collection.query(query_texts=["test query"], n_results=1)
                        logger.info("Successfully tested collection with query")
                    except Exception as e:
                        if "dimension" in str(e).lower():
                            logger.warning("Dimension mismatch detected. Recreating collection...")
                            self.reset_collection()
                        else:
                            logger.error(f"Error testing collection: {str(e)}")
                            raise e
                else:
                    # Create new collection
                    logger.info(f"Creating new collection: {self.collection_name}")
                    self.collection = self.client.create_collection(
                        name=self.collection_name, embedding_function=self.embedding_function
                    )
                    logger.info("New collection created successfully")

            except Exception as e:
                logger.error(f"Error with collection initialization: {str(e)}")
                raise e

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to initialize ChromaDB: {str(e)}")

    def query(self, query_text: str, n_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query the ChromaDB collection.

        Args:
            query_text: Text to search for
            n_results: Number of results to return (uses instance default if not specified)

        Returns:
            List of dictionaries containing search results sorted by citations.
            Returns empty list if no results found.
        """
        try:
            # Use instance default if n_results not specified
            n_results = n_results or self.n_results

            # Ensure n_results is positive
            n_results = max(1, n_results)

            # Query collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
            )

            # Check if we have any results
            if not results or not results.get("documents") or not results["documents"]:
                logger.info(f"No results found for query: {query_text}")
                return []

            # Ensure we have matching lengths of documents and metadata
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []

            if not documents or len(documents) != len(metadatas):
                logger.warning("Mismatch between documents and metadata or empty results")
                return []

            # Process and sort results
            sorted_results = []
            for doc, meta in zip(documents, metadatas):
                try:
                    # Convert citations to int, default to 0 if invalid
                    citations = 0
                    try:
                        citations = int(meta.get("citations", "0"))
                    except (ValueError, TypeError):
                        pass

                    # Create result entry with all fields defaulting to empty strings
                    result = {
                        "content": str(doc) if doc else "",
                        "metadata": {
                            "doc_type": str(meta.get("doc_type", "")),
                            "author": str(meta.get("author", "")),
                            "affiliations": str(meta.get("affiliations", "")),
                            "interests": str(meta.get("interests", "")),
                            "citations": str(citations),
                            "url": str(meta.get("url", "")),
                            "chunk_index": str(meta.get("chunk_index", "")),
                            "original_id": str(meta.get("original_id", "")),
                        },
                        "citations": citations,
                    }
                    sorted_results.append(result)

                except Exception as e:
                    logger.warning(f"Error processing result: {str(e)}")
                    continue

            # Sort by citations (highest first) if we have any results
            if sorted_results:
                sorted_results.sort(key=lambda x: x["citations"], reverse=True)

            return sorted_results

        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {str(e)}")
            return []  # Return empty list instead of raising error

    def add_documents(self, documents: List[str], ids: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Add documents to the ChromaDB collection.

        Args:
            documents: List of document contents
            ids: List of unique IDs for the documents
            metadatas: Optional list of metadata dictionaries for each document
        """
        try:
            # Validate inputs
            if not documents or not ids:
                raise ValueError("Documents and IDs cannot be empty")
            if len(documents) != len(ids):
                raise ValueError("Number of documents must match number of IDs")
            if metadatas and len(metadatas) != len(documents):
                raise ValueError("Number of metadata entries must match number of documents")

            # Ensure all documents are strings and not empty
            documents = [str(doc).strip() for doc in documents if doc and str(doc).strip()]
            if not documents:
                logger.warning("No valid documents to add after filtering")
                return

            # Ensure all metadata values are strings
            if metadatas:
                for metadata in metadatas:
                    for key in metadata:
                        if metadata[key] is None:
                            metadata[key] = ""
                        else:
                            metadata[key] = str(metadata[key])

            # Add to collection in smaller batches to avoid API limits
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                self.collection.add(
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end] if metadatas else None,
                    ids=ids[i:batch_end],
                )
                logger.info(f"Added batch of {batch_end - i} documents")

            logger.info(f"Successfully added {len(documents)} documents to ChromaDB")

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
            project_root = current_file.parent.parent.parent.parent
            db_path = project_root / "chromadb"

            return {"name": self.collection_name, "document_count": count, "location": str(db_path)}

        except Exception as e:
            raise RuntimeError(f"Failed to get collection stats: {str(e)}")

    def delete_collection(self):
        """Delete the current collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = None
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete collection: {str(e)}")

    def reset_collection(self):
        """Reset the collection by deleting and recreating it."""
        try:
            logger.info(f"Resetting collection: {self.collection_name}")
            # Delete existing collection
            self.client.delete_collection(self.collection_name)
            logger.info("Existing collection deleted")

            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name, embedding_function=self.embedding_function
            )
            logger.info("Collection recreated successfully")
        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}")
            raise RuntimeError(f"Failed to reset collection: {str(e)}")

    def add_documents_with_version(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        update_info: Optional[Dict[str, Any]] = None,
        version_after_batch: bool = False,
    ) -> bool:
        """
        Add documents to the ChromaDB collection with optional DVC versioning.

        Args:
            documents: List of document contents
            ids: List of unique IDs for the documents
            metadatas: Optional list of metadata dictionaries for each document
            update_info: Optional information about the update for DVC commit message
            version_after_batch: If True, version the database after adding documents

        Returns:
            bool: True if documents were added successfully, False otherwise
        """
        try:
            # Add documents using existing method
            self.add_documents(documents, ids, metadatas)

            # If versioning is requested, use DVC to version the database
            if version_after_batch:
                dvc_manager = DVCManager()
                return dvc_manager.version_database(update_info)

            return True

        except Exception as e:
            logger.error(f"Failed to add documents with versioning: {str(e)}")
            return False
