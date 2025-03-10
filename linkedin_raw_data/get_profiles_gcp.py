import pandas as pd
import time
import random
import json
import os
from datetime import datetime
from linkedin_api import Linkedin
from google.cloud import storage
from google.oauth2 import service_account

# Initialize GCP client using environment credentials
try:
    storage_client = storage.Client()
    print("✅ Successfully connected to GCP using environment credentials")
except Exception as e:
    print(f"❌ Error initializing GCP client: {str(e)}")
    print("Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly")
    exit(1)

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
    exit(1)

# GCP paths
combined_csv_path = "linkedin_raw_data/data/combined_linkedin_searches.csv"
processed_urns_path = "linkedin_raw_data/data/processed_profile_urns.txt"
profiles_folder = "linkedin_raw_data/data/profiles/"

# Create local temp directory
temp_dir = "/tmp/linkedin_profiles"
os.makedirs(temp_dir, exist_ok=True)

# Authenticate using Linkedin credentials
# api = Linkedin('3chamois-bifocal@icloud.com', 'cinnyn-surfix-8Cejji', refresh_cookies=True)
# api = Linkedin('99-rafter.balcony@icloud.com', 'howvon-peDra4-gaggeb', refresh_cookies=True)
api = Linkedin('hjy.alder@outlook.com', 'Abced12sg!', refresh_cookies=True)

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


# Constants
MIN_WAIT_TIME = 40  # Minimum wait time in seconds
MAX_WAIT_TIME = 70   # Maximum wait time in seconds
MIN_INTERVAL = 5 * 60  # Minimum interval in seconds (8 minutes)
MAX_INTERVAL = 7 * 60  # Maximum interval in seconds (10 minutes)

start_time = time.time()

# Process each URN
for urn in urns_to_process:
    try:
        delay = random.uniform(10, 20)
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
            print(f"Saved processed URNs list to GCP")
            
        print(f"Saved profile for URN: {urn}")
        
        # Check elapsed time
        elapsed_time = time.time() - start_time
        if elapsed_time >= random.uniform(MIN_INTERVAL, MAX_INTERVAL):
            # Wait for a random time between 40 to 70 seconds
            wait_time = random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME)
            print(f"Taking a break for {wait_time:.1f} seconds...")
            time.sleep(wait_time)  # Wait for a random time
            start_time = time.time()  # Reset the timer

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
