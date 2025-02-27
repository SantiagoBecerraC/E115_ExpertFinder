import time
import random
import json
import sys
from datetime import datetime
import os
from linkedin_api import Linkedin
from google.cloud import storage
from google.oauth2 import service_account

# Path to your credentials file
credentials_path = '../secrets/expertfinder-452203-3c0b81d81d3d.json'

# GCP bucket configuration
bucket_name = "expert-finder-bucket-1"

# Authenticate using any Linkedin user account credentials
api = Linkedin('3chamois-bifocal@icloud.com', 'cinnyn-surfix-8Cejji')

REGIONS = {
    '103644278': 'United States',
    '101452733': 'United Kingdom',
    '101174742': 'Canada',
    '101452733': 'Australia',
    '103350119': 'Germany',
    '103819153': 'France',
    '104746697': 'India'
}

def initialize_gcp_client():
    """Initialize and return GCP storage client."""
    try:
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            storage_client = storage.Client(credentials=credentials)
            print("✅ Successfully connected to GCP")
            return storage_client
        else:
            print(f"❌ Credentials file not found at: {credentials_path}")
            return None
    except Exception as e:
        print(f"❌ Error initializing GCP client: {str(e)}")
        return None

def sync_search_files_with_gcp(storage_client, new_local_file=None):
    """
    Sync search files between local storage and GCP bucket.
    
    Args:
        storage_client: GCP storage client
        new_local_file (str, optional): Path to a new local file to upload
    """
    if not storage_client:
        print("❌ GCP client not initialized. Skipping sync.")
        return
    
    try:
        bucket = storage_client.bucket(bucket_name)
        
        # Ensure local directory exists
        local_dir = "linkedin_raw_data/data/keyword_searches"
        os.makedirs(local_dir, exist_ok=True)
        
        # GCP path prefix
        gcp_prefix = "linkedin_raw_data/data/keyword_searches/search_"
        
        # Download all search files from GCP that don't exist locally
        blobs = list(bucket.list_blobs(prefix=gcp_prefix))
        for blob in blobs:
            local_file_path = blob.name
            if not os.path.exists(local_file_path):
                print(f"Downloading {blob.name} from GCP bucket")
                blob.download_to_filename(local_file_path)
        
        # Upload new local file if provided
        if new_local_file and os.path.exists(new_local_file):
            blob = bucket.blob(new_local_file)
            if not blob.exists():
                print(f"Uploading new file {new_local_file} to GCP bucket")
                blob.upload_from_filename(new_local_file)
        
        # Check for any other local files that aren't in GCP
        local_files = []
        for root, _, files in os.walk(local_dir):
            for file in files:
                if file.startswith("search_") and file.endswith(".json"):
                    local_files.append(os.path.join(root, file))
        
        # Upload any missing local files to GCP
        for local_file in local_files:
            gcp_path = local_file
            blob = bucket.blob(gcp_path)
            if not blob.exists():
                print(f"Uploading {local_file} to GCP bucket")
                blob.upload_from_filename(local_file)
        
        print("✅ Successfully synced search files with GCP bucket")
    except Exception as e:
        print(f"❌ Error syncing with GCP bucket: {str(e)}")

def search_linkedin(keywords, region_code='103644278'):
    """
    Search LinkedIn for profiles matching the given keywords in the specified region.
    
    Args:
        keywords (list): List of keywords to search for
        region_code (str, optional): Region code to search in. Defaults to USA.
    """
    if region_code in REGIONS:
        current_region_code = region_code
        current_region_name = REGIONS[current_region_code]
    else:
        print(f"Warning: Invalid region code '{region_code}'. Using default (USA).")
        current_region_code = '103644278'  # Default to USA
        current_region_name = REGIONS[current_region_code]
    
    print(f"Using region: {current_region_name} ({current_region_code})")
    
    # Ensure data directory exists
    os.makedirs("linkedin_raw_data/data/keyword_searches", exist_ok=True)
    
    # Iterate through pairs of keywords
    for i in range(len(keywords) - 1):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get current pair of keywords
        keyword_pair = f"{keywords[i]} {keywords[i+1]}"
        print(f"Searching for pair {i}: '{keyword_pair}' in {current_region_name}")
        
        try:
            # Random delay between 3-7 seconds to avoid rate limiting
            delay = random.uniform(3, 7)
            time.sleep(delay)
            
            # Search for people with the keyword pair
            people = api.search_people(
                keywords=keyword_pair,
                regions=[current_region_code],
                limit=100
            )
            
            # Only save if we have results
            if people and len(people) > 0:
                # Save the results immediately
                filename = f"linkedin_raw_data/data/keyword_searches/search_{timestamp}.json"
                results = {
                    'keywords': keyword_pair,
                    'timestamp': datetime.now().isoformat(),
                    'region_code': current_region_code,
                    'region_name': current_region_name,
                    'results': people
                }
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)
                    
                print(f"Saved {len(people)} results for pair {i} in {current_region_name}")
            else:
                print(f"No results found for pair {i}: '{keyword_pair}' in {current_region_name}. Skipping save.")
            
        except Exception as e:
            print(f"Error occurred with keyword pair '{keyword_pair}' in {current_region_name}")
            print(f"Error message: {str(e)}")
            # Save the error information
            error_filename = f"linkedin_raw_data/data/keyword_searches/errors_{timestamp}.txt"
            with open(error_filename, "a", encoding="utf-8") as f:
                f.write(f"Error at '{keyword_pair}' in {current_region_name} ({current_region_code}): {str(e)}\n")

def print_available_regions():
    """Print all available regions with their codes."""
    print("\nAvailable regions:")
    for code, name in REGIONS.items():
        print(f"  {name}: {code}")

if __name__ == "__main__":
    # Initialize GCP client
    storage_client = initialize_gcp_client()
    
    # Check if help is requested
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python search_profiles_gcp.py keyword1 keyword2 ... [--region REGION_CODE]")
        print("Example: python search_profiles_gcp.py machine learning data science")
        print("Example with region: python search_profiles_gcp.py machine learning data science --region 101452733")
        print_available_regions()
        sys.exit(0)
    
    # Default values
    keywords = []
    region_code = '103644278'  # Default to USA
    
    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--region':
            if i + 1 < len(sys.argv):
                region_code = sys.argv[i + 1]
                i += 2
            else:
                print("Error: --region flag requires a region code")
                print_available_regions()
                sys.exit(1)
        else:
            keywords.append(sys.argv[i])
            i += 1
    
    # Perform the search if keywords are provided
    if len(keywords) >= 2:
        print(f"Searching for keywords: {keywords}")
        print(f"In region: {REGIONS.get(region_code, 'Unknown')} ({region_code})")
        search_linkedin(keywords, region_code)
    else:
        print("No keywords provided or not enough keywords. Skipping search.")
    
    # Always sync with GCP at the end
    if storage_client:
        sync_search_files_with_gcp(storage_client)
    else:
        print("❌ GCP client not available. Skipping sync.")