# Expert Finder API

This is the backend API for the Expert Finder application, which provides endpoints to search for experts from various sources.

## Setup

Run the Docker shell script to set up the environment:
```bash
sh docker-shell.sh
```

## Running the Application Locally

Start the FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`


## LinkedIn Data Processing Pipeline

The Expert Finder includes a complete LinkedIn data processing pipeline that handles:

1. Processing raw LinkedIn profiles
2. Calculating credibility scores
3. Vectorizing profiles for semantic search
4. Storing profiles in ChromaDB

To run the full pipeline:

```bash
python -m linkedin_data_processing.cli pipeline [--force] [--query "optional search query"]
```

Available commands:
- `process`: Process LinkedIn profiles and upload to GCP
- `vectorize`: Vectorize processed profiles into ChromaDB
- `search`: Search for experts matching a query
- `pipeline`: Run the entire processing pipeline
- `reset`: Reset the ChromaDB collection
- `update-credibility-stats`: Update the credibility statistics

## Google Scholar Data Processing Pipeline

The Expert Finder also includes a Google Scholar data processing pipeline for extracting and processing academic information:

```bash
python -m google_scholar.cli pipeline --query "your search query" [options]
```

Available commands:
- `download`: Download scholar data based on a search query
- `process`: Process downloaded scholar data
- `vectorize`: Vectorize processed data into ChromaDB
- `test`: Test a query on vectorized data
- `pipeline`: Run the entire pipeline (download, process, vectorize)
- `archive`: Archive data to GCP storage

Options:
- `--query`: (Required for download/test/pipeline) Search query
- `--start-year`/`--end-year`: Year range for filtering (default: 2022-2025)
- `--num-results`: Total results to fetch (default: 20)
- `--results-per-page`: Results per page (default: 10, max: 20)
- `--input-file`: (For process) Specific JSON file to process
- `--collection`: ChromaDB collection name (default: "google_scholar")
- `--n-results`: (For test) Number of results to return (default: 5)
- `--doc-type`: Filter by document type (author, website_content, journal_content)
- `--bucket`: (For archive) GCP bucket name for archiving
- `--prefix`: (For archive) Prefix for files in GCP bucket
- `--local-dir`: (For archive) Local directory to archive
- `--remove-local`: (For archive) Remove local files after successful archival

## Credibility Scoring System

Expert Finder includes a dynamic credibility scoring system that:

1. Evaluates experts based on multiple metrics including:
   - Years of experience
   - Education level
   - Role seniority

2. Provides a 1-5 credibility level based on percentile ranking
   - Level 5: Top 5% of experts
   - Level 4: Next 15% (80-95th percentile)
   - Level 3: Next 30% (50-80th percentile)
   - Level 2: Next 30% (20-50th percentile)
   - Level 1: Bottom 20%

3. Calculates scores on-demand using database-wide statistics

## API Endpoints

### GET /
Welcome message endpoint that provides API information and available endpoints.

### POST /search
Search for experts across all sources based on a query.

### POST /scholar_search
Search specifically for Google Scholar experts.

### POST /linkedin_search
Search specifically for LinkedIn experts.

### POST /api/data/version
Version the ChromaDB database using DVC after significant updates.

### GET /api/data/versions
Get the version history of the ChromaDB database.

### POST /api/data/restore/{commit_hash}
Restore the ChromaDB database to a specific version.

### POST /api/data/update_credibility_stats
Update the credibility statistics from the current database.

### Request Body (for search endpoints)
```json
{
    "query": "your search query",
    "max_results": 5  // optional, defaults to 5
}
```

### Response Example
```json
{
    "experts": [
        {
            "id": "unique_id",
            "name": "Expert Name",
            "title": "Expert Title",
            "source": "linkedin|scholar",
            "company": "Company Name",  // for LinkedIn
            "location": "Location",     // for LinkedIn
            "skills": ["skill1", "skill2"],  // for LinkedIn
            "citations": 1000,         // for Google Scholar
            "interests": ["interest1", "interest2"],  // for Google Scholar
            "publications": 25,        // for Google Scholar
            "summary": "Expert summary",
            "credibility_level": 4,    // 1-5 scale (LinkedIn only)
            "credibility_percentile": 85.5, // percentile rank (LinkedIn only)
            "years_experience": 10     // years of experience (LinkedIn only)
        }
    ],
    "total": 1,
    "source": "linkedin|scholar"  // or combined statistics for /search
}
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc` 

## Testing

The backend includes a comprehensive testing suite to ensure reliability and functionality:

```bash
# Run unit tests with coverage reporting
python -m pytest tests/unit/ --cov=. --cov-config=../.coveragerc --cov-report=term-missing
```

Set these environment variables when running tests:
```bash
export GCP_PROJECT=dummy
export EF_TEST_MODE=1
export PYTHONPATH=.
```

For detailed testing documentation, refer to [testing_readme.md](docs/testing_readme.md). 