import json
import os
import pytest
import tempfile
from pathlib import Path
import shutil

# Import modules to test
from google_scholar.scholar_data_processor import process_scholar_data, prepare_chroma_data, save_to_json
from google_scholar.scholar_data_vectorization import prepare_documents_for_chromadb, load_to_chromadb
from utils.chroma_db_utils import ChromaDBManager


class TestGoogleScholarPipeline:
    """System test for the entire Google Scholar pipeline from data processing to ChromaDB."""

    @pytest.fixture(scope="class")
    def test_data_path(self):
        """Path to test data file."""
        test_data_dir = Path(__file__).parent.parent / "fixtures" / "test_data"

        # Use the smaller test file if available
        scholar_test_file = test_data_dir / "Google_Scholar_Data_semiglutide_20250414_231353.json"

        if not scholar_test_file.exists():
            # Use alternative test file
            scholar_test_file = list(test_data_dir.glob("**/*Google_Scholar_Data_*.json"))[0]

        assert scholar_test_file.exists(), f"Test data file not found: {scholar_test_file}"
        return scholar_test_file

    @pytest.fixture(scope="class")
    def limited_test_data(self, test_data_path):
        """Return limited test data to prevent hanging in tests."""
        # Load the original data
        with open(test_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create a restricted version with fewer articles
        limited_data = data.copy()

        # Add search_query field which is required by process_scholar_data
        limited_data["search_query"] = data.get("Query", "semaglutide")

        if "Articles" in limited_data and len(limited_data["Articles"]) > 2:
            limited_data["Articles"] = limited_data["Articles"][:2]  # Keep only first 2 articles
            limited_data["Results_Fetched"] = len(limited_data["Articles"])

        # Create a temporary file with the limited data
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(temp_file.name, "w", encoding="utf-8") as f:
            json.dump(limited_data, f)

        # Return the path to the temporary file
        yield Path(temp_file.name)

        # Clean up the temporary file
        try:
            os.unlink(temp_file.name)
        except:
            pass  # Ignore errors on cleanup

    @pytest.fixture(scope="class")
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp(prefix="scholar_test_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)  # Clean up after tests

    @pytest.fixture(scope="class")
    def chroma_db_manager(self):
        """Create a test ChromaDB manager."""
        # Use a special test collection to avoid affecting production data
        db_manager = ChromaDBManager(collection_name="test_google_scholar")

        # Reset the collection to ensure clean state
        db_manager.reset_collection()

        yield db_manager

        # Clean up after tests
        db_manager.delete_collection()

    def test_process_scholar_data(self, limited_test_data):
        """Test processing raw Google Scholar data."""
        # Process the limited test data file
        result = process_scholar_data(limited_test_data)

        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert len(result) > 0, "Should have processed at least one author"

        # Check structure of processed data
        for author_name, author_data in result.items():
            assert isinstance(author_name, str), "Author name should be a string"
            assert "author_info" in author_data, "Missing author_info in processed data"
            assert "articles" in author_data, "Missing articles in processed data"
            assert isinstance(author_data["articles"], list), "Articles should be a list"

            # Check author info
            author_info = author_data["author_info"]
            assert "author" in author_info, "Missing author field in author_info"
            assert author_info["author"] == author_name, "Author name mismatch"

            # Check at least one article if articles exist
            if author_data["articles"]:
                article = author_data["articles"][0]
                assert "title" in article, "Missing title in article"
                assert isinstance(article["title"], str), "Article title should be a string"

        return result

    def test_prepare_chroma_data(self, limited_test_data):
        """Test preparing data for ChromaDB."""
        # First process the data
        processed_data = process_scholar_data(limited_test_data)

        # Prepare data for ChromaDB
        chroma_data = prepare_chroma_data(processed_data, query="test query")

        # Verify result structure
        assert isinstance(chroma_data, dict), "Result should be a dictionary"
        assert "authors" in chroma_data, "Missing authors in ChromaDB data"
        assert "articles" in chroma_data, "Missing articles in ChromaDB data"
        assert isinstance(chroma_data["authors"], list), "Authors should be a list"
        assert isinstance(chroma_data["articles"], list), "Articles should be a list"

        # Check author entries structure if any exist
        if chroma_data["authors"]:
            author = chroma_data["authors"][0]
            assert "id" in author, "Missing id in author entry"
            assert "content" in author, "Missing content in author entry"
            assert "metadata" in author, "Missing metadata in author entry"

            # Check that the query is included in the content
            assert "test query" in author["content"], "Query should be included in content"

        # Check article entries structure if any exist
        if chroma_data["articles"]:
            article = chroma_data["articles"][0]
            assert "id" in article, "Missing id in article entry"
            assert "content" in article, "Missing content in article entry"
            assert "metadata" in article, "Missing metadata in article entry"

            # Check metadata
            assert "author_name" in article["metadata"], "Missing author_name in article metadata"

        return chroma_data

    def test_save_to_json(self, limited_test_data, temp_output_dir):
        """Test saving processed data to JSON files."""
        # First process the data
        processed_data = process_scholar_data(limited_test_data)

        # Save to JSON
        output_file = temp_output_dir / "processed_data.json"
        save_to_json(processed_data, output_file)

        # Verify file was created
        assert output_file.exists(), f"Output file was not created: {output_file}"

        # Read and verify content
        with open(output_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == processed_data, "Loaded data should match the original data"

        return output_file

    def test_prepare_documents_for_chromadb(self, limited_test_data):
        """Test preparing documents for ChromaDB from processed data."""
        # First process the data
        processed_data = process_scholar_data(limited_test_data)

        # Take one author for this test
        author_name = list(processed_data.keys())[0]
        author_data = processed_data[author_name]

        # Prepare documents for ChromaDB
        documents = prepare_documents_for_chromadb(author_name, author_data)

        # Verify result
        assert isinstance(documents, list), "Result should be a list of documents"

        # If we have documents, check their structure
        if documents:
            doc = documents[0]
            assert "id" in doc, "Missing id in document"
            assert "content" in doc, "Missing content in document"
            assert "metadata" in doc, "Missing metadata in document"

            # Check metadata
            metadata = doc["metadata"]
            assert "doc_type" in metadata, "Missing doc_type in metadata"
            if metadata["doc_type"] == "author":
                assert "author" in metadata, "Missing author in metadata"
                assert metadata["author"] == author_name, "Author name mismatch"

        return documents

    def test_load_to_chromadb(self, limited_test_data, chroma_db_manager):
        """Test loading documents into ChromaDB."""
        # First process the data
        processed_data = process_scholar_data(limited_test_data)

        # Get an author
        author_name = list(processed_data.keys())[0]
        author_data = processed_data[author_name]

        # Prepare documents for ChromaDB
        documents = prepare_documents_for_chromadb(author_name, author_data)

        # Skip if no documents
        if not documents:
            pytest.skip("No documents to load into ChromaDB")

        # Load documents into ChromaDB
        load_to_chromadb(documents, chroma_db_manager)

        # Verify documents were added by querying
        query_results = chroma_db_manager.query("test", n_results=5)

        # Check query results
        assert isinstance(query_results, list), "Query results should be a list"
        assert len(query_results) > 0, "Query should return at least one result"

        # Verify stats
        stats = chroma_db_manager.get_collection_stats()
        assert stats["document_count"] > 0, "Collection should have documents"

        return query_results

    def test_full_pipeline(self, limited_test_data, temp_output_dir, chroma_db_manager):
        """
        Test the entire pipeline from processing to ChromaDB storage.
        This test simulates the real-world usage of the Google Scholar pipeline.
        """
        # Step 1: Process raw data
        processed_data = process_scholar_data(limited_test_data)
        assert len(processed_data) > 0, "Should have processed at least one author"

        # Step 2: Save processed data
        processed_file = temp_output_dir / "processed_data.json"
        save_to_json(processed_data, processed_file)
        assert processed_file.exists(), "Processed data file should exist"

        # Step 3: Prepare data for ChromaDB
        chroma_data = prepare_chroma_data(processed_data, query="expert finder test")
        assert "authors" in chroma_data, "ChromaDB data should have authors"
        assert "articles" in chroma_data, "ChromaDB data should have articles"

        # Step 4: Save ChromaDB-ready data
        chroma_file = temp_output_dir / "chroma_data.json"
        save_to_json(chroma_data, chroma_file)
        assert chroma_file.exists(), "ChromaDB data file should exist"

        # Step 5: Prepare documents for each author
        all_documents = []
        for author_name, author_data in processed_data.items():
            documents = prepare_documents_for_chromadb(author_name, author_data)
            all_documents.extend(documents)

        # Step 6: Load documents into ChromaDB
        if all_documents:
            load_to_chromadb(all_documents, chroma_db_manager)

            # Step 7: Query ChromaDB
            query_results = chroma_db_manager.query("expert", n_results=5)
            assert len(query_results) > 0, "Query should return results"

            # Check stats
            stats = chroma_db_manager.get_collection_stats()
            assert stats["document_count"] > 0, "Collection should have documents"

            print(f"\nPipeline test successful! Loaded {stats['document_count']} documents into ChromaDB")
            print(f"First query result: {query_results[0]['metadata'].get('author', 'N/A')}")
        else:
            print("No documents were generated for ChromaDB")
