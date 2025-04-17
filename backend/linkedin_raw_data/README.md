# LinkedIn Data Extraction

This project contains code for extracting and analyzing data from LinkedIn using the unofficial LinkedIn API. It allows searching and retrieving information about LinkedIn users based on various criteria like keywords, location, and job titles.

## Features

- Search for LinkedIn users based on:
  - Keywords (e.g., skills, job titles)
  - Geographic regions
  - Current/past companies
  - Industries
  - Schools
  - And more search parameters

- Extract user profile information including:
  - Name
  - Current job title
  - Location
  - Network distance
  - Unique identifier (URN)
  - Detailed profile data

- GCP Integration:
  - Store search results in Google Cloud Storage
  - Consolidate search data into a single dataset
  - Store detailed profile information

## Docker Setup

### Configuration Requirements

Before running the scripts, you need to configure:

1. GCP Bucket Name:
   - Update the `bucket_name` variable in:
     - `get_profiles_gcp.py`
     - `consolidate_people_gcp.py`
     - `search_profiles_gcp.py`
   - Replace with your own GCP bucket name

2. LinkedIn Credentials (Optional):
   - To use your own LinkedIn account for testing:
     - Update credentials in `get_profiles_gcp.py` (line 44)
     - Update credentials in `search_profiles_gcp.py` (line 183)
   - ⚠️ Warning: Be mindful of LinkedIn's rate limiting when using your credentials
   - *Note: a better implementation to test with your own credentials will be added in future MS*
```
## Usage

### Search for LinkedIn Profiles

```bash
python search_profiles_gcp.py keyword1 keyword2 ... [--region REGION_CODE]
```

Examples:
```bash
# Search with keywords in default region (USA)
python search_profiles_gcp.py machine learning data science

# Search with keywords in a specific region (UK)
python search_profiles_gcp.py machine learning data science --region 101452733

# Show help and available regions
python search_profiles_gcp.py --help
```

### Consolidate Search Results

```bash
python consolidate_people_gcp.py
```

This script:
- Processes new search files and extracts user information
- Combines data into a single CSV file
- Uploads the consolidated data back to GCP

### Extract Detailed Profile Information

```bash
# Inside the Docker container
python get_profiles_gcp.py
```

This script:
- Reads the consolidated CSV file
- Retrieves detailed profile information for each user
- Saves individual profile data as JSON files in GCP
- Tracks processed profiles to avoid duplicates


## GCP Integration

The project uses Google Cloud Storage to store and manage LinkedIn data:

1. Search results are stored in the GCP bucket
2. Consolidated data is stored in the GCP bucket
3. Authentication uses service account credentials mounted as a volume

## Requirements

All requirements are included in the Docker image. If running locally:

- Python 3.12
- pandas
- linkedin_api
- google-cloud-storage

## Note

This project uses the unofficial LinkedIn API. Please ensure you comply with LinkedIn's terms of service and rate limits when using this code.

## Disclaimer

This code is for educational purposes only. Users are responsible for ensuring their use of the LinkedIn API complies with LinkedIn's terms of service and applicable laws.
