# DVC (Data Version Control) in Expert Finder

This document explains how Data Version Control (DVC) is implemented in the Expert Finder project for managing and versioning ChromaDB vector databases.

## Overview

DVC is used to version control the ChromaDB database containing expert profile embeddings. This allows:
- Tracking changes to the vector database over time
- Reverting to previous versions when needed
- Sharing database versions between team members
- Storing large data files outside of Git (in Google Cloud Storage)

## Setup

1. DVC is already configured in this project with Google Cloud Storage as the remote storage backend.

2. To use DVC, make sure you have the required dependencies:
```bash
pip install dvc dvc-gs
```

3. The DVC remote is configured to use the following Google Cloud Storage bucket:
```
gs://expert-finder-bucket-1/dvc-store
```

4. To authenticate with Google Cloud, set up your credentials:
```bash
# Option 1: Use application default credentials
gcloud auth application-default login

# Option 2: Set GOOGLE_APPLICATION_CREDENTIALS environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Custom DVC Integration Functions

The project includes several custom functions that integrate ChromaDB with DVC:

### ChromaDBManager Integration Methods

#### Document Addition Methods Comparison

The project provides two methods for adding documents to ChromaDB, with different versioning capabilities:

##### `add_documents`
```python
def add_documents(self, documents: List[str], ids: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
```
- Basic method that adds documents to ChromaDB **without** DVC versioning
- Handles validation, batching, and error handling
- Perfect for frequent, small updates where versioning each change is unnecessary

##### `add_documents_with_version`
```python
def add_documents_with_version(
    self,
    documents: List[str],
    ids: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    update_info: Optional[Dict[str, Any]] = None,
    version_after_batch: bool = False
) -> bool:
```
- Enhanced method that adds documents and optionally creates a DVC version
- Internally calls `add_documents` to handle the actual document addition
- Adds version control through the additional parameters:
  - `version_after_batch`: Controls whether to create a version after adding documents
  - `update_info`: Metadata for the DVC commit message (source, profiles_added, etc.)
- Returns a boolean success indicator

**Key differences:**
- `add_documents` is focused purely on ChromaDB operations
- `add_documents_with_version` extends this functionality with optional DVC integration
- `add_documents_with_version` allows controlled versioning based on the `version_after_batch` flag

**Example usage:**
```python
# Without versioning - use for frequent, small updates
db_manager.add_documents(
    documents=["Document content 1", "Document content 2"],
    ids=["doc1", "doc2"],
    metadatas=[{"source": "linkedin"}, {"source": "linkedin"}]
)

# With versioning - use after significant updates
db_manager.add_documents_with_version(
    documents=["Document content 1", "Document content 2"],
    ids=["doc1", "doc2"],
    metadatas=[{"source": "linkedin"}, {"source": "linkedin"}],
    update_info={"source": "linkedin", "profiles_added": 2},
    version_after_batch=True  # This triggers DVC versioning
)
```

#### `import_linkedin_profiles` and `import_google_scholar_data`
Methods that import profile data from different sources with built-in DVC versioning:

```python
# LinkedIn import with versioning
count = db_manager.import_linkedin_profiles(
    data_path=data_path,
    create_version=True  # Enable DVC versioning
)

# Google Scholar import with versioning
authors_count, articles_count = db_manager.import_google_scholar_data(
    data_path=data_path,
    create_version=True  # Enable DVC versioning
)
```

#### `restore_database_version`
Wrapper method that uses the DVCManager to restore a specific version of the database:

```python
success = db_manager.restore_database_version(commit_hash)
```

### Testing Functions

The project includes test scripts for verifying DVC functionality:

- `test_dvc_integration.py`: Dedicated test script for DVC and ChromaDB integration
- `test_versioning()` in `test_chromadb.py`: Tests DVC versioning and restoration

Example test command:
```bash
python test_chromadb.py --versioning
```

### Command-Line Interface

You can run versioning operations from the CLI via the test scripts:

```bash
# Test DVC integration
python test_dvc_integration.py

# Test ChromaDB with DVC versioning
python test_chromadb.py --versioning
```

## API Endpoints for DVC Operations

The Expert Finder API provides endpoints to interact with DVC:

### POST /api/data/version
Create a new version of the database.

Request body:
```json
{
    "source": "google_scholar",
    "profiles_added": 50,
    "description": "Added new ML experts from Google Scholar"
}
```

### GET /api/data/versions
Get the version history of the database.

Query parameters:
- `max_entries`: Maximum number of versions to return (default: 10)

Response:
```json
{
    "versions": [
        {
            "commit_hash": "a1b2c3d4e5f6",
            "date": "2023-04-01 14:30:00",
            "message": "Update vector database with 50 profiles from google_scholar"
        },
        ...
    ]
}
```

### POST /api/data/restore/{commit_hash}
Restore the database to a specific version.

Path parameters:
- `commit_hash`: The Git commit hash of the version to restore

## Implementation Details

### Architecture

- `DVCManager` (`utils/dvc_utils.py`): Core class that handles all DVC operations
- Integration with ChromaDB through `ChromaDBManager` (`utils/chroma_db_utils.py`)
- API endpoints in `main.py` expose the versioning functionality

### Key Features

1. **Automatic Initialization**: DVC is automatically initialized if not already set up.

2. **Smart Versioning**: Only creates new versions after significant changes to avoid version bloat.

3. **Batched Updates**: The `add_documents_with_version` method allows controlling when versioning happens.

4. **Remote Storage**: Automatically pushes changes to Google Cloud Storage.

5. **Informative Commit Messages**: Each version includes metadata about the update (source, number of profiles, etc.).

### Best Practices

1. **When to Create Versions**:
   - After importing a significant batch of new profiles (e.g., 50+ profiles)
   - After making major changes to the embedding model
   - Before any significant database schema changes

2. **Using Version Tags**:
   - For important milestones, add a Git tag:
     ```bash
     git tag -a v1.0-database -m "Initial database with 1000 profiles"
     ```

3. **Restoring Data Safely**:
   - Create a new branch before restoring to avoid losing current state:
     ```bash
     git checkout -b restore-experiment
     # Then use the API or DVC commands to restore
     ```

## Troubleshooting

### Common Issues

1. **Cannot push to remote storage**:
   - Check Google Cloud authentication
   - Verify you have write permissions to the bucket

2. **DVC files not being tracked by Git**:
   - Ensure you add the DVC files to Git after creating a version:
     ```bash
     git add chromadb.dvc
     git commit -m "Update database version"
     ```

3. **Cannot restore specific version**:
   - Check if you have the specific commit hash in your Git history
   - Ensure you have pulled all DVC data with `dvc pull`

## Additional Resources

- [DVC Documentation](https://dvc.org/doc)
- [DVC with Google Cloud Storage](https://dvc.org/doc/user-guide/data-management/remote-storage/google-cloud-storage)
- [Version Control for ML Projects](https://dvc.org/doc/use-cases/versioning-data-and-models) 