# ExpertFinder

## Team Members - Jinyu Han, Santiago Becerra Cordoba, Umapathy (Umy) Bhakthavatsulu
## Project Advisor - Rashmi Banthia 

In today's digital age, the proliferation of misinformation has become a significant challenge. With the vast amount of online information, it is increasingly difficult for individuals to identify credible sources and trusted experts. This issue is exacerbated by biased or misleading content, which can quickly spread through social media and other online platforms. As a result, there is a growing need for a reliable tool that can help users find and verify expert opinions on various topics. Our project aims to address this problem by developing an intuitive expert search tool that leverages Large Language Models (LLMs) to identify and rank credible experts based on their online presence and contributions.

Expert finder system using LinkedIn and Google Scholar data and advanced LLM techniques to process user queries and identify relevant experts across multiple domains. The system uses RAG (Retrieval-Augmented Generation) for effective expert search and ranking.

### Key Features
- Multi-source expert data collection
- Advanced semantic search capabilities
- Natural language query processing
- Intelligent result ranking and filtering
- Custom-tuned LLM for domain-specific responses
- Modern web interface for intuitive user experience
- Scalable data processing pipeline
- Docker-based deployment to kubernetes 
- GCP integration for storage and processing

### Architecture
   - [Solution Architecture](/images/ExpertFinder-Solution-Architecture.pdf)
   - [Application Architecture](/images/ExpertFinder-Application-Architecture.png)
   - [Frontend Design](/images/ExpertFinder-Frontend-Design.png)
   
### Backend API
   - Built using FastAPI with comprehensive type validation using Pydantic models
   - RESTful API endpoints for expert search and profile retrieval
   - [API Documentation](/images/ExpertFinder-API.png)
   - Advanced filtering capabilities for location, industry, and experience
   - Real-time credibility scoring and ranking system
   - Integration with ChromaDB for semantic search functionality

### Web Frontend Interface
   - Added a modern, responsive Next.js frontend for an intuitive user experience
   - Implemented tabbed interface for viewing experts from different sources
   - Designed mobile-friendly UI with real-time search capabilities
   - Interactive expert cards with detailed profile information
   - Credibility score visualization with tooltips
   - Dynamic filtering and sorting options
   - Real-time search with instant results
   
### Data Versioning and Tracking
   - Implemented DVC for version controlling the ChromaDB database
   - Tracks significant database updates rather than individual profile additions
   - Maintains version history with commit hashes and metadata
   - Supports database restoration to previous versions

### Data Processing Pipeline
   - LinkedIn profile extraction and processing
   - Google Scholar data collection
   - Vector embedding generation
   - RAG-based search implementation

### LLM Fine-tuning
   - Generate specialized QA dataset
   - Train model on Vertex AI
   - Integrate model with expert search system
   - Monitor performance and results

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Google Cloud Platform account with Storage access
- GCP credentials JSON file
- OpenAI API key (for LLM functionality)
- Cohere API key (for LLM Reranking functionality)
- Node.js 18+ (for frontend development)

## Installation & Setup

Each component has its own detailed installation and setup guide:

- [Backend](./backend/README.md#getting-started)
- [Frontend](./frontend/README.md#getting-started)
- [LLM Fine-tuning](./llm-finetuning/README.md#getting-started)
- [Kubernetes Deployment](./deployment/README.md)

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
│   │   ├── dynamic_credibility.py       # Dynamic credibility scoring
│   │   └── credibility_system.py        # Profile verification
│   ├── linkedin_raw_data/     # LinkedIn data extraction
│   ├── google_scholar/        # Scholar data collection
│   ├── chromaDBtest/          # ChromaDB testing and configuration
│   ├── utils/                 # Shared utilities
│   │   ├── chroma_db_utils.py # ChromaDB management
│   │   └── dvc_utils.py       # DVC integration
│   ├── main.py                # FastAPI application
│   ├── Dockerfile             # Backend container
│   ├── docker-compose.yml     # Backend services
│   └── test_*.py              # Test files
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   │   ├── ui/           # Base UI components
│   │   │   ├── ExpertCard.tsx
│   │   │   ├── ExpertList.tsx
│   │   │   └── ExpertTabs.tsx
│   │   └── lib/              # Utilities and API
│   ├── public/               # Static assets
│   ├── Dockerfile            # Frontend container
│   └── docker-compose.yml    # Frontend services
├── .dvc/                     # DVC configuration
├── .git/                     # Git repository
├── images/                   # Project images
├── reports/                  # Project reports
├── llm-finetuning/           # Model fine-tuning
├── cleanup.sh                # Cleanup scripts
├── Pipfile                   # Python dependencies
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
   - ChromaDB for vector database and semantic search
   - Persistent storage for embeddings and metadata
   - Optimized for similarity search operations

6. **Security**:
   - Secure storage for credentials
   - Environment configuration
   - API keys and access tokens
   - GCP service account credentials



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LinkedIn API integration based on unofficial API implementations
- Vector search powered by ChromaDB
- LLM capabilities provided by OpenAI and Google Vertex AI
