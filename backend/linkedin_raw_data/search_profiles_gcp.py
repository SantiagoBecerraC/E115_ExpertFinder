import json
import os
import random
import sys
import time
from datetime import datetime

from google.cloud import storage
from google.oauth2 import service_account
from linkedin_api import Linkedin

# GCP bucket configuration
bucket_name = "expert-finder-bucket-1"

REGIONS = {
    "103644278": "United States",
    "101452733": "United Kingdom",
    "101174742": "Canada",
    "101452733": "Australia",
    "103350119": "Germany",
    "103819153": "France",
    "104746697": "India",
}


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


def upload_to_gcp(storage_client, data, filename):
    """
    Upload data directly to GCP bucket.

    Args:
        storage_client: GCP storage client
        data (dict): Data to upload
        filename (str): Filename to use in GCP
    """
    if not storage_client:
        print("❌ GCP client not initialized. Cannot upload data.")
        return False

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)

        # Convert data to JSON string
        json_data = json.dumps(data, indent=4, ensure_ascii=False)

        # Upload JSON string directly to GCP
        blob.upload_from_string(json_data, content_type="application/json")
        print(f"✅ Successfully uploaded {filename} to GCP bucket")
        return True
    except Exception as e:
        print(f"❌ Error uploading to GCP bucket: {str(e)}")
        return False


def search_linkedin(keywords, region_code="103644278", storage_client=None):
    """
    Search LinkedIn for profiles matching the given keywords in the specified region.

    Args:
        keywords (list): List of keywords to search for
        region_code (str, optional): Region code to search in. Defaults to USA.
        storage_client: GCP storage client
    """
    if region_code in REGIONS:
        current_region_code = region_code
        current_region_name = REGIONS[current_region_code]
    else:
        print(f"Warning: Invalid region code '{region_code}'. Using default (USA).")
        current_region_code = "103644278"  # Default to USA
        current_region_name = REGIONS[current_region_code]

    print(f"Using region: {current_region_name} ({current_region_code})")

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
            people = api.search_people(keywords=keyword_pair, regions=[current_region_code], limit=100)

            # Only save if we have results
            if people and len(people) > 0:
                # Prepare the results
                gcp_filename = f"linkedin_raw_data/data/keyword_searches/search_{timestamp}.json"
                results = {
                    "keywords": keyword_pair,
                    "timestamp": datetime.now().isoformat(),
                    "region_code": current_region_code,
                    "region_name": current_region_name,
                    "results": people,
                }

                # Upload directly to GCP
                if storage_client:
                    upload_success = upload_to_gcp(storage_client, results, gcp_filename)
                    if upload_success:
                        print(f"Saved {len(people)} results for pair {i} in {current_region_name} to GCP")
                    else:
                        print(f"Failed to save results for pair {i} to GCP")
                else:
                    print("No GCP client available. Cannot save results.")
            else:
                print(f"No results found for pair {i}: '{keyword_pair}' in {current_region_name}. Skipping save.")

        except Exception as e:
            print(f"Error occurred with keyword pair '{keyword_pair}' in {current_region_name}")
            print(f"Error message: {str(e)}")
            # Log the error to GCP
            if storage_client:
                error_data = {
                    "error": str(e),
                    "keywords": keyword_pair,
                    "region": current_region_name,
                    "region_code": current_region_code,
                    "timestamp": datetime.now().isoformat(),
                }
                error_filename = f"linkedin_raw_data/data/keyword_searches/errors_{timestamp}.json"
                upload_to_gcp(storage_client, error_data, error_filename)


def print_available_regions():
    """Print all available regions with their codes."""
    print("\nAvailable regions:")
    for code, name in REGIONS.items():
        print(f"  {name}: {code}")


if __name__ == "__main__":
    # Check if help is requested
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python search_profiles_gcp.py keyword1 keyword2 ... [--region REGION_CODE]")
        print("Example: python search_profiles_gcp.py machine learning data science")
        print("Example with region: python search_profiles_gcp.py machine learning data science --region 101452733")
        print_available_regions()
        sys.exit(0)

    # Default values
    keywords = []
    region_code = "103644278"  # Default to USA

    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--region":
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

        # Authenticate using any Linkedin user account credentials
        try:
            api = Linkedin("3chamois-bifocal@icloud.com", "cinnyn-surfix-8Cejji", refresh_cookies=True)
        except Exception as e:
            print(f"❌ Error authenticating: {str(e)}")
            sys.exit(1)

        # Only initialize GCP client when keywords are provided
        storage_client = initialize_gcp_client()
        search_linkedin(keywords, region_code, storage_client)
    else:
        print("No keywords provided or not enough keywords. Skipping search.")
