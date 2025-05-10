# backend/tests/integration/data/test_process_linkedin_profiles_integration.py
import pytest
import json
import os
import shutil
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from linkedin_data_processing.process_linkedin_profiles import (
    initialize_gcp_client,
    get_processed_file_list,
    extract_profile_data,
    download_unprocessed_profiles_from_gcp,
    download_profiles_from_gcp,
    process_profiles_and_upload_to_gcp,
    get_credibility_distribution,
    download_new_processed_profiles_for_rag,
    get_profiles_in_chroma,
    prepare_profiles_for_rag,
    create_profile_text,
    setup_chroma_db,
    search_profiles_demo
)

# For testing the GCP initialization function (lines 16-18)
@pytest.mark.integration
def test_initialize_gcp_client():
    """Test GCP client initialization with mocked responses."""
    # Test successful initialization
    with patch('linkedin_data_processing.process_linkedin_profiles.storage.Client') as mock_client:
        # Setup the mock to return successfully
        mock_storage_client = MagicMock()
        mock_client.return_value = mock_storage_client
        
        client = initialize_gcp_client()
        assert client is not None
        assert client == mock_storage_client
        
    # Test failed initialization
    with patch('linkedin_data_processing.process_linkedin_profiles.storage.Client', 
               side_effect=Exception("GCP client error")):
        client = initialize_gcp_client()
        assert client is None


@pytest.fixture
def mock_gcp_storage_client():
    """Create a mock GCP storage client."""
    client = MagicMock()
    
    # Mock bucket
    bucket = MagicMock()
    client.bucket.return_value = bucket
    
    # Mock blob list
    mock_blobs = []
    for i in range(5):
        blob = MagicMock()
        blob.name = f"linkedin_data_processing/processed_profiles/urn_id_{i}_processed.json"
        mock_blobs.append(blob)
    
    # Setup blob.list_blobs to return our mock blobs
    bucket.list_blobs.return_value = mock_blobs
    
    return client


@pytest.mark.integration
def test_get_processed_file_list(mock_gcp_storage_client):
    """Test getting the list of processed URN IDs from GCP."""
    # Test normal case
    processed_urns = get_processed_file_list(mock_gcp_storage_client)
    assert len(processed_urns) == 5
    assert "urn_id_0" in processed_urns
    assert "urn_id_4" in processed_urns
    
    # Test with empty blob list
    mock_gcp_storage_client.bucket().list_blobs.return_value = []
    processed_urns = get_processed_file_list(mock_gcp_storage_client)
    assert len(processed_urns) == 0
    
    # Test with error
    mock_gcp_storage_client.bucket.side_effect = Exception("Bucket error")
    processed_urns = get_processed_file_list(mock_gcp_storage_client)
    assert len(processed_urns) == 0


@pytest.fixture
def sample_profile_json():
    """Create a sample LinkedIn profile JSON for testing."""
    return {
        "urn_id": "test_urn_id",
        "fetch_timestamp": "2023-05-01T12:00:00",
        "profile_data": {
            "firstName": "John",
            "lastName": "Doe",
            "headline": "Software Engineer",
            "summary": "Experienced software engineer with expertise in Python and machine learning.",
            "public_id": "johndoe",
            "member_urn": "urn:li:member:123456789",
            "locationName": "San Francisco, California",
            "geoLocationName": "San Francisco Bay Area",
            "geoCountryName": "United States",
            "location": {
                "basicLocation": {
                    "countryCode": "us"
                }
            },
            "geoCountryUrn": "urn:li:geo:103644278",
            "industryName": "Computer Software",
            "industryUrn": "urn:li:industry:4",
            "student": False,
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "companyName": "Tech Company",
                    "companyUrn": "urn:li:company:123456",
                    "locationName": "San Francisco Bay Area",
                    "timePeriod": {
                        "startDate": {
                            "month": 1,
                            "year": 2020
                        }
                    },
                    "description": "Leading the machine learning team.",
                    "company": {
                        "employeeCountRange": {
                            "start": 1001
                        },
                        "industries": ["Software", "AI"]
                    }
                },
                {
                    "title": "Software Engineer",
                    "companyName": "Previous Company",
                    "companyUrn": "urn:li:company:654321",
                    "locationName": "Seattle, Washington",
                    "timePeriod": {
                        "startDate": {
                            "month": 6,
                            "year": 2018
                        },
                        "endDate": {
                            "month": 12,
                            "year": 2019
                        }
                    },
                    "description": "Developed web applications.",
                    "company": {
                        "employeeCountRange": {
                            "start": 501
                        },
                        "industries": ["Software"]
                    }
                }
            ],
            "education": [
                {
                    "schoolName": "Stanford University",
                    "degreeName": "Master of Science",
                    "fieldOfStudy": "Computer Science",
                    "timePeriod": {
                        "startDate": {
                            "year": 2016
                        },
                        "endDate": {
                            "year": 2018
                        }
                    }
                },
                {
                    "schoolName": "University of California, Berkeley",
                    "degreeName": "Bachelor of Science",
                    "fieldOfStudy": "Computer Science",
                    "timePeriod": {
                        "startDate": {
                            "year": 2012
                        },
                        "endDate": {
                            "year": 2016
                        }
                    }
                }
            ],
            "skills": [
                {"name": "Python"},
                {"name": "Machine Learning"},
                {"name": "TensorFlow"},
                {"name": "SQL"},
                {"name": "JavaScript"}
            ],
            "languages": [
                {"name": "English", "proficiency": "Native"},
                {"name": "Spanish", "proficiency": "Professional"}
            ],
            "publications": [
                {
                    "name": "Machine Learning Advances",
                    "publisher": "AI Journal",
                    "description": "Latest advancements in ML algorithms",
                    "url": "https://example.com/publication1",
                    "date": {"year": 2022, "month": 3}
                }
            ],
            "certifications": [
                {
                    "name": "AWS Certified Developer",
                    "authority": "Amazon Web Services",
                    "licenseNumber": "AWS12345",
                    "url": "https://example.com/cert1",
                    "timePeriod": {
                        "startDate": {"year": 2021, "month": 5}
                    }
                }
            ],
            "projects": [
                {
                    "title": "ML Framework",
                    "description": "Developed a new machine learning framework",
                    "url": "https://example.com/project1",
                    "timePeriod": {
                        "startDate": {"year": 2021, "month": 1},
                        "endDate": {"year": 2021, "month": 6}
                    }
                }
            ],
            "volunteer": [
                {
                    "companyName": "Code for America",
                    "role": "Volunteer Developer",
                    "description": "Developed applications for civic purposes",
                    "timePeriod": {
                        "startDate": {"year": 2019, "month": 1},
                        "endDate": {"year": 2020, "month": 12}
                    }
                }
            ],
            "honors": [
                {
                    "title": "Outstanding Engineer Award",
                    "issuer": "Tech Company",
                    "description": "Awarded for excellence in engineering",
                    "date": {"year": 2021, "month": 12}
                }
            ]
        }
    }


@pytest.fixture
def sample_profile_file(sample_profile_json, tmp_path):
    """Create a temporary profile file for testing."""
    profile_path = tmp_path / "test_profile.json"
    with open(profile_path, 'w') as f:
        json.dump(sample_profile_json, f)
    return str(profile_path)


@pytest.mark.integration
def test_extract_profile_data(sample_profile_file):
    """Test extracting profile data from a JSON file."""
    # Test with valid profile
    profile_data = extract_profile_data(sample_profile_file)
    
    assert profile_data is not None
    assert profile_data["urn_id"] == "test_urn_id"
    assert profile_data["full_name"] == "John Doe"
    assert profile_data["current_title"] == "Senior Software Engineer"
    assert profile_data["current_company"] == "Tech Company"
    assert profile_data["education_level"] == "Masters"
    assert profile_data["career_level"] == "Senior"
    assert profile_data["total_years_experience"] > 0
    assert len(profile_data["skills"]) == 5
    assert len(profile_data["experiences"]) == 2
    assert len(profile_data["educations"]) == 2
    
    # Test with invalid file
    invalid_file = "non_existent_file.json"
    profile_data = extract_profile_data(invalid_file)
    assert profile_data is None


@pytest.mark.integration
def test_download_profiles_from_gcp(mock_gcp_storage_client, tmp_path):
    """Test downloading profiles from GCP."""
    # Setup mock blob download
    def side_effect_download(path):
        # Create an empty file at the specified path
        with open(path, 'w') as f:
            f.write("{}")
    
    for blob in mock_gcp_storage_client.bucket().list_blobs():
        blob.download_to_filename.side_effect = side_effect_download
    
    # Test normal case
    temp_dir = str(tmp_path / "profiles")
    result = download_profiles_from_gcp(mock_gcp_storage_client, temp_dir)
    assert result == temp_dir
    
    # Test with error
    mock_gcp_storage_client.bucket.side_effect = Exception("Bucket error")
    result = download_profiles_from_gcp(mock_gcp_storage_client, temp_dir)
    assert result is None


@pytest.mark.integration
def test_download_unprocessed_profiles_from_gcp(mock_gcp_storage_client, tmp_path):
    """Test downloading only unprocessed profiles from GCP."""
    # Setup mock for get_processed_file_list to return specific URNs
    with patch('linkedin_data_processing.process_linkedin_profiles.get_processed_file_list') as mock_get_list:
        mock_get_list.return_value = {"urn_id_0", "urn_id_1"}  # These are already processed
        
        # Setup mock blob objects
        mock_blobs = []
        for i in range(5):
            blob = MagicMock()
            blob.name = f"linkedin_raw_data/data/profiles/urn_id_{i}.json"
            mock_blobs.append(blob)
        
        mock_gcp_storage_client.bucket().list_blobs.return_value = mock_blobs
        
        # Setup mock download
        def side_effect_download(path):
            with open(path, 'w') as f:
                f.write("{}")
        
        for blob in mock_blobs:
            blob.download_to_filename.side_effect = side_effect_download
        
        # Test downloading unprocessed profiles
        temp_dir = str(tmp_path / "profiles")
        result = download_unprocessed_profiles_from_gcp(mock_gcp_storage_client, temp_dir)
        assert result == temp_dir
        
        # Test with all profiles already processed
        mock_get_list.return_value = {f"urn_id_{i}" for i in range(5)}  # All are processed
        result = download_unprocessed_profiles_from_gcp(mock_gcp_storage_client, temp_dir)
        assert result is None
        
        # Test with error
        mock_get_list.side_effect = Exception("Error getting processed list")
        result = download_unprocessed_profiles_from_gcp(mock_gcp_storage_client, temp_dir)
        assert result is None


@pytest.fixture
def sample_profiles_dir(sample_profile_json, tmp_path):
    """Create a directory with sample profile files."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    
    # Create multiple profile files
    for i in range(3):
        profile = sample_profile_json.copy()
        profile["urn_id"] = f"urn_id_{i}"
        profile["profile_data"]["firstName"] = f"User{i}"
        
        with open(profiles_dir / f"urn_id_{i}.json", 'w') as f:
            json.dump(profile, f)
    
    return str(profiles_dir)


@pytest.mark.integration
def test_process_profiles_and_upload_to_gcp(sample_profiles_dir, mock_gcp_storage_client):
    """Test processing profiles and uploading to GCP."""
    with patch('linkedin_data_processing.process_linkedin_profiles.initialize_gcp_client', return_value=mock_gcp_storage_client):
        # Test successful processing
        result = process_profiles_and_upload_to_gcp(sample_profiles_dir)
        assert result is True
        
        # Verify blob upload was called for each profile
        bucket = mock_gcp_storage_client.bucket.return_value
        assert bucket.blob.call_count >= 3
        
        # For catastrophic failure, we need to patch at a higher level
        # The function seems to handle extraction errors gracefully
        with patch('linkedin_data_processing.process_linkedin_profiles.glob.glob', 
                   side_effect=Exception("Critical globbing error")):
            result = process_profiles_and_upload_to_gcp(sample_profiles_dir)
            assert result is False


@pytest.mark.integration
def test_create_profile_text():
    """Test creating text representation of a profile."""
    # Create a simple profile
    profile = {
        "full_name": "Jane Smith",
        "headline": "Data Scientist",
        "location_name": "New York",
        "industry": "Technology",
        "summary": "Experienced data scientist with ML expertise",
        "current_title": "Senior Data Scientist",
        "current_company": "AI Corp",
        "experiences": [
            {
                "title": "Senior Data Scientist",
                "company": "AI Corp",
                "description": "Leading data science initiatives"
            },
            {
                "title": "Data Scientist",
                "company": "Tech Startup",
                "description": "Developed ML models"
            }
        ],
        "educations": [
            {
                "degree": "PhD",
                "field_of_study": "Computer Science",
                "school": "MIT"
            }
        ],
        "skills": ["Python", "Machine Learning", "TensorFlow"]
    }
    
    # Test text creation
    text = create_profile_text(profile)
    assert "Jane Smith" in text
    assert "Data Scientist" in text
    assert "New York" in text
    assert "Technology" in text
    assert "Experienced data scientist" in text
    assert "AI Corp" in text
    assert "Tech Startup" in text
    assert "PhD in Computer Science from MIT" in text
    assert "Python, Machine Learning, TensorFlow" in text


@pytest.mark.integration
def test_setup_chroma_db(tmp_path):
    """Test setting up ChromaDB client and collection."""
    with patch('linkedin_data_processing.process_linkedin_profiles.chromadb.PersistentClient') as mock_client:
        # Setup mock client and collection
        mock_chroma_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        
        # Test getting existing collection
        mock_chroma_client.get_collection.return_value = mock_collection
        mock_client.return_value = mock_chroma_client
        
        chroma_dir = str(tmp_path / "chroma_test")
        client, collection = setup_chroma_db(chroma_dir)
        
        assert client == mock_chroma_client
        assert collection == mock_collection
        mock_chroma_client.get_collection.assert_called_once_with(name="linkedin_profiles")
        
        # Test creating new collection
        mock_chroma_client.get_collection.side_effect = Exception("Collection not found")
        mock_chroma_client.create_collection.return_value = mock_collection
        
        client, collection = setup_chroma_db(chroma_dir)
        
        assert client == mock_chroma_client
        assert collection == mock_collection
        mock_chroma_client.create_collection.assert_called_once()


@pytest.mark.integration
def test_get_profiles_in_chroma():
    """Test getting profiles from ChromaDB."""
    with patch('linkedin_data_processing.process_linkedin_profiles.setup_chroma_db') as mock_setup:
        # Setup mock collection
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            'ids': ['urn_id_0', 'urn_id_1', 'urn_id_2'],
            'metadatas': [{'name': 'User0'}, {'name': 'User1'}, {'name': 'User2'}]
        }
        mock_setup.return_value = (None, mock_collection)
        
        # Test getting profiles
        profiles = get_profiles_in_chroma()
        assert len(profiles) == 3
        assert 'urn_id_0' in profiles
        assert 'urn_id_2' in profiles
        
        # Test with empty result
        mock_collection.get.return_value = {'ids': []}
        profiles = get_profiles_in_chroma()
        assert len(profiles) == 0
        
        # Test with error
        mock_collection.get.side_effect = Exception("ChromaDB error")
        profiles = get_profiles_in_chroma()
        assert len(profiles) == 0


@pytest.mark.integration
def test_download_new_processed_profiles_for_rag(mock_gcp_storage_client, tmp_path):
    """Test downloading new processed profiles for RAG."""
    # Setup mock blobs
    mock_blobs = []
    for i in range(5):
        blob = MagicMock()
        blob.name = f"linkedin_data_processing/processed_profiles/urn_id_{i}_processed.json"
        mock_blobs.append(blob)
    
    mock_gcp_storage_client.bucket().list_blobs.return_value = mock_blobs
    
    # Setup mock download
    def side_effect_download(path):
        with open(path, 'w') as f:
            f.write("{}")
    
    for blob in mock_blobs:
        blob.download_to_filename.side_effect = side_effect_download
    
    # Test with some existing profiles
    existing_profiles = {'urn_id_0', 'urn_id_1'}  # These are already in ChromaDB
    temp_dir = str(tmp_path / "processed_profiles")
    
    result = download_new_processed_profiles_for_rag(mock_gcp_storage_client, existing_profiles, temp_dir)
    assert result == temp_dir
    
    # Test with all profiles already in ChromaDB
    existing_profiles = {f'urn_id_{i}' for i in range(5)}
    result = download_new_processed_profiles_for_rag(mock_gcp_storage_client, existing_profiles, temp_dir)
    assert result is None
    
    # Test with error
    mock_gcp_storage_client.bucket.side_effect = Exception("Bucket error")
    result = download_new_processed_profiles_for_rag(mock_gcp_storage_client, set(), temp_dir)
    assert result is None


@pytest.mark.integration
def test_prepare_profiles_for_rag():
    """Test preparing profiles for RAG."""
    with patch('linkedin_data_processing.process_linkedin_profiles.initialize_gcp_client') as mock_init, \
         patch('linkedin_data_processing.process_linkedin_profiles.get_profiles_in_chroma') as mock_get_profiles, \
         patch('linkedin_data_processing.process_linkedin_profiles.download_new_processed_profiles_for_rag') as mock_download, \
         patch('linkedin_data_processing.process_linkedin_profiles.SentenceTransformer') as mock_transformer, \
         patch('linkedin_data_processing.process_linkedin_profiles.setup_chroma_db') as mock_setup, \
         patch('linkedin_data_processing.process_linkedin_profiles.shutil.rmtree') as mock_rmtree, \
         patch('linkedin_data_processing.process_linkedin_profiles.glob.glob') as mock_glob, \
         patch('linkedin_data_processing.process_linkedin_profiles.create_profile_text') as mock_create_text, \
         patch('linkedin_data_processing.process_linkedin_profiles.os.makedirs') as mock_makedirs:
        
        # Setup mocks
        mock_gcp_client = MagicMock()
        mock_init.return_value = mock_gcp_client
        
        mock_get_profiles.return_value = {'urn_id_0', 'urn_id_1'}
        
        # Test with no new profiles
        mock_download.return_value = None
        result = prepare_profiles_for_rag()
        assert result is True
        
        # Reset call count for next test
        mock_rmtree.reset_mock()
        
        # Test with new profiles
        mock_download.return_value = "/tmp/processed_profiles"
        
        mock_transformer_instance = MagicMock()
        mock_transformer_instance.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_transformer_instance
        
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10
        mock_setup.return_value = (None, mock_collection)
        
        # Setup mock file list
        mock_glob.return_value = ["/tmp/processed_profiles/urn_id_2_processed.json", 
                                 "/tmp/processed_profiles/urn_id_3_processed.json"]
        
        # Mock create_profile_text to return a string
        mock_create_text.return_value = "Profile text representation"
        
        # Properly mock file open and json.load
        mock_file_content = {
            "urn_id": "urn_id_2",
            "full_name": "Test User",
            "current_title": "Engineer",
            "current_company": "Test Co",
            "location_name": "San Francisco",
            "industry": "Technology",
            "education_level": "Masters",
            "career_level": "Senior",
            "total_years_experience": 5
        }
        
        # Use a proper mock for file operations
        mock_open = mock_open = MagicMock()
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        with patch('builtins.open', mock_open), \
             patch('json.load', return_value=mock_file_content):
            
            result = prepare_profiles_for_rag()
            assert result is True
            # Check that upsert was called at least once
            assert mock_collection.upsert.call_count > 0
            # Verify cleanup is called with the correct path
            mock_rmtree.assert_called_once_with("/tmp/processed_profiles")
        
        # Test with error
        mock_download.side_effect = Exception("Download error")
        result = prepare_profiles_for_rag()
        assert result is False


@pytest.mark.integration
def test_search_profiles_demo():
    """Test searching profiles with demo function."""
    with patch('linkedin_data_processing.process_linkedin_profiles.SentenceTransformer') as mock_transformer, \
         patch('linkedin_data_processing.process_linkedin_profiles.setup_chroma_db') as mock_setup:
        
        # Setup mock embedding
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_transformer_instance = MagicMock()
        mock_transformer_instance.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_transformer_instance
        
        # Setup mock ChromaDB response
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'ids': [['urn_id_0', 'urn_id_1', 'urn_id_2']],
            'documents': [['Profile text 0', 'Profile text 1', 'Profile text 2']],
            'metadatas': [[
                {
                    "name": "User 0",
                    "current_title": "Engineer",
                    "current_company": "Tech Co",
                    "location": "San Francisco",
                    "industry": "Software",
                    "education_level": "Masters",
                    "career_level": "Senior"
                },
                {
                    "name": "User 1",
                    "current_title": "Manager",
                    "current_company": "Big Corp",
                    "location": "New York",
                    "industry": "Finance",
                    "education_level": "Bachelors",
                    "career_level": "Manager"
                },
                {
                    "name": "User 2",
                    "current_title": "Researcher",
                    "current_company": "University",
                    "location": "Boston",
                    "industry": "Education",
                    "education_level": "PhD",
                    "career_level": "Senior"
                }
            ]],
            'distances': [[0.1, 0.2, 0.3]]
        }
        mock_setup.return_value = (None, mock_collection)
        
        # Test basic search
        results = search_profiles_demo("machine learning", top_k=3)
        assert len(results) == 3
        assert results[0]["name"] == "User 0"
        assert results[0]["similarity"] == 0.9  # 1 - distance
        
        # Test with filters
        results = search_profiles_demo("machine learning", filters={"industry": "Software"}, top_k=2)
        assert len(results) == 3  # Our mock returns 3 regardless of filters
        mock_collection.query.assert_called_with(
            query_embeddings=[mock_embedding.tolist()],
            n_results=2,
            where={"industry": "Software"}
        )
        
        # Test with empty results
        mock_collection.query.return_value = {'ids': [[]]}
        results = search_profiles_demo("no results query")
        assert len(results) == 0


@pytest.mark.integration
def test_get_credibility_distribution():
    """Test getting credibility distribution."""
    with patch('linkedin_data_processing.process_linkedin_profiles.OnDemandCredibilityCalculator') as mock_calc:
        # Setup mock calculator
        mock_calc_instance = MagicMock()
        mock_calc_instance.update_stats_if_needed.return_value = None
        
        # Have calculate_credibility return different levels for different profiles
        def side_effect_calc(profile):
            if profile.get('urn_id') == 'urn_id_0':
                return {'level': 5}
            elif profile.get('urn_id') == 'urn_id_1':
                return {'level': 4}
            elif profile.get('urn_id') == 'urn_id_2':
                return {'level': 3}
            elif profile.get('urn_id') == 'urn_id_3':
                return {'level': 2}
            else:
                return {'level': 1}
            
        mock_calc_instance.calculate_credibility.side_effect = side_effect_calc
        mock_calc.return_value = mock_calc_instance
        
        # Create test profiles
        profiles = [
            {'urn_id': 'urn_id_0'},
            {'urn_id': 'urn_id_1'},
            {'urn_id': 'urn_id_2'},
            {'urn_id': 'urn_id_3'},
            {'urn_id': 'urn_id_4'}
        ]
        
        # Test distribution calculation
        distribution = get_credibility_distribution(profiles)
        
        assert 1 in distribution
        assert 5 in distribution
        assert distribution[5]['count'] == 1
        assert distribution[4]['count'] == 1
        assert distribution[3]['count'] == 1
        assert distribution[2]['count'] == 1
        assert distribution[1]['count'] == 1
        assert distribution[5]['percentage'] == 20.0