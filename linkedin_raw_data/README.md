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
  - Sync local files with GCP bucket
  - Consolidate search data into a single dataset

## Usage

### Search for LinkedIn Profiles

```bash
python linkedin_raw_data/search_profiles_gcp.py keyword1 keyword2 ... [--region REGION_CODE]
```

Examples:
```bash
# Search with keywords in default region (USA)
python linkedin_raw_data/search_profiles_gcp.py machine learning data science

# Search with keywords in a specific region (UK)
python linkedin_raw_data/search_profiles_gcp.py machine learning data science --region 101452733

# Show help and available regions
python linkedin_raw_data/search_profiles_gcp.py --help
```

### Consolidate Search Results

```bash
python linkedin_raw_data/consolidate_people_gcp.py
```

This script:
- Syncs with GCP bucket to get the latest search files
- Processes new search files and extracts user information
- Combines data into a single CSV file
- Uploads the consolidated data back to GCP

### Extract Detailed Profile Information

```bash
python linkedin_raw_data/get_profiles.py
```

This script:
- Reads the consolidated CSV file
- Retrieves detailed profile information for each user
- Saves individual profile data as JSON files
- Tracks processed profiles to avoid duplicates

## GCP Integration

The project uses Google Cloud Storage to store and manage LinkedIn data:

1. Search results are stored in the GCP bucket
2. Local and GCP files are synchronized
3. Consolidated data is stored in the GCP bucket
4. Authentication uses service account credentials

## Requirements

- Python 3.x
- pandas
- linkedin_api
- google-cloud-storage
- google-auth

## Installation

```bash
pip install pandas numpy linkedin_api google-cloud-storage google-auth
```

## Note

This project uses the unofficial LinkedIn API. Please ensure you comply with LinkedIn's terms of service and rate limits when using this code.

## Disclaimer

This code is for educational purposes only. Users are responsible for ensuring their use of the LinkedIn API complies with LinkedIn's terms of service and applicable laws.