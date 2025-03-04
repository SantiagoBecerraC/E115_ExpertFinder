import pandas as pd
import time
import random
import json
import os
from datetime import datetime
from linkedin_api import Linkedin
from google.cloud import storage
from google.oauth2 import service_account

credentials_path = '../secrets/expertfinder-452203-3c0b81d81d3d.json'

 # Check if credentials file exists
if os.path.exists(credentials_path):
    print(f"✅ Credentials file found at: {credentials_path}")
    print(f"File size: {os.path.getsize(credentials_path)} bytes")
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        print("✅ Successfully loaded credentials from file")
        storage_client = storage.Client(credentials=credentials)
        print("✅ Created storage client with explicit credentials")
    except Exception as e:
        print(f"❌ Error loading credentials: {str(e)}")
else:
    print(f"❌ Credentials file NOT found at: {credentials_path}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please check the path to your credentials file")
    # Try to list files in the directory where credentials should be
    try:
        parent_dir = os.path.dirname(credentials_path)
        if os.path.exists(parent_dir):
            print(f"Files in {parent_dir}:")
            for file in os.listdir(parent_dir):
                print(f"  - {file}")
        else:
            print(f"Directory {parent_dir} does not exist")
    except Exception as e:
        print(f"Error listing directory: {str(e)}")

# GCP bucket configuration
bucket_name = "expert-finder-bucket-1"
try:
    bucket = storage_client.bucket(bucket_name)
    # Test bucket access
    bucket.exists()
    print(f"✅ Successfully connected to GCP bucket: {bucket_name}")
except Exception as e:
    print(f"❌ Error connecting to GCP bucket: {bucket_name}")
    print(f"Error details: {str(e)}")

# GCP paths
combined_csv_path = "linkedin_raw_data/data/combined_linkedin_searches.csv"
processed_urns_path = "linkedin_raw_data/data/processed_profile_urns.txt"
profiles_folder = "linkedin_raw_data/data/profiles/"

# Create local temp directory
temp_dir = "/tmp/linkedin_profiles"
os.makedirs(temp_dir, exist_ok=True)

# Authenticate using Linkedin credentials
api = Linkedin('3chamois-bifocal@icloud.com', 'cinnyn-surfix-8Cejji', refresh_cookies=True)

# Download and read the combined CSV file from GCP
temp_csv_path = "/tmp/combined_linkedin_searches.csv"
bucket.blob(combined_csv_path).download_to_filename(temp_csv_path)
df = pd.read_csv(temp_csv_path)

# Load list of already processed URNs from GCP
processed_urns = set()
processed_urns_blob = bucket.blob(processed_urns_path)
if processed_urns_blob.exists():
    temp_urns_path = "/tmp/processed_profile_urns.txt"
    processed_urns_blob.download_to_filename(temp_urns_path)
    with open(temp_urns_path, 'r') as f:
        processed_urns = set(f.read().splitlines())
    print(f"Found {len(processed_urns)} previously processed profiles")

# ... existing error handling setup ...
consecutive_errors = 0
MAX_CONSECUTIVE_ERRORS = 10

# Get list of URNs to process
urns_to_process = set(df['person_id'].unique()) - processed_urns
print(f"Found {len(urns_to_process)} new profiles to process")

# Process each URN
for urn in urns_to_process:
    try:
        delay = random.uniform(3, 15)
        time.sleep(delay)
        
        profile = api.get_profile(urn_id=urn)
        
        # Create profile data with metadata
        profile_data = {
            'urn_id': urn,
            'fetch_timestamp': datetime.now().isoformat(),
            'profile_data': profile
        }
        
        # Save to temporary file first
        temp_profile_path = f"{temp_dir}/{urn}.json"
        with open(temp_profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4, ensure_ascii=False)
        
        # Upload to GCP
        profile_blob = bucket.blob(f"{profiles_folder}{urn}.json")
        profile_blob.upload_from_filename(temp_profile_path)
        
        # Clean up temp file
        os.remove(temp_profile_path)
        
        # Reset consecutive errors counter
        consecutive_errors = 0
        
        # Add to processed URNs
        processed_urns.add(urn)
        
        # Periodically save processed URNs list to GCP (every 10 profiles)
        if len(processed_urns) % 10 == 0:
            temp_processed_path = "/tmp/processed_profile_urns.txt"
            with open(temp_processed_path, 'w') as f:
                f.write('\n'.join(processed_urns))
            processed_urns_blob.upload_from_filename(temp_processed_path)
            os.remove(temp_processed_path)
            
        print(f"Saved profile for URN: {urn}")
        
    except Exception as e:
        print(f"Error processing URN {urn}: {str(e)}")
        
        # Log errors to GCP
        error_blob = bucket.blob(f"{profiles_folder}errors.txt")
        error_message = f"{datetime.now().isoformat()}: Error with URN {urn}: {str(e)}\n"
        
        # Append to existing errors or create new file
        try:
            existing_errors = error_blob.download_as_text()
            error_message = existing_errors + error_message
        except:
            pass
        
        error_blob.upload_from_string(error_message)
        
        consecutive_errors += 1
        print(f"Consecutive errors: {consecutive_errors}")
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            print(f"\nStopping: {MAX_CONSECUTIVE_ERRORS} consecutive errors encountered")
            break

# Save final list of processed URNs to GCP
temp_final_urns_path = "/tmp/processed_profile_urns.txt"
with open(temp_final_urns_path, 'w') as f:
    f.write('\n'.join(processed_urns))
processed_urns_blob.upload_from_filename(temp_final_urns_path)
os.remove(temp_final_urns_path)

print(f"\nProcessing complete. Total profiles processed: {len(processed_urns)}")
