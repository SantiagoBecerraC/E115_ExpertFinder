# ExpertFinder

Expert finder system using LinkedIn data, Google Scholar, PubMed, and advanced LLM techniques to process user queries and identify relevant experts across multiple domains. The system combines data from various professional and academic sources, using RAG (Retrieval-Augmented Generation) and clustering algorithms for effective expert search and ranking.

## System Components

### [LinkedIn Data Pipeline](./linkedin_raw_data)

The LinkedIn component consists of two main parts:

1. **Data Extraction**: 
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
- **PubMed Integration**: Analyzes scientific publications and author data
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
   - PubMed publication analysis

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LinkedIn API integration based on unofficial API implementations
- Vector search powered by ChromaDB
- LLM capabilities provided by OpenAI and Google Vertex AI