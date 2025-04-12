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

### Option 1: Using docker-shell script (Recommended)

The easiest way to build and run the container is using the provided shell script:

```bash
# Make sure you're inside the project folder
cd linkedin_raw_data

# Run the script
sh docker-shell.sh
```

The script will:
1. Build the Docker image automatically
2. Prompt for your GCP credentials file path (with a default option)
3. Mount both the credentials and the current directory
4. Run the container in interactive mode

### Option 2: Manual Docker Commands

#### Building the Docker Image

Build the Docker image from the project directory:

```bash
# Navigate to the project directory
cd linkedin_raw_data

# Build the Docker image
docker build -t linkedin-raw-data .
```


### Running the Docker Container

The container requires your GCP credentials to be mounted as a volume. Run the container in interactive mode:

```bash
docker run -it -v /path/to/your/credentials.json:/app/secrets.json linkedin-raw-data
```

Replace `/path/to/your/credentials.json` with the actual path to your GCP service account key file.

## Usage

### Search for LinkedIn Profiles

```bash
# Inside the Docker container
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
# Inside the Docker container
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
