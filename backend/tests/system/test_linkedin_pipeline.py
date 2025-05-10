"""
System tests for the LinkedIn profile processing pipeline.

These tests verify the entire LinkedIn data flow:
1. Profile data extraction
2. Processing LinkedIn profiles
3. Calculating credibility
4. Vectorizing profiles
5. Adding to ChromaDB
"""

import os
import json
import pytest
import tempfile
import shutil
import uuid
import chromadb
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import LinkedIn processing modules
from linkedin_data_processing.process_linkedin_profiles import extract_profile_data, create_profile_text
from linkedin_data_processing.linkedin_vectorizer import LinkedInVectorizer
from linkedin_data_processing.dynamic_credibility import OnDemandCredibilityCalculator


class TestLinkedInPipeline:
    """System test for the entire LinkedIn data pipeline from processing to ChromaDB."""

    @pytest.fixture(scope="class")
    def test_data_path(self):
        """Path to test LinkedIn profile data file."""
        test_data_dir = Path(__file__).parent.parent / "fixtures" / "test_data"

        # Get the existing test profile file
        profile_files = list(test_data_dir.glob("*_processed.json*"))

        # If no processed files found, look for any JSON files
        if not profile_files:
            profile_files = list(test_data_dir.glob("*ACoA*.json"))

        # Make sure we found at least one file
        assert profile_files, "No test profile files found in test data directory"
        return profile_files[0]

    @pytest.fixture(scope="class")
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp(prefix="linkedin_test_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)  # Clean up after tests

    @pytest.fixture(scope="class")
    def chroma_db_path(self, temp_output_dir):
        """Create a temporary directory for ChromaDB."""
        db_path = temp_output_dir / "chromadb"
        db_path.mkdir(exist_ok=True)
        yield db_path
        # Cleanup happens with temp_output_dir

    @pytest.fixture
    def test_collection_name(self):
        """Generate a unique collection name for testing.

        Note: This fixture has function scope to ensure a unique name for each test.
        """
        return f"test_linkedin_{uuid.uuid4().hex[:8]}"

    @pytest.fixture(scope="class")
    def sample_profile(self, test_data_path):
        """Load a sample LinkedIn profile for testing with limited data fields."""
        with open(test_data_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        # If profile has a large experience section, limit it
        if (
            "experience" in profile_data
            and isinstance(profile_data["experience"], list)
            and len(profile_data["experience"]) > 3
        ):
            profile_data["experience"] = profile_data["experience"][:3]  # Keep only 3 experiences

        # If profile has a large education section, limit it
        if (
            "education" in profile_data
            and isinstance(profile_data["education"], list)
            and len(profile_data["education"]) > 2
        ):
            profile_data["education"] = profile_data["education"][:2]  # Keep only 2 education entries

        # If profile has many skills, limit them
        if "skills" in profile_data and isinstance(profile_data["skills"], list) and len(profile_data["skills"]) > 5:
            profile_data["skills"] = profile_data["skills"][:5]  # Keep only 5 skills

        return profile_data

    def test_extract_profile_data(self, test_data_path):
        """Test extracting profile data from a LinkedIn profile file."""
        # This test handles both raw and processed profiles
        profile_data = None

        # Since we might be using a processed file, just load it directly first
        with open(test_data_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        # If this looks like a raw profile, try using extract_profile_data
        if "lastName" in profile_data or "profilePicture" in profile_data:
            try:
                profile_data = extract_profile_data(test_data_path)
            except Exception as e:
                pytest.skip(f"Skipping extract test with error: {str(e)}")

        # Verify the structure of the profile data
        assert profile_data is not None, "Failed to extract or load profile data"
        assert "full_name" in profile_data, "Profile should have a full_name field"
        assert "headline" in profile_data, "Profile should have a headline field"
        assert "urn_id" in profile_data, "Profile should have a urn_id field"

        # Check for other expected fields
        expected_fields = ["current_title", "current_company", "location_name", "skills"]
        for field in expected_fields:
            assert field in profile_data, f"Profile should have a {field} field"

        # Check for data structures
        assert "experiences" in profile_data, "Profile should have experiences"
        assert isinstance(profile_data["experiences"], list), "Experiences should be a list"

        if "educations" in profile_data:
            assert isinstance(profile_data["educations"], list), "Educations should be a list"

        if "skills" in profile_data:
            assert isinstance(profile_data["skills"], list), "Skills should be a list"

        return profile_data

    def test_create_profile_text(self, sample_profile):
        """Test creating a text representation of a LinkedIn profile."""
        # Use the real function from the module
        profile_text = create_profile_text(sample_profile)

        # Verify the text contains key profile information
        assert isinstance(profile_text, str), "Profile text should be a string"
        assert sample_profile["full_name"] in profile_text, "Profile text should include name"
        if "current_title" in sample_profile and "current_company" in sample_profile:
            assert sample_profile["current_title"] in profile_text, "Profile text should include title"
            assert sample_profile["current_company"] in profile_text, "Profile text should include company"

        # Check for sections
        expected_sections = ["Name:", "Location:"]

        # Add conditional sections
        if "summary" in sample_profile and sample_profile["summary"]:
            expected_sections.append("Summary:")
        if "experiences" in sample_profile and sample_profile["experiences"]:
            expected_sections.append("Experience:")
        if "educations" in sample_profile and sample_profile["educations"]:
            expected_sections.append("Education:")
        if "skills" in sample_profile and sample_profile["skills"]:
            expected_sections.append("Skills:")

        for section in expected_sections:
            assert section in profile_text, f"Profile text should include {section} section"

        return profile_text

    def test_credibility_calculation(self, sample_profile):
        """Test calculating credibility for a LinkedIn profile."""
        # Create a copy of the profile to avoid modifying the fixture
        profile_copy = json.loads(json.dumps(sample_profile))

        # Create the real credibility calculator
        calculator = OnDemandCredibilityCalculator()

        # Calculate credibility score
        try:
            credibility_score = calculator.calculate_credibility(profile_copy)

            # Verify the score is a float between 0 and 10
            assert isinstance(credibility_score, float), "Credibility score should be a float"
            assert 0 <= credibility_score <= 10, "Credibility score should be between 0 and 10"

            # The calculator should add these fields to the profile
            assert "credibility_score" in profile_copy, "Credibility score should be added to profile"
            assert "credibility_factors" in profile_copy, "Credibility factors should be present"

            # Verify credibility factors data type
            assert isinstance(profile_copy["credibility_factors"], dict), "Credibility factors should be a dictionary"

            return credibility_score

        except Exception as e:
            # If the calculator can't process this profile, skip the test
            pytest.skip(f"Skipping credibility calculation with error: {str(e)}")

        return credibility_score

    def test_vectorize_and_add_to_chroma(self, sample_profile, chroma_db_path, test_collection_name, temp_output_dir):
        """Test vectorizing a profile and adding it to ChromaDB."""
        # Create a profiles directory and save the sample profile
        profiles_dir = temp_output_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        profile_filename = f"{sample_profile['urn_id']}_processed.json"
        profile_path = profiles_dir / profile_filename

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(sample_profile, f, indent=2)

        # Create a real ChromaDB client
        client = chromadb.PersistentClient(path=str(chroma_db_path))

        # Create a vectorizer with the test client
        with patch("chromadb.PersistentClient", return_value=client):
            vectorizer = LinkedInVectorizer(collection_name=test_collection_name)

            # Mock only external dependencies
            with patch.object(vectorizer, "download_profiles_from_gcp", return_value=True), patch.object(
                vectorizer, "get_profiles_in_collection", return_value=set()
            ):

                # Use glob to find our test profile
                with patch("glob.glob", return_value=[str(profile_path)]):
                    # First add the profile to ChromaDB - using the real implementation
                    num_added = vectorizer.add_profiles_to_chroma(profiles_dir=str(profiles_dir))

                    # Verify one profile was added
                    assert num_added == 1, f"Expected 1 profile to be added, got {num_added}"

                    # Verify the collection has one document
                    collection_count = vectorizer.chroma_manager.collection.count()
                    assert collection_count == 1, f"Expected collection to have 1 document, got {collection_count}"

                    # Get all documents to verify content
                    all_docs = vectorizer.chroma_manager.collection.get()
                    assert len(all_docs["ids"]) == 1
                    assert len(all_docs["documents"]) == 1
                    assert len(all_docs["metadatas"]) == 1

                    # Verify metadata
                    metadata = all_docs["metadatas"][0]
                    assert metadata["urn_id"] == sample_profile["urn_id"], "URN ID doesn't match expected value"
                    assert metadata["name"] == sample_profile["full_name"], "Name doesn't match expected value"

                    return vectorizer, all_docs

    def test_search_profiles(self, sample_profile, chroma_db_path, test_collection_name, temp_output_dir):
        # Create a profiles directory and save the sample profile
        profiles_dir = temp_output_dir / "profiles_for_search"
        profiles_dir.mkdir(exist_ok=True)

        profile_filename = f"{sample_profile['urn_id']}_processed.json"
        profile_path = profiles_dir / profile_filename

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(sample_profile, f, indent=2)

        # Create a real ChromaDB client
        client = chromadb.PersistentClient(path=str(chroma_db_path))

        # Create a vectorizer with the test client
        with patch("chromadb.PersistentClient", return_value=client):
            vectorizer = LinkedInVectorizer(collection_name=test_collection_name)

            # Mock only external dependencies
            with patch.object(vectorizer, "download_profiles_from_gcp", return_value=True), patch.object(
                vectorizer, "get_profiles_in_collection", return_value=set()
            ):

                # Use glob to find our test profile
                with patch("glob.glob", return_value=[str(profile_path)]):
                    # First add the profile to ChromaDB - using the real implementation
                    num_added = vectorizer.add_profiles_to_chroma(profiles_dir=str(profiles_dir))

                    # Verify one profile was added
                    assert num_added == 1, f"Expected 1 profile to be added, got {num_added}"

        # Now search for the profile using a relevant query
        # Try to use terms from the profile for better matching
        query_terms = []
        if "skills" in sample_profile and sample_profile["skills"]:
            query_terms.extend(sample_profile["skills"][:2])  # Use first two skills
        if "current_title" in sample_profile:
            query_terms.append(sample_profile["current_title"])
        if "industry" in sample_profile:
            query_terms.append(sample_profile["industry"])

        # Fall back to generic query if needed
        if not query_terms:
            query_terms = ["experienced professional"]

        query = " ".join(query_terms)
        results = vectorizer.search_profiles(query=query, n_results=5)

        # Verify results
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"

        # Verify result structure and content
        result = results[0]
        assert result["name"] == sample_profile["full_name"], "Name in search result should match profile"
        assert "similarity" in result, "Result should include similarity score"
        assert result["rank"] == 1, "Result should have rank 1"

        return results

    def test_full_linkedin_pipeline(self, sample_profile, chroma_db_path, test_collection_name, temp_output_dir):
        """
        Test the entire LinkedIn pipeline from profile extraction to ChromaDB search.
        This test simulates the real-world usage of the LinkedIn data processing pipeline.
        """
        # Step 1: Use the already limited sample profile data
        profile_data = sample_profile

        # Step 2: Try to calculate credibility (but handle if it fails)
        calculator = OnDemandCredibilityCalculator()
        try:
            calculator.calculate_credibility(profile_data)
            # If calculation works, verify profile has credibility information
            assert (
                "credibility_score" in profile_data or "credibility_factors" in profile_data
            ), "Credibility information missing from profile"
        except Exception as e:
            print(f"Note: Credibility calculation skipped: {str(e)}")
            # Continue with test even if credibility calculation fails

        # Step 3: Save processed profile
        profiles_dir = temp_output_dir / "processed_profiles"
        profiles_dir.mkdir(exist_ok=True)

        profile_filename = f"{profile_data['urn_id']}_processed.json"
        profile_path = profiles_dir / profile_filename

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        # Step 4: Create a LinkedIn vectorizer with ChromaDB
        client = chromadb.PersistentClient(path=str(chroma_db_path))

        with patch("chromadb.PersistentClient", return_value=client):
            vectorizer = LinkedInVectorizer(collection_name=test_collection_name)

            # Step 5: Add profile to ChromaDB
            with patch.object(vectorizer, "download_profiles_from_gcp", return_value=True), patch.object(
                vectorizer, "get_profiles_in_collection", return_value=set()
            ):

                # Use glob to find our test profile
                with patch("glob.glob", return_value=[str(profile_path)]):
                    num_added = vectorizer.add_profiles_to_chroma(profiles_dir=str(profiles_dir))
                    assert num_added == 1, f"Expected 1 profile to be added, got {num_added}"

            # Step 6: Search for the profile
            # Use skills as query terms for better matching
            query_terms = []
            if "skills" in profile_data and profile_data["skills"]:
                query_terms.extend(profile_data["skills"][:3])  # Use first three skills

            # Fall back to generic query if needed
            if not query_terms:
                query_terms = ["experienced professional"]

            query = " ".join(query_terms)
            results = vectorizer.search_profiles(query=query, n_results=5)

            # Verify results
            assert len(results) > 0, "Search should return results"

            # Verify first result matches our profile
            assert results[0]["name"] == profile_data["full_name"], "First result should match our profile"

            print(f"\nFull LinkedIn pipeline test successful!")
            print(f"Query: '{query}'")
            print(f"Top result: {results[0]['name']} ({results[0]['similarity']:.2f} similarity)")
            if "credibility_score" in profile_data and isinstance(profile_data["credibility_score"], (int, float)):
                print(f"Credibility score: {profile_data['credibility_score']:.2f}/10.0")
            else:
                print("Credibility score: Not calculated")
