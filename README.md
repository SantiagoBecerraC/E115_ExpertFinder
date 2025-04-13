# ExpertFinder - Milestone 3

Expert finder system using LinkedIn and Google Scholar data and advanced LLM techniques to process user queries and identify relevant experts across multiple domains. The system uses RAG (Retrieval-Augmented Generation) for effective expert search and ranking.

## Updates in Milestone 3

### New Features:
1. **Web Frontend Interface**: 
   - Added a modern, responsive Next.js frontend for an intuitive user experience
   - Implemented tabbed interface for viewing experts from different sources
   - Designed mobile-friendly UI with real-time search capabilities

2. **LLM Fine-tuning**: 
   - Trained a custom Gemini model specifically for expert finding tasks
   - Generated specialized dataset for training with expert profiles

## System Components

### [Backend Services](./backend)

The backend contains several key components:

1. **LinkedIn Data Pipeline**:
   
   a. **[Data Extraction](./backend/linkedin_raw_data)**:
   - Extracts user profiles using the unofficial LinkedIn API
   - Supports keyword and region-based searching
   - Consolidates and stores data in GCP
   - Includes rate limiting protection
   
   b. **[Data Processing](./backend/linkedin_data_processing)**:
   - Processes raw LinkedIn profiles into structured formats
   - Implements RAG-based expert search system
   - Uses ChromaDB for vector storage and retrieval
   - Features advanced filtering and reranking capabilities

2. **[Google Scholar Integration](./backend/google_scholar)**:
   - Collects and processes academic profile data
   - Agent System: LLM-powered agents for intelligent expert finding
   - Vector Search: ChromaDB integration for efficient similarity search

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Google Cloud Platform account with Storage access
- GCP credentials JSON file
- OpenAI API key (for LLM functionality)
- Node.js 18+ (for frontend development)

## Installation & Setup

Each component has its own detailed installation and setup guide:

- [LinkedIn Data Extraction Setup](./backend/linkedin_raw_data/README.md#docker-setup)
- [LinkedIn Data Processing Setup](./backend/linkedin_data_processing/README.md#docker-installation)
- [Backend Services Setup](./backend/README.md#getting-started)
- [Frontend Setup](./frontend/README.md#getting-started)
- [LLM Fine-tuning Setup](./backend/llm-finetuning/README.md#prerequisites)

## Starting the Services

### Backend Services
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Start the backend services:
   ```bash
   ./docker-shell.sh
   ```
   This will start:
   - LinkedIn data processing service
   - Google Scholar integration
   - API server
   - ChromaDB vector database

3. Verify services are running:
   ```bash
   docker compose ps
   ```

### Frontend Application
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the frontend container:
   ```bash
    ./docker-shell.sh
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Codebase Architecture

```
ExpertFinder/
├── backend/
│   ├── agent/                 # LLM-powered agent system
│   │   ├── scholar_agent.py   # Google Scholar expert finder
│   │   └── test_scholar_agent.py
│   ├── linkedin_data_processing/
│   │   ├── expert_finder_linkedin.py    # LinkedIn expert search
│   │   ├── process_linkedin_profiles.py # Profile processing
│   │   └── credibility_system.py        # Profile verification
│   ├── linkedin_raw_data/     # LinkedIn data extraction
│   ├── google_scholar/        # Scholar data collection
│   ├── llm-finetuning/        # Model fine-tuning
│   └── utils/                 # Shared utilities
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── styles/           # CSS and styling
│   ├── public/               # Static assets
│   └── Dockerfile            # Frontend container
├── chroma_db/                # Vector database storage
│   ├── embeddings/           # Stored embeddings
│   └── metadata/             # Search metadata
├── secrets/                  # Secure configuration
│   ├── .env                  # Environment variables
│   ├── gcp_credentials.json  # GCP access
│   └── api_keys/             # API credentials
└── docker-compose.yml        # Main service orchestration
```

### Key Components:

1. **Backend Services**:
   - `agent/`: LLM-powered expert finding agents
   - `linkedin_data_processing/`: Profile processing and search
   - `google_scholar/`: Academic data integration
   - `llm-finetuning/`: Custom model training

2. **Frontend Application**:
   - Next.js-based web interface
   - React components for expert display
   - Real-time search functionality
   - Responsive design with TailwindCSS

3. **Data Processing Pipeline**:
   - LinkedIn profile extraction and processing
   - Google Scholar data collection
   - Vector embedding generation
   - RAG-based search implementation

4. **Container Configuration**:
   - Separate Dockerfiles for each service
   - Docker Compose for orchestration
   - Environment-specific configurations
   - Volume management for persistence

5. **Data Storage**:
   - `chroma_db/`: Vector database for semantic search
   - Persistent storage for embeddings and metadata
   - Optimized for similarity search operations

6. **Security**:
   - `secrets/`: Secure storage for credentials
   - Environment configuration
   - API keys and access tokens
   - GCP service account credentials

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
   - Fine-tuned LLM for response generation

4. **Storage Layer**:
   - Google Cloud Storage for raw data
   - ChromaDB for vector storage
   - Structured data persistence

5. **Presentation Layer**:
   - Next.js frontend application
   - Responsive UI components
   - Source-specific expert displays

## Key Features

- Multi-source expert data collection
- Advanced semantic search capabilities
- Natural language query processing
- Intelligent result ranking and filtering
- Custom-tuned LLM for domain-specific responses
- Modern web interface for intuitive user experience
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
   - Generate result summaries with fine-tuned LLM

4. **Frontend Development**:
   - Implement React components
   - Connect to backend API
   - Style with TailwindCSS
   - Ensure responsive design

5. **LLM Fine-tuning**:
   - Generate specialized QA dataset
   - Train model on Vertex AI
   - Integrate model with expert search system
   - Monitor performance and results

# Next Steps
Right now, both data sources have their own independent RAG workflow. For future milestones, we want to:

1. Further integrate data sources for a more comprehensive and robust expert list
2. Enhance the frontend with additional visualization capabilities
3. Expand fine-tuning efforts to improve expert characterization
4. Add real-time collaboration features for team-based expert finding

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LinkedIn API integration based on unofficial API implementations
- Vector search powered by ChromaDB
- LLM capabilities provided by OpenAI and Google Vertex AI