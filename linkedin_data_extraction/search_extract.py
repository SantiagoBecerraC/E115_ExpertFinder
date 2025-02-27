import os
import glob
import pandas as pd
import json


# First, try to load existing combined data
combined_csv_path = "linkedin_data_extraction/data/combined_linkedin_searches.csv"
processed_files_path = "linkedin_data_extraction/data/processed_files.txt"

# Load existing data if available
if os.path.exists(combined_csv_path):
    existing_df = pd.read_csv(combined_csv_path)
    print(f"Loaded existing data with {len(existing_df)} records")
else:
    existing_df = pd.DataFrame()
    print("No existing data found")

# Load list of previously processed files
processed_files = set()
if os.path.exists(processed_files_path):
    with open(processed_files_path, 'r') as f:
        processed_files = set(f.read().splitlines())
    print(f"Found {len(processed_files)} previously processed files")

# Get all JSON files and filter out already processed ones
all_search_files = glob.glob("linkedin_data_extraction/data/keyword_searches/search_*.json")
new_files = [f for f in all_search_files if f not in processed_files]
print(f"Found {len(new_files)} new files to process")

# List to store new data
new_data = []

# Process each new file
for file_path in new_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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
    
    # Save updated data
    df.to_csv(combined_csv_path, index=False)
    
    # Save updated list of processed files
    with open(processed_files_path, 'w') as f:
        f.write('\n'.join(processed_files))
    
    print("\nUpdated data and processed files list saved")
else:
    print("\nNo new data to process")