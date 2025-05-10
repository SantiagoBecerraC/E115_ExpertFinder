"""
Unit tests for the ChromaDBManager class in utils/chroma_db_utils.py.

Tests focus on the functionality of the ChromaDBManager class with a
focus on real data structures and realistic usage patterns.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from chromadb.config import Settings

import chromadb
from utils.chroma_db_utils import ChromaDBManager


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB files during tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Set environment variable for test mode
        old_env = os.environ.get("EF_TEST_MODE")
        os.environ["EF_TEST_MODE"] = "1"

        # Set environment variable for ChromaDB path
        old_chromadb_path = os.environ.get("CHROMADB_PATH")
        os.environ["CHROMADB_PATH"] = tmp_dir

        yield tmp_dir

        # Restore environment variables
        if old_env:
            os.environ["EF_TEST_MODE"] = old_env
        else:
            os.environ.pop("EF_TEST_MODE", None)

        if old_chromadb_path:
            os.environ["CHROMADB_PATH"] = old_chromadb_path
        else:
            os.environ.pop("CHROMADB_PATH", None)


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client that returns a controlled mock collection."""
    mock_client = MagicMock()
    mock_collection = MagicMock()

    # Setup the mock collection to return predictable results
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {
        "ids": [["doc1", "doc2"]],
        "documents": [["Test document 1", "Test document 2"]],
        "metadatas": [[{"source": "test"}, {"source": "test"}]],
        "distances": [[0.1, 0.2]],
    }

    # Configure client to return our mock collection
    mock_client.get_collection.return_value = mock_collection
    mock_client.create_collection.return_value = mock_collection

    # Return mocked collections list
    mock_client.list_collections.return_value = []

    return mock_client


@pytest.fixture
def mock_embedding_function():
    """Mock embedding function that returns predictable embeddings."""
    mock_func = MagicMock()
    mock_func.return_value = [[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
    return mock_func


class TestChromaDBManagerInitialization:
    """Test initialization scenarios for ChromaDBManager."""

    def test_create_embedding_function(self):
        """Test the _create_embedding_function method directly."""
        with patch(
            "utils.chroma_db_utils.embedding_functions.SentenceTransformerEmbeddingFunction"
        ) as mock_embedding_cls, patch("utils.chroma_db_utils.chromadb.PersistentClient") as mock_client_cls, patch(
            "utils.chroma_db_utils.ChromaDBManager._initialize_chromadb"
        ):

            # Setup the mock
            mock_embedding = MagicMock()
            mock_embedding_cls.return_value = mock_embedding

            # Create a mock client
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            # Create manager with initialization mocked out
            db_manager = ChromaDBManager()

            # Override the existing embedding function
            db_manager.embedding_function = None

            # Call method directly
            result = db_manager._create_embedding_function()

            # Verify the embedding function was created with the correct model
            mock_embedding_cls.assert_called_once_with(model_name="all-MiniLM-L6-v2")
            assert result == mock_embedding

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    @patch("utils.chroma_db_utils.embedding_functions.SentenceTransformerEmbeddingFunction")
    def test_initialization_with_defaults(self, mock_embedding_cls, mock_client_cls, temp_chroma_dir):
        """Test initialization with default parameters."""
        # Setup mocks
        mock_embedding = MagicMock()
        mock_embedding_cls.return_value = mock_embedding

        mock_client = MagicMock()
        mock_client.list_collections.return_value = []
        mock_collection = MagicMock()
        mock_client.create_collection.return_value = mock_collection
        mock_client_cls.return_value = mock_client

        # Initialize with temp directory for ChromaDB
        with patch.dict(os.environ, {"CHROMADB_PATH": temp_chroma_dir}):
            db_manager = ChromaDBManager()

            # Verify client initialization
            mock_client_cls.assert_called_once()

            # Verify collection creation (since list_collections returns empty list)
            mock_client.create_collection.assert_called_once_with(
                name="google_scholar", embedding_function=mock_embedding  # default name
            )

            # Verify basic properties
            assert db_manager.collection_name == "google_scholar"
            assert db_manager.n_results == 100  # default
            assert db_manager.collection is mock_collection

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    @patch("utils.chroma_db_utils.embedding_functions.SentenceTransformerEmbeddingFunction")
    def test_initialization_with_custom_params(self, mock_embedding_cls, mock_client_cls, temp_chroma_dir):
        """Test initialization with custom parameters."""
        # Setup mocks
        mock_embedding = MagicMock()
        mock_embedding_cls.return_value = mock_embedding

        mock_client = MagicMock()
        mock_client.list_collections.return_value = []
        mock_collection = MagicMock()
        mock_client.create_collection.return_value = mock_collection
        mock_client_cls.return_value = mock_client

        # Custom parameters
        custom_collection_name = "test_collection"
        custom_n_results = 10

        # Initialize with custom parameters
        with patch.dict(os.environ, {"CHROMADB_PATH": temp_chroma_dir}):
            db_manager = ChromaDBManager(collection_name=custom_collection_name, n_results=custom_n_results)

            # Verify collection creation with custom name
            mock_client.create_collection.assert_called_once_with(
                name=custom_collection_name, embedding_function=mock_embedding
            )

            # Verify custom properties
            assert db_manager.collection_name == custom_collection_name
            assert db_manager.n_results == custom_n_results


class TestChromaDBManagerOperations:
    """Test the ChromaDB operations (add, query, etc.)."""

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_collection_dimension_mismatch(self, mock_client_cls, mock_embedding_function):
        """Test handling of dimension mismatch in existing collection."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Create a mock collection that raises dimension mismatch error on query
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5  # Collection has some documents
        dimension_error = Exception("Embedding dimensions do not match")
        mock_collection.query.side_effect = dimension_error

        # Configure the client to return our collection
        mock_client.list_collections.return_value = ["test_collection"]
        mock_client.get_collection.return_value = mock_collection
        mock_client.create_collection.return_value = MagicMock()  # New collection after reset

        # Create manager with mocked embedding function
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            with patch("utils.chroma_db_utils.logger.warning") as mock_warning:
                # This initialization should detect the dimension mismatch and recreate the collection
                db_manager = ChromaDBManager(collection_name="test_collection")

                # Verify it tried to get the existing collection
                mock_client.get_collection.assert_called_once()

                # Verify the dimension mismatch was detected and handled
                mock_warning.assert_called_once()
                assert "Dimension mismatch detected" in mock_warning.call_args[0][0]

                # Verify the collection was reset (deleted and recreated)
                mock_client.delete_collection.assert_called_once_with("test_collection")
                assert mock_client.create_collection.call_count == 1

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_collection_other_error(self, mock_client_cls, mock_embedding_function):
        """Test handling of non-dimension errors in existing collection."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Create a mock collection that raises some other error on query
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5  # Collection has some documents
        other_error = Exception("Some other error")
        mock_collection.query.side_effect = other_error

        # Configure the client to return our collection
        mock_client.list_collections.return_value = ["test_collection"]
        mock_client.get_collection.return_value = mock_collection

        # Create manager with mocked embedding function
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            with patch("utils.chroma_db_utils.logger.error") as mock_error:
                # This initialization should detect the error and re-raise it
                with pytest.raises(Exception) as excinfo:
                    db_manager = ChromaDBManager(collection_name="test_collection")

                # Verify the errors were properly logged - will be multiple error logs
                assert any("Error testing collection" in args[0][0] for args in mock_error.call_args_list)

                # Verify the original error was re-raised
                assert "Some other error" in str(excinfo.value)

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_add_documents(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test adding documents to the collection."""
        # Configure mock client
        mock_client_cls.return_value = mock_chroma_client
        mock_collection = mock_chroma_client.create_collection.return_value

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Test documents to add
            documents = ["Document 1", "Document 2"]
            ids = ["id1", "id2"]
            metadatas = [{"source": "test1"}, {"source": "test2"}]

            # Call the add_documents method - returns None on success, raises RuntimeError on failure
            # We'll assert no exception is raised
            try:
                db_manager.add_documents(documents=documents, ids=ids, metadatas=metadatas)
                # If we get here, the call succeeded
                success = True
            except RuntimeError:
                success = False

            # Verify the collection's add method was called with correct arguments
            mock_collection.add.assert_called_once_with(documents=documents, ids=ids, metadatas=metadatas)

            # Verify success flag
            assert success is True

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_query_collection(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test querying the collection."""
        # Configure mock client and collection with expected query results
        mock_client_cls.return_value = mock_chroma_client
        mock_collection = mock_chroma_client.create_collection.return_value

        # Configure the mock collection.query response
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Test document 1", "Test document 2"]],
            "metadatas": [
                [
                    {
                        "doc_type": "test",
                        "author": "Test Author",
                        "affiliations": "Test University",
                        "interests": "Testing",
                        "citations": "5",
                        "url": "http://test.com",
                        "chunk_index": "1",
                        "original_id": "doc1",
                    },
                    {
                        "doc_type": "test",
                        "author": "Test Author 2",
                        "affiliations": "Test University 2",
                        "interests": "Testing 2",
                        "citations": "10",
                        "url": "http://test2.com",
                        "chunk_index": "2",
                        "original_id": "doc2",
                    },
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        # Expected processed results (this is what ChromaDBManager.query actually returns)
        expected_results = [
            {
                "content": "Test document 2",
                "metadata": {
                    "doc_type": "test",
                    "author": "Test Author 2",
                    "affiliations": "Test University 2",
                    "interests": "Testing 2",
                    "citations": "10",
                    "url": "http://test2.com",
                    "chunk_index": "2",
                    "original_id": "doc2",
                },
                "citations": 10,
            },
            {
                "content": "Test document 1",
                "metadata": {
                    "doc_type": "test",
                    "author": "Test Author",
                    "affiliations": "Test University",
                    "interests": "Testing",
                    "citations": "5",
                    "url": "http://test.com",
                    "chunk_index": "1",
                    "original_id": "doc1",
                },
                "citations": 5,
            },
        ]

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Call query method
            results = db_manager.query("test query", n_results=2)

            # Verify the collection's query method was called
            mock_collection.query.assert_called_once()

            # Assert the correct formatting of results
            assert len(results) == 2
            for idx, result in enumerate(results):
                assert result["content"] == expected_results[idx]["content"]
                assert result["metadata"] == expected_results[idx]["metadata"]
                assert result["citations"] == expected_results[idx]["citations"]

            # Verify results are sorted by citations (highest first)
            assert results[0]["citations"] >= results[1]["citations"]

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_query_empty_results(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test querying the collection when no results are found."""
        # Configure mock client and collection with empty query results
        mock_client_cls.return_value = mock_chroma_client
        mock_collection = mock_chroma_client.create_collection.return_value

        # Configure empty response
        mock_collection.query.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ), patch("utils.chroma_db_utils.logger.info") as mock_info:
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Call query method
            results = db_manager.query("test query with no matches", n_results=2)

            # Verify empty results are handled correctly
            assert len(results) == 0

            # For the log message, just check that logger.info was called
            # We don't need to check the exact message since we're testing functionality
            assert mock_info.called

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_query_with_invalid_citations(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test querying the collection with invalid citation values."""
        # Configure mock client and collection with expected query results
        mock_client_cls.return_value = mock_chroma_client
        mock_collection = mock_chroma_client.create_collection.return_value

        # Configure response with non-integer citations
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Test document 1", "Test document 2"]],
            "metadatas": [
                [
                    {
                        "doc_type": "test",
                        "author": "Test Author",
                        "citations": "invalid",  # Invalid citation value
                        "original_id": "doc1",
                    },
                    {
                        "doc_type": "test",
                        "author": "Test Author 2",
                        "citations": None,  # Missing citation value
                        "original_id": "doc2",
                    },
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Call query method
            results = db_manager.query("test query", n_results=2)

            # Verify results with invalid citations are handled correctly
            assert len(results) == 2
            assert results[0]["citations"] == 0  # Default to 0 for invalid
            assert results[1]["citations"] == 0  # Default to 0 for None

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_query_metadata_document_mismatch(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test querying the collection when there's a mismatch between documents and metadata."""
        # Configure mock client and collection with mismatched query results
        mock_client_cls.return_value = mock_chroma_client
        mock_collection = mock_chroma_client.create_collection.return_value

        # Configure response with different lengths for documents and metadata
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Test document 1", "Test document 2"]],
            "metadatas": [[{"author": "Test Author"}]],  # Only one metadata entry
            "distances": [[0.1, 0.2]],
        }

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ), patch("utils.chroma_db_utils.logger.warning") as mock_warning:

            db_manager = ChromaDBManager(collection_name="test_collection")

            # Call query method
            results = db_manager.query("test query", n_results=2)

            # Should log a warning and return empty results
            assert len(results) == 0

            # Verify warning was logged
            mismatch_warnings = [
                call for call in mock_warning.call_args_list if "Mismatch between documents and metadata" in call[0][0]
            ]
            assert len(mismatch_warnings) > 0

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_query_processing(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test the profile processing in the query method."""
        # Configure mock client and collection with scholar data
        mock_client_cls.return_value = mock_chroma_client
        mock_collection = mock_chroma_client.create_collection.return_value

        # Configure response with typical scholar data
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Test paper 1", "Test paper 2"]],
            "metadatas": [
                [
                    {
                        "doc_type": "test",
                        "author": "Test Author",
                        "affiliations": "Test University",
                        "interests": "Testing",
                        "citations": "100",
                        "url": "http://test1.com",
                        "chunk_index": "1",
                        "original_id": "doc1",
                    },
                    {
                        "doc_type": "test",
                        "author": "Test Author 2",
                        "affiliations": "Test University 2",
                        "interests": "Testing 2",
                        "citations": "50",
                        "url": "http://test2.com",
                        "chunk_index": "2",
                        "original_id": "doc2",
                    },
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Call query method
            results = db_manager.query("test query", n_results=2)

            # Verify scholar data processing
            assert len(results) == 2

            # Results should be sorted by citations (highest first)
            assert results[0]["citations"] == 100
            assert results[1]["citations"] == 50

            # Verify the metadata matches what we sent
            assert results[0]["metadata"]["author"] == "Test Author"
            assert results[0]["metadata"]["affiliations"] == "Test University"
            assert results[0]["content"] == "Test paper 1"

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_create_collection_error(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test error handling during collection creation."""
        # Configure mock client with an error on create_collection
        mock_client_cls.return_value = mock_chroma_client

        # Set collection not to exist
        mock_chroma_client.list_collections.return_value = []

        # Make create_collection raise an exception
        mock_chroma_client.create_collection.side_effect = Exception("Create collection failed")

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ), patch("utils.chroma_db_utils.logger.error") as mock_error:

            # Should raise the exception outside
            with pytest.raises(Exception) as excinfo:
                db_manager = ChromaDBManager(collection_name="test_collection")

            # Verify error was logged
            assert mock_error.call_count > 0
            create_error_logs = [
                call for call in mock_error.call_args_list if "Error with collection initialization" in call[0][0]
            ]
            assert len(create_error_logs) > 0

            # Verify exception was propagated
            assert "Create collection failed" in str(excinfo.value)

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_reset_collection(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test resetting (recreating) a collection."""
        # Configure mock client
        mock_client_cls.return_value = mock_chroma_client

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Call reset method
            db_manager.reset_collection()

            # Verify delete and create were called
            mock_chroma_client.delete_collection.assert_called_once_with("test_collection")
            assert mock_chroma_client.create_collection.call_count == 2  # Once during init, once during reset

    @patch("utils.chroma_db_utils.chromadb.PersistentClient")
    def test_delete_collection_error(self, mock_client_cls, mock_chroma_client, mock_embedding_function):
        """Test error handling when deleting a collection fails."""
        # Configure mock client with an error on delete_collection
        mock_client_cls.return_value = mock_chroma_client
        mock_chroma_client.delete_collection.side_effect = Exception("Delete failed")

        # Create manager with mocked embedding
        with patch(
            "utils.chroma_db_utils.ChromaDBManager._create_embedding_function", return_value=mock_embedding_function
        ):
            db_manager = ChromaDBManager(collection_name="test_collection")

            # Test that errors are caught and logged, but RuntimeError is raised
            with patch("utils.chroma_db_utils.logger.error") as mock_error:
                # The method will raise RuntimeError
                with pytest.raises(RuntimeError) as excinfo:
                    db_manager.reset_collection()

                # Verify error was logged
                mock_error.assert_called_once()
                assert "Failed to reset collection" in mock_error.call_args[0][0]

                # Verify the RuntimeError contains the original error message
                assert "Delete failed" in str(excinfo.value)
