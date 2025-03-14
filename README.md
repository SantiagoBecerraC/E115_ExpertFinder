# ExpertFinder - Milestone 2
**Team Members:** Santiago Becerra, Umapathy Bhakthavatsulu, Jinyu Han

For this milestone, our expert finder system is using LinkedIn and Google Scholar data, and advanced LLM techniques to process user queries and identify relevant experts across multiple domains. The system combines data from various professional and academic sources, using RAG (Retrieval-Augmented Generation) for effective expert search and ranking.

## System Components

### LinkedIn Data Pipeline

The LinkedIn component consists of two main parts:

1. **[Data Extraction](./linkedin_raw_data)**: 
   - Extracts user profiles using the unofficial LinkedIn API
   - Supports keyword and region-based searching
   - Consolidates and stores data in GCP
   - Includes rate limiting protection
   
2. **[Data Processing](./linkedin_data_processing)**:
   - Processes raw LinkedIn profiles into structured formats
   - Implements RAG-based expert search system
   - Uses ChromaDB for vector storage and retrieval
   - Features advanced filtering and reranking capabilities

### [Google Scholar Data Pipeline](./backend)

The backend provides additional data sources and processing capabilities:

- **Google Scholar Integration**: Collects and processes academic profile data
- **Agent System**: LLM-powered agents for intelligent expert finding
- **Vector Search**: ChromaDB integration for efficient similarity search

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Google Cloud Platform account with Storage access
- GCP credentials JSON file
- OpenAI API key (for LLM functionality)

## Installation & Setup

Each component has its own detailed installation and setup guide:

- [LinkedIn Data Extraction Setup](./linkedin_raw_data/README.md#docker-setup)
- [LinkedIn Data Processing Setup](./linkedin_data_processing/README.md#docker-installation)
- [Backend Services Setup](./backend/README.md#getting-started)

## Architecture

The system uses a modular architecture with the following key components:

1. **Data Collection Layer**:
   - LinkedIn profile extraction
   - Google Scholar data collection

2. **Processing Layer**:
   - Profile structuring and enrichment
   - Vector embedding generation
   - Semantic search capabilities

3. **Search Layer**:
   - RAG-based expert finding
   - Multi-source data integration
   - Advanced filtering and ranking

4. **Storage Layer**:
   - Google Cloud Storage for raw data
   - ChromaDB for vector storage
   - Structured data persistence

## Key Features

- Multi-source expert data collection
- Advanced semantic search capabilities
- Natural language query processing
- Intelligent result ranking and filtering
- Scalable data processing pipeline
- Docker-based deployment
- GCP integration for storage and processing

## Development Workflow

1. **Data Collection**:
   - Extract LinkedIn profiles
   - Gather Google Scholar data
   - Collect PubMed publications

2. **Data Processing**:
   - Structure and clean raw data
   - Generate embeddings
   - Prepare for RAG system

3. **Expert Search**:
   - Process natural language queries
   - Perform semantic search
   - Rank and filter results
   - Generate result summaries

# Next Steps
Right now, both data sources have their own independent RAG workflow. Fur future milestones, we want to integrate both data sources to have a more comprehensive and robust expert list, improving the reliability of the results.

# Data Version Control Strategy
## Overview - Data Evolution Plan
- Initial Dataset: Track the baseline collection of LinkedIn and Google Scholar profiles.
- Incremental Updates, add new expert profiles as we perform additional searches: the baseline dataset will increase overtime, but there will be no modification to the raw data. This is the case as we do not anticipate the APIs having any significant change to their output structure, which is why the raw data will only increase when we scrape new profiles and fetch new articles, but the underlying structure of this data will not change.
- Metadata Enhancements: Improve profile metadata for better filtering capabilities: we will track the changes to the metadata in a simple json file, indicating the structure of the metadata as we improve it.
- Dataset Merging: This is perhaps the most important data change we anticipate, once we are able to combine both datasets we have right now (LinkedIn and Google Scholar) for enhanced and better retrieval.

## Benefits
- Maintain reproducibility across all data processing steps
- Track data lineage as the expert database grows
- Enable easy rollback to previous dataset versions if needed
- Optimize storage by tracking only changes between versions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LinkedIn API integration based on unofficial API implementations
- Vector search powered by ChromaDB
- LLM capabilities provided by OpenAI and Google Vertex AI
