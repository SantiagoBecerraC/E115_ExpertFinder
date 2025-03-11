# ExpertFinder Backend

This is the backend service for the ExpertFinder system, which processes and analyzes expert profiles using data from Google Scholar and PubMed, powered by LLMs and vector search capabilities.

## 🏗 Architecture

The backend consists of several key components:

- **Google Scholar Module** (`/google_scholar/`): Handles data collection and processing from Google Scholar profiles
- **PubMed Module** (`/pubmed/`): Processes scientific publications and author data from PubMed
- **Agent System** (`/agent/`): Implements LLM-powered agents for intelligent expert finding
- **Utils** (`/utils/`): Common utilities and helper functions
- **ChromaDB Integration**: Vector database for efficient similarity search and retrieval

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.13
- GCP credentials (for Google Scholar data collection)
- OpenAI API key (for LLM functionality)

### Environment Setup

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Set up environment variables:
Create a `.env` file with the following variables:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
GCP_PROJECT=your-gcp-project-id
OPENAI_API_KEY=your-openai-api-key
```

3. Start the services using Docker:
```bash
./docker-shell.sh
```

This will start both the ExpertFinder backend service and the ChromaDB instance.

## 📦 Dependencies

The project uses Pipenv for dependency management. Key dependencies include:

- `langchain` & `langchain-openai`: For LLM integration and agent orchestration
- `chromadb`: Vector database for semantic search
- `google-search-results`: SerpAPI integration for Google Scholar data
- `pandas`: Data processing and manipulation
- `openai`: OpenAI API integration
- `xmltodict`: XML processing for PubMed data
- `python-dotenv`: Environment variable management

## 🗄️ Project Structure

```
backend/
├── agent/                 # LLM-powered agent implementation
├── google_scholar/        # Google Scholar data collection and processing
├── pubmed/               # PubMed data integration
├── utils/                # Shared utilities
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Service orchestration
├── Pipfile              # Python dependencies
└── docker-shell.sh      # Development environment setup
```

## 🔧 Configuration

### ChromaDB Setup

The system uses ChromaDB as its vector database, configured with:
- Persistence enabled
- CORS allowed for development
- Default port: 8000

Configure ChromaDB settings in `docker-compose.yml`:
```yaml
environment:
    - IS_PERSISTENT=TRUE
    - ANONYMIZED_TELEMETRY=FALSE
    - CHROMA_SERVER_CORS_ALLOW_ORIGINS=["*"]
```

### Docker Network

The services run on a custom Docker network `lexpert-finder-network`. Create it using:
```bash
docker network create lexpert-finder-network
```
