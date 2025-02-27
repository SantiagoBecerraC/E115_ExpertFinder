import os
import pandas as pd
import json
from google.cloud import storage
import glob

# GCP Authentication
# Option 1: Set credentials via environment variable (recommended)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your-service-account-key.json"

# Option 2: Explicitly specify credentials in code
# from google.oauth2 import service_account
# credentials = service_account.Credentials.from_service_account_file(
#     'path/to/your-service-account-key.json')
# storage_client = storage.Client(credentials=credentials)

from google.oauth2 import service_account
# Path to your credentials file
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
bucket_name = "expert-finder-bucket-1"  # Replace with your actual bucket name
try:
    bucket = storage_client.bucket(bucket_name)
    # Test bucket access
    bucket.exists()
    print(f"✅ Successfully connected to GCP bucket: {bucket_name}")
except Exception as e:
    print(f"❌ Error connecting to GCP bucket: {bucket_name}")
    print(f"Error details: {str(e)}")

# # File paths
combined_csv_path = "linkedin_raw_data/data/combined_linkedin_searches.csv"
processed_files_path = "linkedin_raw_data/data/processed_files.txt"
search_files_prefix = "linkedin_raw_data/data/keyword_searches/search_"

# Local paths (if needed)
local_combined_csv = "linkedin_raw_data/data/combined_linkedin_searches.csv"
local_processed_files = "linkedin_raw_data/data/processed_files.txt"
local_search_files_pattern = "linkedin_raw_data/data/keyword_searches/search_*.json"

# Load existing data if available
existing_df = pd.DataFrame()
combined_blob = bucket.blob(combined_csv_path)

if combined_blob.exists():
    # Download from GCP to a temporary file and load
    temp_csv_path = "/tmp/combined_linkedin_searches.csv"
    combined_blob.download_to_filename(temp_csv_path)
    existing_df = pd.read_csv(temp_csv_path)
    print(f"Loaded existing data from GCP with {len(existing_df)} records")
elif os.path.exists(local_combined_csv):
    # If not in GCP but exists locally, load local file and upload to GCP
    existing_df = pd.read_csv(local_combined_csv)
    print(f"Loaded existing data from local file with {len(existing_df)} records")
    # Upload to GCP
    combined_blob.upload_from_filename(local_combined_csv)
    print(f"Uploaded combined CSV to GCP bucket")
else:
    print("No existing data found")

# Load list of previously processed files
processed_files = set()
processed_blob = bucket.blob(processed_files_path)

if processed_blob.exists():
    # Download and read processed files list from GCP
    temp_processed_path = "/tmp/processed_files.txt"
    processed_blob.download_to_filename(temp_processed_path)
    with open(temp_processed_path, 'r') as f:
        processed_files = set(f.read().splitlines())
    print(f"Found {len(processed_files)} previously processed files in GCP")
elif os.path.exists(local_processed_files):
    # If not in GCP but exists locally, load local file and upload to GCP
    with open(local_processed_files, 'r') as f:
        processed_files = set(f.read().splitlines())
    print(f"Found {len(processed_files)} previously processed files locally")
    # Upload to GCP
    processed_blob.upload_from_filename(local_processed_files)
    print(f"Uploaded processed files list to GCP bucket")

# Get all JSON files from the bucket
gcp_search_files = []
blobs = list(bucket.list_blobs(prefix=search_files_prefix))
for blob in blobs:
    if blob.name.endswith('.json'):
        gcp_search_files.append(blob.name)

# Check if we need to upload local search files to GCP
if not gcp_search_files:
    # Look for local search files
    local_search_files = glob.glob(local_search_files_pattern)
    if local_search_files:
        print(f"Found {len(local_search_files)} local search files to upload to GCP")
        for local_file in local_search_files:
            # Create the GCP path
            gcp_path = local_file.replace('\\', '/')  # Handle Windows paths
            blob = bucket.blob(gcp_path)
            blob.upload_from_filename(local_file)
            gcp_search_files.append(gcp_path)
        print(f"Uploaded {len(local_search_files)} search files to GCP bucket")

# Get all search files and filter out already processed ones
all_search_files = gcp_search_files
new_files = [f for f in all_search_files if f not in processed_files]
print(f"Found {len(new_files)} new files to process")

# List to store new data
new_data = []

# Process each new file
for file_path in new_files:
    try:
        # Download the file to a temporary location
        temp_json_path = f"/tmp/{os.path.basename(file_path)}"
        blob = bucket.blob(file_path)
        blob.download_to_filename(temp_json_path)
        
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extract the base data for each result
        for person in data['results']:
            record = {
                'keywords': data['keywords'],
                'timestamp': data['timestamp'],
                'region_code': data['region_code'],
                'person_id': person.get('urn_id'),
                'name': person.get('name'),
                'title': person.get('jobtitle'),
                'location': person.get('location'),
                'distance': person.get('distance')
            }
            new_data.append(record)
            
        # Add to processed files set
        processed_files.add(file_path)
        
        # Clean up temporary file
        os.remove(temp_json_path)
            
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")

# If we have new data, process and combine it
if new_data:
    # Create DataFrame with new data
    new_df = pd.DataFrame(new_data)
    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'])
    
    # Combine with existing data
    if not existing_df.empty:
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df
    
    # Remove duplicates from combined data
    print(f"\nBefore removing duplicates: {len(df)} records")
    df = df.drop_duplicates(subset='person_id', keep='first')
    print(f"After removing duplicates: {len(df)} records")

    # Sort by timestamp and keywords
    df = df.sort_values(['timestamp', 'keywords'])

    # Display basic information about the dataset
    print("\nDataset Summary:")
    print(f"Total records: {len(df)}")
    print(f"Unique keywords: {df['keywords'].nunique()}")
    print(f"Unique people: {df['person_id'].nunique()}")
    
    # Save updated data to a temporary file then upload to GCP
    temp_output_csv = "/tmp/combined_linkedin_searches.csv"
    df.to_csv(temp_output_csv, index=False)
    
    # Upload to GCP bucket
    combined_blob = bucket.blob(combined_csv_path)
    combined_blob.upload_from_filename(temp_output_csv)
    
    # Save updated list of processed files to a temporary file then upload
    temp_processed_output = "/tmp/processed_files.txt"
    with open(temp_processed_output, 'w') as f:
        f.write('\n'.join(processed_files))
    
    processed_blob = bucket.blob(processed_files_path)
    processed_blob.upload_from_filename(temp_processed_output)
    
    # Clean up temporary files
    os.remove(temp_output_csv)
    os.remove(temp_processed_output)
    
    print("\nUpdated data and processed files list saved to GCP bucket")
else:
    print("\nNo new data to process")