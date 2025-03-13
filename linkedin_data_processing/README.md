# LinkedIn Data Processing

This repository contains tools for processing LinkedIn profile data and building a Retrieval-Augmented Generation (RAG) system to search for experts based on natural language queries.

## Overview

The system consists of two main components:

1. **Profile Processing Pipeline** (`process_linkedin_profiles.py`): Extracts, transforms, and loads LinkedIn profile data from raw JSON files to structured formats stored in Google Cloud Storage.

2. **Expert Finder Agent** (`expert_finder_linkedin.py`): A RAG-based search system that uses natural language processing to find and rank LinkedIn experts based on user queries.

## Prerequisites

- Python 3.12
- Google Cloud Platform account with Storage access
- GCP credentials JSON file
- Docker (optional, for containerized execution)

## Docker Installation

### Configuration Requirements

Before running the scripts, you need to configure:

- GCP Bucket Name:
   - Update the `bucket_name` variable in:
     - `process_linkedin_profiles.py`
     - `expert_finder_linkedin.py`
   - Replace with your own GCP bucket name


### Option 1: Using docker-shell script (Recommended)

The easiest way to build and run the container is using the provided shell script:

```bash
# Make sure you're inside the project folder
cd linkedin_data_processing

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
cd linkedin_data_processing

# Build the Docker image
docker build -t linkedin-data-processing .
```


### Running the Docker Container

The container requires your GCP credentials to be mounted as a volume. Run the container in interactive mode:

```bash
docker run -it -v /path/to/your/credentials.json:/app/secrets.json linkedin-data-processing
```

Replace `/path/to/your/credentials.json` with the actual path to your GCP service account key file.

## Profile Processing Pipeline

The `process_linkedin_profiles.py` script handles the extraction and transformation of LinkedIn profile data. After processing the profiles, it sets up a ChromaDB database for future RAG extraction.

### Key Features

- Downloads only unprocessed profiles from GCP
- Extracts structured data from raw LinkedIn profile JSONs
- Derives additional fields like education level and career level
- Uploads processed data back to GCP
- Prepares profiles for semantic search

### Usage

```bash
# Process new LinkedIn profiles
python process_linkedin_profiles.py --action process

# Prepare processed profiles for RAG
python process_linkedin_profiles.py --action prepare_rag

# Demo search for profiles (just to see it is working)
python process_linkedin_profiles.py --action search --query "machine learning experts"

# Run the complete pipeline
python process_linkedin_profiles.py --action all
```

### Command-line Arguments

- `--action`: Choose from `process`, `prepare_rag`, `search`, or `all`
- `--chroma_dir`: Directory to persist ChromaDB data (default: "chroma_db")
- `--query`: Search query for the search action
- `--industry`: Filter by industry
- `--location`: Filter by location
- `--top_k`: Number of results to return (default: 5)
- `--force`: Force processing of all profiles, even if already processed

### Workflow

1. **Download**: The script connects to GCP and downloads only unprocessed LinkedIn profile JSONs.
2. **Extract**: It extracts structured data from the raw JSONs, including:
   - Basic information (name, location, industry)
   - Experience details (current position, company, career history)
   - Education information (degrees, schools, fields of study)
   - Skills, languages, publications, and more
3. **Transform**: The script derives additional fields like:
   - Education level (PhD, Masters, Bachelors, Other)
   - Career level (Executive, Director, Manager, Senior, Other)
   - Total years of experience
4. **Load**: Processed data is uploaded to GCP for storage and future use.
5. **Prepare for RAG**: The script creates text representations of profiles and generates embeddings for semantic search, which are passed to a ChromaDB database.

## Expert Finder Agent

The `expert_finder_linkedin.py` script provides an agentic search system for finding LinkedIn experts based on natural language queries.

### Key Features

- Natural language query parsing
- Advanced filtering capabilities
- Semantic search with ChromaDB
- Reranking for improved relevance
- AI-generated summaries of search results

### Usage

```bash
# Basic search with reranking
python expert_finder_linkedin.py --query "Find me machine learning experts"

# Advanced search with reranking
python expert_finder_linkedin.py --query "Senior data scientists with PhD degrees" 

# Specify ChromaDB directory
python expert_finder_linkedin.py --query "Marketing executives in healthcare" --chroma_dir "my_chroma_db"
```

### Command-line Arguments

- `--query`: Natural language query to find experts (required)
- `--chroma_dir`: Directory where ChromaDB data is persisted (default: "chroma_db")
- `--initial_k`: Number of initial results to retrieve (default: 20)
- `--final_k`: Number of results to return after reranking (default: 5)
- `--project_id`: Google Cloud project ID
- `--location`: Google Cloud region (default: "us-central1")
- `--reranker`: HuggingFace reranker model name (default: "BAAI/bge-reranker-v2-m3")

### Workflow

1. **Query Parsing**: The agent uses Vertex AI's Gemini 1.5 Flash model to parse natural language queries into structured search terms and filters.
2. **Initial Retrieval**: ChromaDB performs semantic search using the all-MiniLM-L6-v2 embedding model to find relevant profiles.
3. **Reranking**: The BAAI/bge-reranker-v2-m3 model reranks the initial results for improved relevance.
4. **Response Generation**: Gemini 1.5 Flash generates a human-friendly summary of the top experts found.

## Technical Decisions

### Embedding Model Selection

We use the `all-MiniLM-L6-v2` model from Sentence Transformers for generating embeddings because:

1. **Balance of Performance and Efficiency**: It provides good semantic understanding while being lightweight (80MB) and fast.
2. **Multilingual Support**: Works well with professional terminology across different languages.
3. **Proven Effectiveness**: Widely used for semantic search applications with strong performance on benchmark datasets.

### Reranking Approach

The two-stage retrieval process (initial retrieval + reranking) was chosen because:

1. **Improved Precision**: Reranking significantly improves the relevance of search results by considering the full context of both query and profile.
2. **Computational Efficiency**: Allows us to cast a wider net initially (20 results) and then focus computational resources on refining the most promising candidates.
3. **Complementary Strengths**: The embedding model is optimized for recall, while the reranker is optimized for precision.

### ChromaDB as Vector Database

ChromaDB was selected as our vector database because:

1. **Simplicity**: Easy to set up and use with a Python-native API.
2. **Persistence**: Supports local persistence without requiring a separate database server.
3. **Filtering Capabilities**: Provides robust metadata filtering alongside vector search.
4. **Performance**: Efficient for collections of thousands of profiles.

### Vertex AI Integration

We use Google's Vertex AI with the Gemini 1.5 Flash model for:

1. **Query Understanding**: Accurately parses natural language queries into structured search parameters.
2. **Result Summarization**: Generates concise, informative summaries of search results.
3. **Cost Efficiency**: Gemini 1.5 Flash offers a good balance of performance and cost for this application.

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Process new LinkedIn profiles
python process_linkedin_profiles.py --action process

# 2. Prepare processed profiles for RAG
python process_linkedin_profiles.py --action prepare_rag

# 3. Search for experts using the Expert Finder Agent
python expert_finder_linkedin.py --query "Find me senior machine learning engineers who also have a PHD"
```

## Advanced Usage

### Custom Filtering

The Expert Finder Agent supports advanced filtering through natural language:

```bash
# Find experts with specific education level
python expert_finder_linkedin.py --query "Data scientists with PhD degrees"

# Find experts in specific locations
python expert_finder_linkedin.py --query "Computer Vision experts in San Francisco or New York"

# Find experts with minimum experience
python expert_finder_linkedin.py --query "AI experts with at least 5 years of experience"

# Combine multiple filters
python expert_finder_linkedin.py --query "NLP experts who hold C-level positions in New York"
```

## Limitations and Future Work

- The reranking model requires significant memory. A more efficient model could be used for resource-constrained environments.
- The reranking model must be hosted by the running container or machine, and takes a long time to download for a first-time use.

## Troubleshooting

- **ChromaDB SQLite Error**: If you encounter a SQLite version error, make sure you're using a compatible version of SQLite (≥ 3.35.0). The Dockerfile has been configured to use a compatible version.
- **GCP Authentication**: Ensure your credentials file is correctly set up and the environment variable is properly configured.
- **Memory Issues**: If you encounter memory issues with large collections, try reducing the `initial_k` parameter or using a smaller embedding model.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
