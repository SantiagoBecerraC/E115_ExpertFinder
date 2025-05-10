import os
import pandas as pd
import json
from google.cloud import storage
from google.oauth2 import service_account


# Initialize GCP client
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


# GCP bucket configuration
bucket_name = "expert-finder-bucket-1"

# File paths in GCP
combined_csv_path = "linkedin_raw_data/data/combined_linkedin_searches.csv"
processed_files_path = "linkedin_raw_data/data/processed_files.txt"
search_files_prefix = "linkedin_raw_data/data/keyword_searches/search_"


def main():
    # Initialize GCP client
    storage_client = initialize_gcp_client()
    if not storage_client:
        print("Failed to initialize GCP client. Exiting.")
        return

    try:
        bucket = storage_client.bucket(bucket_name)
        # Test bucket access
        bucket.exists()
        print(f"✅ Successfully connected to GCP bucket: {bucket_name}")
    except Exception as e:
        print(f"❌ Error connecting to GCP bucket: {bucket_name}")
        print(f"Error details: {str(e)}")
        return

    # Load existing data if available
    existing_df = pd.DataFrame()
    combined_blob = bucket.blob(combined_csv_path)

    if combined_blob.exists():
        # Download from GCP to a temporary file and load
        temp_csv_path = "/tmp/combined_linkedin_searches.csv"
        combined_blob.download_to_filename(temp_csv_path)
        existing_df = pd.read_csv(temp_csv_path)
        print(f"Loaded existing data from GCP with {len(existing_df)} records")
        # Clean up temporary file
        os.remove(temp_csv_path)
    else:
        print("No existing combined data found in GCP bucket")

    # Load list of previously processed files
    processed_files = set()
    processed_blob = bucket.blob(processed_files_path)

    if processed_blob.exists():
        # Download and read processed files list from GCP
        temp_processed_path = "/tmp/processed_files.txt"
        processed_blob.download_to_filename(temp_processed_path)
        with open(temp_processed_path, "r") as f:
            processed_files = set(f.read().splitlines())
        print(f"Found {len(processed_files)} previously processed files in GCP")
        # Clean up temporary file
        os.remove(temp_processed_path)
    else:
        print("No processed files list found in GCP bucket")

    # Get all JSON search files from the bucket
    gcp_search_files = []
    blobs = list(bucket.list_blobs(prefix=search_files_prefix))
    for blob in blobs:
        if blob.name.endswith(".json"):
            gcp_search_files.append(blob.name)

    print(f"Found {len(gcp_search_files)} total search files in GCP bucket")

    # Filter out already processed files
    new_files = [f for f in gcp_search_files if f not in processed_files]
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

            with open(temp_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract the base data for each result
            for person in data["results"]:
                record = {
                    "keywords": data["keywords"],
                    "timestamp": data["timestamp"],
                    "region_code": data["region_code"],
                    "person_id": person.get("urn_id"),
                    "name": person.get("name"),
                    "title": person.get("jobtitle"),
                    "location": person.get("location"),
                    "distance": person.get("distance"),
                }
                new_data.append(record)

            # Add to processed files set
            processed_files.add(file_path)

            # Clean up temporary file
            os.remove(temp_json_path)
            print(f"Processed file: {file_path}")

        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    # If we have new data, process and combine it
    if new_data:
        # Create DataFrame with new data
        new_df = pd.DataFrame(new_data)
        new_df["timestamp"] = pd.to_datetime(new_df["timestamp"])

        # Combine with existing data
        if not existing_df.empty:
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = new_df

        # Remove duplicates from combined data
        print(f"\nBefore removing duplicates: {len(df)} records")
        df = df.drop_duplicates(subset="person_id", keep="first")
        print(f"After removing duplicates: {len(df)} records")

        # Sort by timestamp and keywords
        df = df.sort_values(["timestamp", "keywords"])

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
        print("✅ Updated combined CSV file in GCP bucket")

        # Save updated list of processed files to a temporary file then upload
        temp_processed_output = "/tmp/processed_files.txt"
        with open(temp_processed_output, "w") as f:
            f.write("\n".join(processed_files))

        processed_blob = bucket.blob(processed_files_path)
        processed_blob.upload_from_filename(temp_processed_output)
        print("✅ Updated processed files list in GCP bucket")

        # Clean up temporary files
        os.remove(temp_output_csv)
        os.remove(temp_processed_output)

        print("\nConsolidation complete. All data stored in GCP bucket.")
    else:
        print("\nNo new data to process")


if __name__ == "__main__":
    main()
