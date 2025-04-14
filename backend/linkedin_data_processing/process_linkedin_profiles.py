import os
import json
import shutil
import pandas as pd
import glob
from google.cloud import storage
from tqdm import tqdm
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer
import argparse

try:
    # Try relative import first (when imported)
    from .credibility_system import DynamicCredibilityCalculator
except ImportError:
    # Fall back to absolute import (when run directly)
    from credibility_system import DynamicCredibilityCalculator

# Initialize the calculator as a global instance
credibility_calculator = DynamicCredibilityCalculator()

def initialize_gcp_client():
    """Initialize and return GCP storage client."""
    try:
        # Use environment variable for authentication
        storage_client = storage.Client()
        print("✅ Successfully connected to GCP using environment credentials")
        return storage_client
    except Exception as e:
        print(f"❌ Error initializing GCP client: {str(e)}")
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly")
        return None

def get_processed_file_list(storage_client, gcp_folder="linkedin_data_processing/processed_profiles"):
    """
    Get a list of already processed profile URN IDs from GCP.
    
    Args:
        storage_client: GCP storage client
        gcp_folder (str): GCP folder containing processed profiles
        
    Returns:
        set: Set of URN IDs that have already been processed
    """
    try:
        bucket_name = "expert-finder-bucket-1"
        bucket = storage_client.bucket(bucket_name)
        
        # List all processed profiles in GCP
        blobs = list(bucket.list_blobs(prefix=gcp_folder))
        processed_files = [blob.name for blob in blobs if blob.name.endswith('_processed.json')]
        
        # Extract URN IDs from filenames
        processed_urns = set()
        for filename in processed_files:
            # Extract URN ID from filename (format: path/to/URN_ID_processed.json)
            basename = os.path.basename(filename)
            urn_id = basename.replace('_processed.json', '')
            processed_urns.add(urn_id)
        
        print(f"Found {len(processed_urns)} already processed profiles in GCP")
        return processed_urns
    
    except Exception as e:
        print(f"Error getting processed file list: {str(e)}")
        return set()

def download_unprocessed_profiles_from_gcp(storage_client, local_dir="/tmp/profiles"):
    """Download only unprocessed profile files from GCP bucket to local directory."""
    bucket_name = "expert-finder-bucket-1"
    profiles_prefix = "linkedin_raw_data/data/profiles/"
    
    # Create local directory if it doesn't exist
    os.makedirs(local_dir, exist_ok=True)
    
    try:
        bucket = storage_client.bucket(bucket_name)
        
        # Get list of already processed URN IDs
        processed_urns = get_processed_file_list(storage_client)
        
        # List all profile files in GCP
        blobs = list(bucket.list_blobs(prefix=profiles_prefix))
        profile_blobs = [blob for blob in blobs if blob.name.endswith('.json') and not blob.name.endswith('errors.json')]
        
        print(f"Found {len(profile_blobs)} total profile files in GCP bucket")
        
        # Filter out already processed profiles
        unprocessed_blobs = []
        for blob in profile_blobs:
            # Extract URN ID from filename
            basename = os.path.basename(blob.name)
            urn_id = basename.replace('.json', '')
            
            if urn_id not in processed_urns:
                unprocessed_blobs.append(blob)
        
        print(f"Found {len(unprocessed_blobs)} unprocessed profiles to download")
        
        # Download unprocessed files with progress bar
        for blob in tqdm(unprocessed_blobs, desc="Downloading unprocessed profiles"):
            local_path = os.path.join(local_dir, os.path.basename(blob.name))
            blob.download_to_filename(local_path)
        
        print(f"Downloaded {len(unprocessed_blobs)} unprocessed profile files to {local_dir}")
        return local_dir if unprocessed_blobs else None
    except Exception as e:
        print(f"Error downloading profiles from GCP: {str(e)}")
        return None

def download_profiles_from_gcp(storage_client, local_dir="/tmp/profiles"):
    """Download profile files from GCP bucket to local directory."""
    bucket_name = "expert-finder-bucket-1"
    profiles_prefix = "linkedin_raw_data/data/profiles/"
    
    # Create local directory if it doesn't exist
    os.makedirs(local_dir, exist_ok=True)
    
    try:
        bucket = storage_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=profiles_prefix))
        
        print(f"Found {len(blobs)} profile files in GCP bucket")
        
        # Download files with progress bar
        for blob in tqdm(blobs, desc="Downloading profiles"):
            if blob.name.endswith('.json') and not blob.name.endswith('errors.json'):
                local_path = os.path.join(local_dir, os.path.basename(blob.name))
                blob.download_to_filename(local_path)
        
        print(f"Downloaded {len(blobs)} profile files to {local_dir}")
        return local_dir
    except Exception as e:
        print(f"Error downloading profiles from GCP: {str(e)}")
        return None

def extract_profile_data(file_path):
    """
    Extract relevant data from a LinkedIn profile JSON file.
    
    Args:
        file_path (str): Path to the profile JSON file
        
    Returns:
        dict: Extracted profle data in a structured format
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get the main profile data
        profile = data.get('profile_data', {})
        urn_id = data.get('urn_id')
        
        # Basic information
        extracted_data = {
            'urn_id': urn_id,
            'fetch_timestamp': data.get('fetch_timestamp'),
            'first_name': profile.get('firstName'),
            'last_name': profile.get('lastName'),
            'full_name': f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
            'headline': profile.get('headline', ''),
            'summary': profile.get('summary', ''),
            'public_id': profile.get('public_id', ''),
            'member_urn': profile.get('member_urn', ''),
        }
        
        # Location information
        extracted_data.update({
            'location_name': profile.get('locationName'),
            'geo_location_name': profile.get('geoLocationName'),
            'country': profile.get('geoCountryName'),
            'country_code': profile.get('location', {}).get('basicLocation', {}).get('countryCode'),
            'geo_country_urn': profile.get('geoCountryUrn'),
        })
        
        # Industry information
        extracted_data.update({
            'industry': profile.get('industryName'),
            'industry_urn': profile.get('industryUrn'),
        })
        
        # Profile flags
        extracted_data.update({
            'student': profile.get('student', False)
        })
        
        # Experience information
        experiences = profile.get('experience', [])
        if experiences:
            # Current experience (most recent)
            current_exp = experiences[0]
            extracted_data.update({
                'current_title': current_exp.get('title', ''),
                'current_company': current_exp.get('companyName', ''),
                'current_company_urn': current_exp.get('companyUrn', ''),
                'current_location': current_exp.get('locationName', ''),
                'current_start_month': current_exp.get('timePeriod', {}).get('startDate', {}).get('month'),
                'current_start_year': current_exp.get('timePeriod', {}).get('startDate', {}).get('year'),
            })
            
            # All experiences
            exp_list = []
            for exp in experiences:
                time_period = exp.get('timePeriod', {})
                start_date = time_period.get('startDate', {})
                end_date = time_period.get('endDate', {})
                
                exp_data = {
                    'title': exp.get('title', ''),
                    'company': exp.get('companyName', ''),
                    'company_urn': exp.get('companyUrn', ''),
                    'location': exp.get('locationName', ''),
                    'description': exp.get('description', ''),
                    'start_month': start_date.get('month'),
                    'start_year': start_date.get('year'),
                    'end_month': end_date.get('month') if end_date else None,
                    'end_year': end_date.get('year') if end_date else None,
                    'is_current': end_date is None,
                    'company_size': exp.get('company', {}).get('employeeCountRange', {}).get('start'),
                    'company_industries': exp.get('company', {}).get('industries', []),
                }
                exp_list.append(exp_data)
            
            extracted_data['experiences'] = exp_list
            extracted_data['experience_count'] = len(exp_list)
            
            # Calculate total years of experience
            total_years = 0
            for exp in exp_list:
                start_year = exp.get('start_year')
                end_year = exp.get('end_year') or datetime.now().year
                if start_year:
                    years = end_year - start_year
                    total_years += years
            
            extracted_data['total_years_experience'] = total_years
        
        # Education information
        educations = profile.get('education', [])
        if educations:
            # Latest education (most recent)
            latest_edu = educations[0]
            extracted_data.update({
                'latest_school': latest_edu.get('schoolName', ''),
                'latest_degree': latest_edu.get('degreeName', ''),
                'latest_field_of_study': latest_edu.get('fieldOfStudy', ''),
                'latest_edu_start_year': latest_edu.get('timePeriod', {}).get('startDate', {}).get('year'),
                'latest_edu_end_year': latest_edu.get('timePeriod', {}).get('endDate', {}).get('year'),
            })
            
            # All education
            edu_list = []
            for edu in educations:
                time_period = edu.get('timePeriod', {})
                start_date = time_period.get('startDate', {})
                end_date = time_period.get('endDate', {})
                
                edu_data = {
                    'school': edu.get('schoolName', ''),
                    'degree': edu.get('degreeName', ''),
                    'field_of_study': edu.get('fieldOfStudy', ''),
                    'grade': edu.get('grade', ''),
                    'start_year': start_date.get('year'),
                    'end_year': end_date.get('year') if end_date else None,
                    'is_current': end_date is None,
                }
                edu_list.append(edu_data)
            
            extracted_data['educations'] = edu_list
            extracted_data['education_count'] = len(edu_list)
        
        # Skills
        skills = profile.get('skills', [])
        if skills:
            skill_names = [skill.get('name', '') for skill in skills if skill.get('name')]
            extracted_data['skills'] = skill_names
            extracted_data['skills_count'] = len(skill_names)
            extracted_data['top_skills'] = skill_names[:5] if len(skill_names) >= 5 else skill_names
        
        # Languages
        languages = profile.get('languages', [])
        if languages:
            lang_list = []
            for lang in languages:
                lang_data = {
                    'name': lang.get('name', ''),
                    'proficiency': lang.get('proficiency', '')
                }
                lang_list.append(lang_data)
            
            extracted_data['languages'] = lang_list
            extracted_data['language_count'] = len(lang_list)
        
        # Publications
        publications = profile.get('publications', [])
        if publications:
            pub_list = []
            for pub in publications:
                pub_data = {
                    'name': pub.get('name', ''),
                    'publisher': pub.get('publisher', ''),
                    'description': pub.get('description', ''),
                    'url': pub.get('url', ''),
                    'year': pub.get('date', {}).get('year'),
                    'month': pub.get('date', {}).get('month'),
                }
                pub_list.append(pub_data)
            
            extracted_data['publications'] = pub_list
            extracted_data['publication_count'] = len(pub_list)
        
        # Certifications
        certifications = profile.get('certifications', [])
        if certifications:
            cert_list = []
            for cert in certifications:
                cert_data = {
                    'name': cert.get('name', ''),
                    'authority': cert.get('authority', ''),
                    'license_number': cert.get('licenseNumber', ''),
                    'url': cert.get('url', ''),
                    'year': cert.get('timePeriod', {}).get('startDate', {}).get('year'),
                    'month': cert.get('timePeriod', {}).get('startDate', {}).get('month'),
                }
                cert_list.append(cert_data)
            
            extracted_data['certifications'] = cert_list
            extracted_data['certification_count'] = len(cert_list)
        
        # Projects
        projects = profile.get('projects', [])
        if projects:
            proj_list = []
            for proj in projects:
                time_period = proj.get('timePeriod', {})
                start_date = time_period.get('startDate', {})
                end_date = time_period.get('endDate', {})
                
                proj_data = {
                    'title': proj.get('title', ''),
                    'description': proj.get('description', ''),
                    'url': proj.get('url', ''),
                    'start_month': start_date.get('month'),
                    'start_year': start_date.get('year'),
                    'end_month': end_date.get('month') if end_date else None,
                    'end_year': end_date.get('year') if end_date else None,
                }
                proj_list.append(proj_data)
            
            extracted_data['projects'] = proj_list
            extracted_data['project_count'] = len(proj_list)
        
        # Volunteer experience
        volunteer = profile.get('volunteer', [])
        if volunteer:
            vol_list = []
            for vol in volunteer:
                time_period = vol.get('timePeriod', {})
                start_date = time_period.get('startDate', {})
                end_date = time_period.get('endDate', {})
                
                vol_data = {
                    'organization': vol.get('companyName', ''),
                    'role': vol.get('role', ''),
                    'description': vol.get('description', ''),
                    'start_month': start_date.get('month'),
                    'start_year': start_date.get('year'),
                    'end_month': end_date.get('month') if end_date else None,
                    'end_year': end_date.get('year') if end_date else None,
                }
                vol_list.append(vol_data)
            
            extracted_data['volunteer_experiences'] = vol_list
            extracted_data['volunteer_count'] = len(vol_list)
        
        # Honors and awards
        honors = profile.get('honors', [])
        if honors:
            honor_list = []
            for honor in honors:
                honor_data = {
                    'title': honor.get('title', ''),
                    'issuer': honor.get('issuer', ''),
                    'description': honor.get('description', ''),
                    'year': honor.get('date', {}).get('year'),
                    'month': honor.get('date', {}).get('month'),
                }
                honor_list.append(honor_data)
            
            extracted_data['honors'] = honor_list
            extracted_data['honor_count'] = len(honor_list)
        
        # Add derived fields for analysis
        
        # Education level
        if 'educations' in extracted_data:
            has_phd = any('ph' in edu.get('degree', '').lower() or 'doctor' in edu.get('degree', '').lower() for edu in extracted_data['educations'])
            has_masters = any('master' in edu.get('degree', '').lower() or 'ms' == edu.get('degree', '').lower() or 'mba' in edu.get('degree', '').lower() for edu in extracted_data['educations'])
            has_bachelors = any('bachelor' in edu.get('degree', '').lower() or 'bs' == edu.get('degree', '').lower() or 'ba' == edu.get('degree', '').lower() for edu in extracted_data['educations'])
            
            if has_phd:
                education_level = 'PhD'
            elif has_masters:
                education_level = 'Masters'
            elif has_bachelors:
                education_level = 'Bachelors'
            else:
                education_level = 'Other'
            
            extracted_data['education_level'] = education_level
        
        # Career level
        if 'experiences' in extracted_data:
            current_title = extracted_data.get('current_title', '').lower()
            
            is_executive = any(term in current_title for term in ['ceo', 'cto', 'cfo', 'coo', 'chief', 'president', 'founder', 'owner', 'partner'])
            is_director = any(term in current_title for term in ['director', 'head', 'vp', 'vice president'])
            is_manager = 'manager' in current_title or 'lead' in current_title
            is_senior = 'senior' in current_title or 'sr' in current_title or 'principal' in current_title
            
            if is_executive:
                career_level = 'Executive'
            elif is_director:
                career_level = 'Director'
            elif is_manager:
                career_level = 'Manager'
            elif is_senior:
                career_level = 'Senior'
            else:
                career_level = 'Other'
            
            extracted_data['career_level'] = career_level
        
        return extracted_data
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None


def process_profiles_and_upload_to_gcp(temp_dir="/tmp/profiles", gcp_folder="linkedin_data_processing/processed_profiles"):
    """
    Process LinkedIn profile JSON files and upload directly to GCP.
    
    Args:
        temp_dir (str): Temporary directory containing raw profile JSON files
        gcp_folder (str): GCP folder to store processed profiles
    """
    # Initialize GCP client
    storage_client = initialize_gcp_client()
    if not storage_client:
        print("Failed to initialize GCP client. Exiting.")
        return False
    
    try:
        bucket_name = "expert-finder-bucket-1"
        bucket = storage_client.bucket(bucket_name)
        
        # Get all JSON files in the input directory
        profile_files = glob.glob(os.path.join(temp_dir, "*.json"))
        print(f"Found {len(profile_files)} profile files to process")
        
        # First pass: extract data from all profiles
        print("Extracting data from all profiles...")
        all_profiles = []
        for file_path in tqdm(profile_files, desc="Extracting profile data"):
            try:
                # Skip files that are not profile files
                if file_path.endswith('errors.json'):
                    continue
                    
                # Extract profile data
                profile_data = extract_profile_data(file_path)
                
                if profile_data and profile_data.get('urn_id'):
                    all_profiles.append(profile_data)
                    
            except Exception as e:
                print(f"Error extracting data from {file_path}: {str(e)}")
        
        print(f"Extracted data from {len(all_profiles)} profiles")
        
        # Second pass: calculate credibility scores
        print("Calculating credibility scores...")
        credibility_calculator = DynamicCredibilityCalculator()
        all_profiles = credibility_calculator.process_profiles(all_profiles)
        
        # Third pass: upload processed profiles
        print("Uploading profiles with credibility scores...")
        processed_count = 0
        for profile_data in tqdm(all_profiles, desc="Uploading profiles"):
            try:
                # Create JSON string
                json_data = json.dumps(profile_data, indent=2, ensure_ascii=False)
                
                # Upload directly to GCP
                gcp_filename = f"{gcp_folder}/{profile_data['urn_id']}_processed.json"
                blob = bucket.blob(gcp_filename)
                blob.upload_from_string(json_data, content_type='application/json')
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error uploading {profile_data.get('urn_id', 'unknown')}: {str(e)}")
        
        print(f"Successfully processed and uploaded {processed_count} profiles to GCP")
        print(f"Credibility distribution: {get_credibility_distribution(all_profiles)}")
        return True
        
    except Exception as e:
        print(f"Error processing profiles: {str(e)}")
        return False

def get_credibility_distribution(profiles):
    """Get distribution of credibility levels for reporting."""
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for profile in profiles:
        level = profile.get('credibility', {}).get('level', 1)
        distribution[level] = distribution.get(level, 0) + 1
    
    # Calculate percentages
    total = len(profiles)
    if total > 0:
        for level in distribution:
            distribution[level] = {
                'count': distribution[level],
                'percentage': round((distribution[level] / total) * 100, 2)
            }
    
    return distribution



def download_new_processed_profiles_for_rag(storage_client, existing_profiles, temp_dir="/tmp/processed_profiles", gcp_folder="linkedin_data_processing/processed_profiles"):
    """
    Download only new processed profiles from GCP for RAG preparation.
    
    Args:
        storage_client: GCP storage client
        existing_profiles: Set of URN IDs already in ChromaDB
        temp_dir (str): Temporary directory to store downloaded profiles
        gcp_folder (str): GCP folder containing processed profiles
        
    Returns:
        str: Path to the temporary directory with downloaded profiles
    """
    # Create temporary directory
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        bucket_name = "expert-finder-bucket-1"
        bucket = storage_client.bucket(bucket_name)
        
        # List all processed profiles in GCP
        blobs = list(bucket.list_blobs(prefix=gcp_folder))
        processed_files = [blob for blob in blobs if blob.name.endswith('_processed.json')]
        
        print(f"Found {len(processed_files)} processed profiles in GCP")
        
        # Filter out profiles already in ChromaDB
        new_blobs = []
        for blob in processed_files:
            # Extract URN ID from filename
            basename = os.path.basename(blob.name)
            urn_id = basename.replace('_processed.json', '')
            
            if urn_id not in existing_profiles:
                new_blobs.append(blob)
        
        print(f"Found {len(new_blobs)} new processed profiles to download")
        
        # Download only new files with progress bar
        for blob in tqdm(new_blobs, desc="Downloading new processed profiles"):
            local_path = os.path.join(temp_dir, os.path.basename(blob.name))
            blob.download_to_filename(local_path)
        
        print(f"Downloaded {len(new_blobs)} new processed profiles to {temp_dir}")
        return temp_dir if new_blobs else None
    
    except Exception as e:
        print(f"Error downloading processed profiles: {str(e)}")
        return None

def get_profiles_in_chroma(chroma_dir="chroma_db"):
    """
    Get a set of URN IDs already in ChromaDB.
    
    Args:
        chroma_dir (str): Directory where ChromaDB data is persisted
        
    Returns:
        set: Set of URN IDs already in ChromaDB
    """
    try:
        # Set up ChromaDB
        _, collection = setup_chroma_db(chroma_dir)
        
        # Get all IDs in the collection
        result = collection.get(include=["metadatas"])
        
        if result and result['ids']:
            return set(result['ids'])
        return set()
    
    except Exception as e:
        print(f"Error getting profiles from ChromaDB: {str(e)}")
        return set()

def prepare_profiles_for_rag(chroma_dir="chroma_db", embedding_model_name="all-MiniLM-L6-v2"):
    """
    Download processed profiles from GCP and prepare them for RAG.
    Only adds profiles that aren't already in ChromaDB.
    
    Args:
        chroma_dir (str): Directory to persist ChromaDB data
        embedding_model_name (str): Name of the sentence transformer model to use
    """
    # Initialize GCP client
    storage_client = initialize_gcp_client()
    if not storage_client:
        print("Failed to initialize GCP client. Exiting.")
        return False
    
    # Create temporary directory for processed profiles
    temp_dir = "/tmp/processed_profiles"
    
    try:
        # Get profiles already in ChromaDB
        existing_profiles = get_profiles_in_chroma(chroma_dir)
        print(f"Found {len(existing_profiles)} profiles already in ChromaDB")
        
        # Download only new processed profiles
        temp_dir = download_new_processed_profiles_for_rag(storage_client, existing_profiles, temp_dir)
        if not temp_dir:
            print("No new profiles to add to ChromaDB. Exiting.")
            return True  # Return True as this is not an error
        
        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model_name}")
        embedding_model = SentenceTransformer(embedding_model_name)
        
        # Set up ChromaDB
        _, collection = setup_chroma_db(chroma_dir)
        
        # Get all processed JSON files
        json_files = glob.glob(os.path.join(temp_dir, "*_processed.json"))
        print(f"Found {len(json_files)} processed files to check")
        
        # Filter out files that are already in ChromaDB
        new_files = []
        for file_path in json_files:
            try:
                # Extract URN ID from filename
                basename = os.path.basename(file_path)
                urn_id = basename.replace('_processed.json', '')
                
                if urn_id not in existing_profiles:
                    new_files.append(file_path)
            except Exception:
                # If we can't parse the filename, include it to be safe
                new_files.append(file_path)
        
        print(f"Found {len(new_files)} new profiles to add to ChromaDB")
        
        # Process each new file
        processed_count = 0
        for file_path in tqdm(new_files, desc="Preparing new profiles for RAG"):
            try:
                # Load profile data
                with open(file_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                
                # Skip if no URN ID
                if not profile.get('urn_id'):
                    continue
                
                # Create text representation
                profile_text = create_profile_text(profile)
                
                # Generate embedding
                embedding = embedding_model.encode(profile_text)
                
                # Create metadata for filtering
                metadata = {
                    "urn_id": profile.get("urn_id"),
                    "name": profile.get("full_name", ""),
                    "current_title": profile.get("current_title", ""),
                    "current_company": profile.get("current_company", ""),
                    "location": profile.get("location_name", ""),
                    "industry": profile.get("industry", ""),
                    "education_level": profile.get("education_level", ""),
                    "career_level": profile.get("career_level", ""),
                    "years_experience": str(profile.get("total_years_experience", 0))
                }
                
                # Add to ChromaDB
                collection.upsert(
                    ids=[profile.get("urn_id")],
                    embeddings=[embedding.tolist()],
                    metadatas=[metadata],
                    documents=[profile_text]
                )
                
                processed_count += 1
                    
            except Exception as e:
                print(f"Error preparing {file_path} for RAG: {str(e)}")
        
        print(f"Successfully added {processed_count} new profiles to RAG")
        print(f"ChromaDB collection now has {collection.count()} documents")
        
        return True
    
    except Exception as e:
        print(f"Error in RAG preparation: {str(e)}")
        return False
    
    finally:
        # Clean up temporary directory
        try:
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
            print(f"✅ Temporary directory {temp_dir} has been removed")
        except Exception as e:
            print(f"⚠️ Warning: Could not remove temporary directory: {str(e)}")

# Part 3: Prepare profiles for ChromaDB and RAG
def create_profile_text(profile):
    """
    Create a text representation of a profile for embedding.
    
    Args:
        profile (dict): Processed profile data
        
    Returns:
        str: Text representation of the profile
    """
    sections = []
    
    # Basic info
    basic_info = f"Name: {profile.get('full_name', '')}\n"
    if profile.get('headline'):
        basic_info += f"Headline: {profile.get('headline')}\n"
    basic_info += f"Location: {profile.get('location_name', '')}\n"
    if profile.get('industry'):
        basic_info += f"Industry: {profile.get('industry')}\n"
    sections.append(basic_info)
    
    # Summary
    if profile.get('summary'):
        sections.append(f"Summary: {profile.get('summary')}")
    
    # Current position
    if profile.get('current_title') and profile.get('current_company'):
        sections.append(f"Current Position: {profile.get('current_title')} at {profile.get('current_company')}")
    
    # Experience
    if 'experiences' in profile and profile['experiences']:
        exp_texts = []
        for exp in profile['experiences']:
            exp_text = f"{exp.get('title')} at {exp.get('company')}"
            if exp.get('description'):
                exp_text += f": {exp.get('description')}"
            exp_texts.append(exp_text)
        sections.append("Experience: " + "\n".join(exp_texts))
    
    # Education
    if 'educations' in profile and profile['educations']:
        edu_texts = []
        for edu in profile['educations']:
            edu_text = f"{edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('school', '')}"
            edu_texts.append(edu_text)
        sections.append("Education: " + "\n".join(edu_texts))
    
    # Skills
    if 'skills' in profile and profile['skills']:
        sections.append("Skills: " + ", ".join(profile['skills']))
    
    # Publications
    if 'publications' in profile and profile['publications']:
        pub_texts = []
        for pub in profile['publications']:
            pub_text = f"{pub.get('name', '')}"
            if pub.get('description'):
                pub_text += f": {pub.get('description')}"
            pub_texts.append(pub_text)
        sections.append("Publications: " + "\n".join(pub_texts))
    
    # Projects
    if 'projects' in profile and profile['projects']:
        proj_texts = []
        for proj in profile['projects']:
            proj_text = f"{proj.get('title', '')}"
            if proj.get('description'):
                proj_text += f": {proj.get('description')}"
            proj_texts.append(proj_text)
        sections.append("Projects: " + "\n".join(proj_texts))
    
    return "\n\n".join(sections)

def setup_chroma_db(persist_directory="chroma_db"):
    """
    Set up and return a ChromaDB client and collection.
    
    Args:
        persist_directory (str): Directory to persist ChromaDB data
        
    Returns:
        tuple: (chroma_client, collection)
    """
    # Create directory if it doesn't exist
    os.makedirs(persist_directory, exist_ok=True)
    
    # Initialize ChromaDB with persistence
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    
    # Create or get collection
    try:
        collection = chroma_client.get_collection(name="linkedin_profiles")
        print(f"Using existing collection 'linkedin_profiles' with {collection.count()} documents")
    except:
        collection = chroma_client.create_collection(
            name="linkedin_profiles",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        print("Created new collection 'linkedin_profiles'")
    
    return chroma_client, collection



# Part 4: RAG search function

def search_profiles_demo(query, filters=None, top_k=5, chroma_dir="chroma_db"):
    """
    Search for profiles using semantic search with optional filters.
    
    Args:
        query (str): The search query
        filters (dict, optional): Metadata filters (e.g., {"industry": "Internet"})
        top_k (int): Number of results to return
        chroma_dir (str): Directory where ChromaDB data is persisted
        
    Returns:
        list: Matching profiles with similarity scores
    """
    # Initialize embedding model
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Set up ChromaDB
    _, collection = setup_chroma_db(chroma_dir)
    
    # Generate query embedding
    query_embedding = embedding_model.encode(query)
    
    # Prepare where clause if filters are provided
    where_clause = {}
    if filters:
        for key, value in filters.items():
            if key in ["industry", "location", "current_company", "education_level", "career_level"]:
                where_clause[key] = value
    
    # Search in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
        where=where_clause if where_clause else None
    )
    
    # Format results
    matches = []
    if results and results['ids'] and len(results['ids'][0]) > 0:
        for i, (doc_id, document, metadata, distance) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            # Calculate similarity score (convert distance to similarity)
            similarity = 1 - distance
            
            matches.append({
                "rank": i + 1,
                "urn_id": doc_id,
                "name": metadata.get("name"),
                "current_title": metadata.get("current_title"),
                "current_company": metadata.get("current_company"),
                "location": metadata.get("location"),
                "industry": metadata.get("industry"),
                "education_level": metadata.get("education_level"),
                "career_level": metadata.get("career_level"),
                "similarity": similarity,
                "profile_summary": document[:300] + "..." if len(document) > 300 else document
            })
    
    return matches



def demo_search(query, filters=None, top_k=5, chroma_dir="chroma_db"):
    """Demonstrate the search functionality."""
    print(f"Searching for: '{query}'")
    if filters:
        print(f"With filters: {filters}")
    
    results = search_profiles_demo(query, filters, top_k, chroma_dir)
    
    print(f"\nFound {len(results)} matching profiles:")
    for result in results:
        print(f"\n{result['rank']}. {result['name']} ({result['similarity']:.2f})")
        print(f"   {result['current_title']} at {result['current_company']}")
        print(f"   Location: {result['location']}")
        print(f"   Industry: {result['industry']}")
        print(f"   Summary: {result['profile_summary'][:150]}...")

def get_metadata_values(field_name, chroma_dir="chroma_db"):
    """
    Get all unique values for a specific metadata field from ChromaDB.
    Used for testing.
    
    Args:
        field_name (str): The metadata field name to extract values for
        chroma_dir (str): Directory where ChromaDB data is persisted
        
    Returns:
        list: Sorted list of unique values for the specified field
    """
    # Set up ChromaDB
    _, collection = setup_chroma_db(chroma_dir)
    
    try:
        # Get all items from the collection
        # We only need the metadata
        result = collection.get(include=["metadatas"])
        
        if not result or not result['metadatas']:
            print(f"No data found in the collection")
            return []
        
        # Extract all values for the specified field
        values = []
        for metadata in result['metadatas']:
            if field_name in metadata and metadata[field_name] is not None:
                values.append(metadata[field_name])
        
        # Get unique values and sort them
        unique_values = sorted(list(set(values)))
        
        print(f"Found {len(unique_values)} unique values for '{field_name}'")
        return unique_values
        
    except Exception as e:
        print(f"Error getting metadata values: {str(e)}")
        return []

# Main execution with simplified argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Profile Processing and RAG Preparation")
    parser.add_argument("--action", choices=["process", "prepare_rag", "search", "all"], 
                        default="all", help="Action to perform")
    parser.add_argument("--chroma_dir", default="chroma_db", 
                        help="Directory to persist ChromaDB data")
    parser.add_argument("--query", default="machine learning experts with experience at top tech companies", 
                        help="Search query (for search action)")
    parser.add_argument("--industry", help="Filter by industry (for search action)")
    parser.add_argument("--location", help="Filter by location (for search action)")
    parser.add_argument("--top_k", type=int, default=5, 
                        help="Number of results to return (for search action)")
    parser.add_argument("--force", action="store_true",
                        help="Force processing of all profiles, even if already processed")
    
    args = parser.parse_args()
    
    # Execute requested action
    if args.action == "process":
        # Download unprocessed profiles from GCP to temporary directory
        storage_client = initialize_gcp_client()
        if storage_client:
            if args.force:
                # Download all profiles if force flag is set
                temp_dir = download_profiles_from_gcp(storage_client)
            else:
                # Download only unprocessed profiles
                temp_dir = download_unprocessed_profiles_from_gcp(storage_client)
                
            if temp_dir:
                # Process and upload directly to GCP
                process_profiles_and_upload_to_gcp(temp_dir)
            else:
                print("No new profiles to process.")
    
    elif args.action == "prepare_rag":
        prepare_profiles_for_rag(chroma_dir=args.chroma_dir)
    
    elif args.action == "search":
        filters = {}
        if args.industry:
            filters["industry"] = args.industry
        if args.location:
            filters["location"] = args.location
        demo_search(args.query, filters, args.top_k, args.chroma_dir)
    
    elif args.action == "all":
        # Download unprocessed profiles from GCP to temporary directory
        storage_client = initialize_gcp_client()
        if storage_client:
            if args.force:
                # Download all profiles if force flag is set
                temp_dir = download_profiles_from_gcp(storage_client)
            else:
                # Download only unprocessed profiles
                temp_dir = download_unprocessed_profiles_from_gcp(storage_client)
                
            if temp_dir:
                # Process and upload directly to GCP
                process_profiles_and_upload_to_gcp(temp_dir)
                
                # Prepare for RAG
                prepare_profiles_for_rag(chroma_dir=args.chroma_dir)
                
                # Demo search
                filters = {}
                if args.industry:
                    filters["industry"] = args.industry
                if args.location:
                    filters["location"] = args.location
                demo_search(args.query, filters, args.top_k, args.chroma_dir)
            else:
                print("No new profiles to process. Skipping to RAG preparation.")
                
                # Prepare for RAG
                prepare_profiles_for_rag(chroma_dir=args.chroma_dir)
                
                # Demo search
                filters = {}
                if args.industry:
                    filters["industry"] = args.industry
                if args.location:
                    filters["location"] = args.location
                demo_search(args.query, filters, args.top_k, args.chroma_dir)