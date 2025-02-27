import pandas as pd
import time
import random
import json
import os
from datetime import datetime
from linkedin_api import Linkedin

# Authenticate using any Linkedin user account credentials
api = Linkedin('3chamois-bifocal@icloud.com', 'cinnyn-surfix-8Cejji')

# Create directory if it doesn't exist
profile_dir = "linkedin_data_extraction/data/profiles"
os.makedirs(profile_dir, exist_ok=True)

# Read the combined CSV file
df = pd.read_csv("linkedin_data_extraction/data/combined_linkedin_searches.csv")

# Load list of already processed URNs
processed_urns_file = "linkedin_data_extraction/data/processed_profile_urns.txt"
processed_urns = set()
if os.path.exists(processed_urns_file):
    with open(processed_urns_file, 'r') as f:
        processed_urns = set(f.read().splitlines())
    print(f"Found {len(processed_urns)} previously processed profiles")

# Get list of URNs to process (excluding already processed ones)
urns_to_process = set(df['person_id'].unique()) - processed_urns
print(f"Found {len(urns_to_process)} new profiles to process")

# Process each URN
for urn in urns_to_process:
    try:
        # Random delay between 3-7 seconds to avoid rate limiting
        delay = random.uniform(3, 7)
        time.sleep(delay)
        
        # Get the profile
        profile = api.get_profile(urn_id=urn)
        
        # Create filename using URN
        filename = f"{profile_dir}/{urn}.json"
        
        # Save profile data
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                'urn_id': urn,
                'fetch_timestamp': datetime.now().isoformat(),
                'profile_data': profile
            }, f, indent=4, ensure_ascii=False)
        
        # Add to processed URNs
        processed_urns.add(urn)
        
        # Periodically save processed URNs list (every 10 profiles)
        if len(processed_urns) % 10 == 0:
            with open(processed_urns_file, 'w') as f:
                f.write('\n'.join(processed_urns))
            
        print(f"Saved profile for URN: {urn}")
        
    except Exception as e:
        print(f"Error processing URN {urn}: {str(e)}")
        # Optionally log errors to a separate file
        with open(f"{profile_dir}/errors.txt", "a") as f:
            f.write(f"{datetime.now().isoformat()}: Error with URN {urn}: {str(e)}\n")

# Save final list of processed URNs
with open(processed_urns_file, 'w') as f:
    f.write('\n'.join(processed_urns))

print(f"\nProcessing complete. Total profiles processed: {len(processed_urns)}")