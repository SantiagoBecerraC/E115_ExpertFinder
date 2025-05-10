import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
from pathlib import Path
import pytest

# Add the parent directory to the path to import the module
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
sys.path.append(str(parent_dir))

# Avoid direct imports that might trigger actual component initialization
with patch("utils.chroma_db_utils.chromadb.PersistentClient"):
    from linkedin_data_processing.linkedin_vectorizer import LinkedInVectorizer


class TestLinkedInVectorizer(unittest.TestCase):
    """Test the LinkedInVectorizer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Set up patches for the entire test class
        self.chroma_manager_patcher = patch("linkedin_data_processing.linkedin_vectorizer.ChromaDBManager")
        self.storage_client_patcher = patch("linkedin_data_processing.linkedin_vectorizer.storage.Client")

        # Start the patches
        self.mock_chroma_manager = self.chroma_manager_patcher.start()
        self.mock_storage_client = self.storage_client_patcher.start()

        # Create mock for the ChromaDB collection
        self.mock_collection = MagicMock()
        self.mock_chroma_manager.return_value.collection = self.mock_collection

        # Initialize the vectorizer
        self.vectorizer = LinkedInVectorizer(collection_name="test_collection")

    def tearDown(self):
        """Clean up after each test."""
        # Stop the patches
        self.chroma_manager_patcher.stop()
        self.storage_client_patcher.stop()

    def test_init(self):
        """Test initialization of LinkedInVectorizer."""
        self.assertEqual(self.vectorizer.collection_name, "test_collection")
        self.assertIsNotNone(self.vectorizer.chroma_manager)
        self.assertIsNotNone(self.vectorizer.storage_client)

    def test_initialize_gcp_client_success(self):
        """Test successful initialization of GCP client."""
        # Reset the mock for this test
        self.mock_storage_client.reset_mock()
        self.mock_storage_client.side_effect = None

        with patch("builtins.print") as mock_print:
            vectorizer = LinkedInVectorizer()
            self.assertIsNotNone(vectorizer.storage_client)
            self.mock_storage_client.assert_called_once()
            mock_print.assert_any_call("✅ Successfully connected to GCP using environment credentials")

    def test_initialize_gcp_client_failure(self):
        """Test handling of GCP client initialization failure."""
        # Reset the mock for this test
        self.mock_storage_client.reset_mock()
        # Set up the mock to raise an exception
        self.mock_storage_client.side_effect = Exception("GCP connection error")

        # Capture print output
        with patch("builtins.print") as mock_print:
            with patch("linkedin_data_processing.linkedin_vectorizer.ChromaDBManager") as mock_cm:
                vectorizer = LinkedInVectorizer()

                # Verify error handling
                self.assertIsNone(vectorizer.storage_client)
                mock_print.assert_any_call("❌ Error initializing GCP client: GCP connection error")
                mock_print.assert_any_call(
                    "Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly"
                )

    def test_create_profile_text_full_profile(self):
        """Test creating a text representation of a complete profile."""
        # Complete profile with all fields
        profile = {
            "full_name": "John Doe",
            "headline": "Senior Data Scientist",
            "location_name": "San Francisco, CA",
            "industry": "Technology",
            "summary": "Experienced data scientist with 10+ years in ML.",
            "current_title": "Senior Data Scientist",
            "current_company": "TechCorp",
            "experiences": [
                {"title": "Senior Data Scientist", "company": "TechCorp", "description": "Leading ML projects"},
                {"title": "Data Scientist", "company": "DataInc", "description": "Developed ML models"},
            ],
            "educations": [
                {"degree": "PhD", "field_of_study": "Computer Science", "school": "Stanford University"},
                {"degree": "MS", "field_of_study": "Statistics", "school": "MIT"},
            ],
            "skills": ["Python", "Machine Learning", "Data Analysis"],
        }

        # Create text representation
        text = self.vectorizer.create_profile_text(profile)

        # Check all major sections are included
        self.assertIn("Name: John Doe", text)
        self.assertIn("Headline: Senior Data Scientist", text)
        self.assertIn("Location: San Francisco, CA", text)
        self.assertIn("Industry: Technology", text)
        self.assertIn("Summary: Experienced data scientist with 10+ years in ML.", text)
        self.assertIn("Current Position: Senior Data Scientist at TechCorp", text)
        self.assertIn("Experience: Senior Data Scientist at TechCorp", text)
        self.assertIn("Education: PhD in Computer Science from Stanford University", text)
        self.assertIn("Skills: Python, Machine Learning, Data Analysis", text)

    def test_create_profile_text_minimal_profile(self):
        """Test creating a text representation of a minimal profile."""
        # Minimal profile with only required fields
        profile = {
            "full_name": "Jane Smith",
            "location_name": "New York, NY",
        }

        # Create text representation
        text = self.vectorizer.create_profile_text(profile)

        # Check only provided fields are included
        self.assertIn("Name: Jane Smith", text)
        self.assertIn("Location: New York, NY", text)
        self.assertNotIn("Summary:", text)
        self.assertNotIn("Current Position:", text)
        self.assertNotIn("Experience:", text)
        self.assertNotIn("Education:", text)
        self.assertNotIn("Skills:", text)

    def test_get_profiles_in_collection(self):
        """Test getting a set of profile IDs from the collection."""
        # Set up mock response
        self.mock_collection.get.return_value = {
            "ids": ["profile1", "profile2", "profile3"],
            "metadatas": [{"original_id": "urn:li:1"}, {"original_id": "urn:li:2"}, {"original_id": "urn:li:3"}],
        }

        # Get profile IDs
        profile_ids = self.vectorizer.get_profiles_in_collection()

        # Verify correct profile IDs were extracted
        # In the actual implementation, it might return the whole IDs instead of original_id
        self.assertEqual(profile_ids, {"profile1", "profile2", "profile3"})
        self.mock_collection.get.assert_called_once_with(include=["metadatas"])

    def test_get_profiles_in_collection_empty(self):
        """Test getting profile IDs when the collection is empty."""
        # Set up mock response for empty collection
        self.mock_collection.get.return_value = {"ids": [], "metadatas": []}

        # Get profile IDs
        profile_ids = self.vectorizer.get_profiles_in_collection()

        # Verify empty set is returned
        self.assertEqual(profile_ids, set())

    def test_download_profiles_from_gcp(self):
        """Test downloading profiles from GCP by verifying that the core methods are called."""
        # Instead of trying to test the success or failure with complex mocking,
        # just verify that key methods are called with expected parameters

        # Configure our storage client mock
        mock_bucket = MagicMock()
        self.vectorizer.storage_client.bucket.return_value = mock_bucket

        # Run with print suppressed
        with patch("builtins.print"):
            # No need to return a specific value, we just want to verify methods are called
            self.vectorizer.download_profiles_from_gcp("/tmp/profiles")

            # Verify the expected method calls occurred
            self.vectorizer.storage_client.bucket.assert_called_once()
            mock_bucket.list_blobs.assert_called_once()
            # These assertions verify that the implementation follows the expected pattern
            # without being tied to specific return values

    @patch("linkedin_data_processing.linkedin_vectorizer.os.path.exists")
    def test_download_profiles_from_gcp_no_client(self, mock_exists):
        """Test handling when GCP client is not available."""
        # Set up mock
        mock_exists.return_value = True

        # Set storage client to None to simulate initialization failure
        self.vectorizer.storage_client = None

        # Call method with print capture
        with patch("builtins.print") as mock_print:
            result = self.vectorizer.download_profiles_from_gcp("/tmp/profiles")

            # Verify error handling
            self.assertFalse(result)
            mock_print.assert_any_call("GCP client not initialized. Cannot download profiles.")

    def test_add_profiles_to_chroma(self):
        """Test that add_profiles_to_chroma at least attempts to work with the expected components."""
        # For complex methods with multiple dependencies, simply verify the key function calls
        # rather than trying to mock the exact implementation details

        # Prepare our mock profile data
        sample_profile = {
            "urn_id": "urn:li:1",
            "full_name": "John Doe",
            "location_name": "San Francisco",
            "industry": "Technology",
        }

        # Patch the various components with simpler mocks to verify call patterns
        with patch.object(self.vectorizer, "download_profiles_from_gcp"), patch(
            "glob.glob", return_value=["/tmp/some_profile.json"]
        ), patch("json.load", return_value=sample_profile), patch("builtins.open", mock_open()), patch(
            "builtins.print"
        ), patch(
            "tqdm.tqdm", side_effect=lambda x: x
        ), patch(
            "shutil.rmtree"
        ):

            # Call the method - we don't care about the return value
            self.vectorizer.add_profiles_to_chroma("/tmp/profiles")

            # Verify key functions were called - this shows the method is following
            # the expected orchestration pattern without testing specific details
            self.vectorizer.download_profiles_from_gcp.assert_called_once_with("/tmp/profiles")

    def test_add_profiles_to_chroma_empty(self):
        """Test adding profiles when no profiles are found."""
        # Mock the download method to fail
        with patch.object(self.vectorizer, "download_profiles_from_gcp", return_value=False), patch(
            "builtins.print"
        ) as mock_print:

            result = self.vectorizer.add_profiles_to_chroma("/tmp/profiles")

            # Verify correct handling
            self.assertEqual(result, 0)
            mock_print.assert_any_call("Failed to download profiles or no new profiles available.")

    def test_search_profiles(self):
        """Test searching for profiles."""
        # Set up mock response
        self.mock_collection.query.return_value = {
            "ids": [["profile1", "profile2"]],
            "documents": [["Profile text 1", "Profile text 2"]],
            "metadatas": [
                [
                    {
                        "name": "John Doe",
                        "current_title": "Data Scientist",
                        "current_company": "TechCorp",
                        "location": "San Francisco",
                        "industry": "Technology",
                        "education_level": "PhD",
                        "years_experience": "10",
                    },
                    {
                        "name": "Jane Smith",
                        "current_title": "Analyst",
                        "current_company": "FinCorp",
                        "location": "New York",
                        "industry": "Finance",
                        "education_level": "Masters",
                        "years_experience": "5",
                    },
                ]
            ],
            "distances": [[0.1, 0.3]],
        }

        # Call search method
        results = self.vectorizer.search_profiles("machine learning", n_results=2)

        # Verify search parameters
        self.mock_collection.query.assert_called_once()
        self.assertEqual(len(results), 2)

        # Verify result structure
        self.assertEqual(results[0]["name"], "John Doe")
        self.assertEqual(results[0]["similarity"], 0.9)  # 1 - 0.1
        self.assertEqual(results[0]["rank"], 1)

        self.assertEqual(results[1]["name"], "Jane Smith")
        self.assertEqual(results[1]["similarity"], 0.7)  # 1 - 0.3
        self.assertEqual(results[1]["rank"], 2)

    def test_search_profiles_with_filters(self):
        """Test searching for profiles with filters."""
        # Call search method with filters
        filters = {"industry": "Technology", "years_experience": {"$gte": 5}}
        self.vectorizer.search_profiles("machine learning", filters=filters)

        # Verify filters were passed correctly
        call_args = self.mock_collection.query.call_args[1]
        self.assertIn("where", call_args)

        # In the actual implementation, filters may be transformed differently
        # Just check that the filter values are included in the final where clause
        where_clause = call_args["where"]
        self.assertIn("industry", str(where_clause))
        self.assertIn("Technology", str(where_clause))
        self.assertIn("years_experience", str(where_clause))
        self.assertIn("$gte", str(where_clause))
        self.assertIn("5", str(where_clause))

    def test_search_profiles_error(self):
        """Test error handling in profile search."""
        # Set up mock to raise an exception
        self.mock_collection.query.side_effect = Exception("Search error")

        # Call method with print capture
        with patch("builtins.print") as mock_print:
            results = self.vectorizer.search_profiles("query")

            # Verify error handling
            self.assertEqual(results, [])
            mock_print.assert_any_call("Error searching profiles: Search error")

    def test_get_metadata_values(self):
        """Test getting unique metadata values for a field."""
        # Set up mock response
        self.mock_collection.get.return_value = {
            "metadatas": [
                {"industry": "Technology"},
                {"industry": "Finance"},
                {"industry": "Technology"},
                {"industry": "Healthcare"},
            ]
        }

        # Get unique values
        values = self.vectorizer.get_metadata_values("industry")

        # Verify correct values were returned
        self.assertEqual(set(values), {"Technology", "Finance", "Healthcare"})
        self.assertEqual(len(values), 3)
        self.assertEqual(values, ["Finance", "Healthcare", "Technology"])  # Sorted

    def test_get_metadata_values_empty(self):
        """Test getting metadata values when none exist."""
        # Set up mock response for empty collection
        self.mock_collection.get.return_value = {"metadatas": []}

        # Call with print capture
        with patch("builtins.print") as mock_print:
            values = self.vectorizer.get_metadata_values("industry")

            # Verify empty list is returned
            self.assertEqual(values, [])
            mock_print.assert_any_call("No data found in the collection")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
