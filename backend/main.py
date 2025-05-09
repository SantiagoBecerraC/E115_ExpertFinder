from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, model_validator, ConfigDict, BeforeValidator
from typing import List, Optional, Union, Any, Annotated
import os
import logging

# Wrap problematic imports in try-except blocks
try:
    from agent.scholar_agent import create_scholar_agent, ChromaDBTool
    torch_available = True
except Exception as e:
    logging.error(f"Error importing scholar_agent: {e}")
    # Create stub classes or functions to allow the app to run
    torch_available = False
    class ChromaDBTool:
        def __init__(self, *args, **kwargs):
            pass
        def invoke(self, query):
            return {"error": "ChromaDBTool is not available due to dependency issues"}
    def create_scholar_agent(*args, **kwargs):
        return None

# Import other modules that don't depend on PyTorch
from linkedin_data_processing.expert_finder_linkedin import ExpertFinderAgent
from linkedin_data_processing.linkedin_vectorizer import LinkedInVectorizer
from linkedin_data_processing.dynamic_credibility import OnDemandCredibilityCalculator
from langchain_core.messages import HumanMessage
from utils.chroma_db_utils import ChromaDBManager
from utils.dvc_utils import DVCManager
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize credibility calculator
credibility_calculator = OnDemandCredibilityCalculator()
# Update stats if needed
credibility_calculator.update_stats_if_needed()

app = FastAPI(
    title="Expert Finder API",
    description="API for finding experts from various sources",
    version="1.0.0"
)

app.root_path = "/backend" 

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom type for interests that can be either a string or a list
def convert_interests(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        # Split by common delimiters and clean up
        if ',' in v:
            return [i.strip() for i in v.split(',')]
        return [i.strip() for i in v.split()]
    if isinstance(v, list):
        return v
    return []

InterestsList = Annotated[List[str], BeforeValidator(convert_interests)]

# Pydantic models for request/response
class SearchQuery(BaseModel):
    query: str
    max_results: Optional[int] = 5

    @field_validator('query')
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @field_validator('max_results')
    @classmethod
    def max_results_must_be_positive(cls, v: Optional[int]) -> int:
        if v is not None and v < 1:
            return 5  # Default to 5 if invalid
        return v

class Expert(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    title: str
    source: str
    company: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    citations: Optional[int] = None
    interests: InterestsList = []  # Use the custom InterestsList type
    publications: Optional[List[str]] = None
    summary: Optional[str] = None
    credibility_level: Optional[int] = None
    credibility_percentile: Optional[float] = None
    years_experience: Optional[float] = None

class VersionInfo(BaseModel):
    """Model for version information."""
    source: str
    profiles_added: int
    description: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "Welcome to Expert Finder API",
        "version": "1.0.0",
        "endpoints": {
            "scholar_search": "/scholar_search",
            "linkedin_search": "/linkedin_search",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Kubernetes liveness and readiness probes.
    Returns a 200 status code if the service is healthy.
    """
    return {"status": "healthy"}

@app.post("/scholar_search")
async def search_scholar_experts(search_query: SearchQuery):
    """
    Search for experts on Google Scholar based on the provided query.
    Returns a list of experts from Google Scholar.
    """
    # If torch is not available, return an error message
    if not torch_available:
        logger.error("PyTorch dependencies are not available, Google Scholar search is disabled")
        raise HTTPException(
            status_code=503,
            detail="Google Scholar search is temporarily unavailable due to dependency issues. Please use LinkedIn search instead."
        )
    
    try:
        logger.info(f"Received scholar search query: {search_query.query}")
        
        # Create ChromaDB tool with validated max_results
        logger.info("Creating ChromaDB tool...")
        chroma_tool = ChromaDBTool(api_key=os.getenv("OPENAI_API_KEY"), n_results=search_query.max_results)
        
        # Create scholar agent
        logger.info("Creating scholar agent...")
        scholar_agent = create_scholar_agent(tools=[chroma_tool])
        
        # Create a proper HumanMessage for the agent
        logger.info("Creating message and invoking agent...")
        message = HumanMessage(content=search_query.query)
        
        # Run the scholar agent
        scholar_result = scholar_agent.graph.invoke({"messages": [message]})
        logger.info(f"Scholar agent result: {scholar_result}")
        
        # Process scholar results
        scholar_experts = []
        
        # Safely parse the scholar result content
        try:
            result_content = scholar_result['messages'][-1].content
            if result_content == "[]":
                # Empty results case
                scholar_data = []
            else:
                # Try to safely evaluate the string as Python literal
                import ast
                scholar_data = ast.literal_eval(result_content)
        except (SyntaxError, ValueError) as e:
            logger.error(f"Error parsing scholar result: {e}")
            scholar_data = []
        
        # Track seen experts to avoid duplicates
        seen_expert_ids = set()
        
        for expert_data in scholar_data:
            # Extract the author profile to look for metadata
            author_profile = None
            if 'author_profile' in expert_data and 'metadata' in expert_data['author_profile']:
                author_profile = expert_data['author_profile']
            
            # Get the expert name
            expert_name = expert_data.get("name", "")
            
            # Extract Google Scholar user ID from metadata or website URL
            scholar_id = None
            
            # Check if we have the author profile with metadata
            if author_profile and 'metadata' in author_profile:
                # Look for website URL which might contain the user ID
                website = author_profile['metadata'].get('website', '')
                if website and 'citations?user=' in website:
                    # Extract the user ID from the URL
                    start_idx = website.find('user=') + 5
                    end_idx = website.find('&', start_idx) if '&' in website[start_idx:] else len(website)
                    scholar_id = website[start_idx:end_idx]
                    logger.info(f"Found Scholar ID in website URL: {scholar_id}")
            
            # If we still don't have an ID, generate one from the name
            if not scholar_id:
                # Generate a consistent ID from the name
                scholar_id = f"scholar_author_{hash(expert_name) % 10000000}"
                logger.info(f"Generated Scholar ID from name hash: {scholar_id}")
            
            # Skip if we've already seen this expert ID
            if scholar_id in seen_expert_ids:
                logger.info(f"Skipping duplicate expert: {expert_name} with ID {scholar_id}")
                continue
            
            seen_expert_ids.add(scholar_id)
            
            # Convert interests to list first
            raw_interests = expert_data.get("interests", "")
            if isinstance(raw_interests, str):
                # Split by common delimiters and clean up
                if ',' in raw_interests:
                    interests_list = [i.strip() for i in raw_interests.split(',')]
                else:
                    interests_list = [i.strip() for i in raw_interests.split()]
            elif isinstance(raw_interests, list):
                interests_list = raw_interests
            else:
                interests_list = []
            
            # Convert citations to integer
            try:
                citations = expert_data.get("citations", "0")
                if isinstance(citations, str):
                    citations = int(citations) if citations.isdigit() else 0
                else:
                    citations = int(citations) if citations is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"Could not convert citations to int: {expert_data.get('citations')}")
                citations = 0
            
            # Create the Expert object with the Google Scholar ID
            expert = Expert(
                id=scholar_id,  # Use the Google Scholar user ID
                name=expert_name,
                title=expert_data.get("affiliations", ""),  # Using affiliations as title
                source="scholar",
                citations=citations,  # Use the safely converted integer
                interests=interests_list,  # Pass the converted list
                publications=[],  # Not available in current format
                summary=expert_data.get("author_summary", "")
            )
            
            # Log the ID and interests
            logger.info(f"Created expert with ID: {expert.id}")
            
            # Add the expert to the list
            scholar_experts.append(expert)
        return {
            "experts": scholar_experts,
            "total": len(scholar_experts),
            "source": "scholar"
        }
        
    except Exception as e:
        logger.error(f"Error in search_scholar_experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/linkedin_search")
async def search_linkedin_experts(search_query: SearchQuery):
    try:
        logger.info(f"Received LinkedIn search query: {search_query.query}")
        
        # Initialize the agent - it will now use the ChromaDBManager with "linkedin" collection
        linkedin_agent = ExpertFinderAgent(
            chroma_dir=None,  # Not needed since we're using ChromaDBManager
            project_id=os.getenv("GCP_PROJECT"),
            location=os.getenv("GCP_LOCATION", "us-central1")
        )
        
        # Use the find_experts_json method
        expert_json_data = linkedin_agent.find_experts_json(
            search_query.query,
            initial_k=search_query.max_results * 2,
            final_k=search_query.max_results
        )
        
        # Convert to Expert objects
        linkedin_experts = []
        for i, expert_data in enumerate(expert_json_data):
            # Calculate credibility on-demand
            credibility = credibility_calculator.calculate_credibility(expert_data)
            
            # Add credibility data without modifying the original data
            expert = Expert(
                id=expert_data.get("id", f"linkedin_{i}"),
                name=expert_data.get("name", "Unknown"),
                title=expert_data.get("title", "Unknown"),
                source="linkedin",
                company=expert_data.get("company", "Unknown"),
                location=expert_data.get("location", "Unknown"),
                skills=expert_data.get("skills", []),
                summary=expert_data.get("summary", ""),
                credibility_level=credibility.get("level", 1),
                credibility_percentile=credibility.get("percentile", 0),
                years_experience=credibility.get("years_experience", 0)
            )
            linkedin_experts.append(expert)
        
        return {
            "experts": linkedin_experts,
            "total": len(linkedin_experts),
            "source": "linkedin"
        }
        
    except Exception as e:
        logger.error(f"Error in search_linkedin_experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Optional - keep the original search endpoint that combines both sources
@app.post("/search")
async def search_all_experts(search_query: SearchQuery):
    try:
        # Get Scholar experts
        scholar_response = await search_scholar_experts(search_query)
        scholar_experts = scholar_response.get("experts", [])
        
        # Get LinkedIn experts
        linkedin_response = await search_linkedin_experts(search_query)
        linkedin_experts = linkedin_response.get("experts", [])
        
        # Combine results
        all_experts = scholar_experts + linkedin_experts
        
        return {
            "experts": all_experts,
            "total": len(all_experts),
            "scholar_count": len(scholar_experts),
            "linkedin_count": len(linkedin_experts)
        }
    except Exception as e:
        logger.error(f"Error in search_all_experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/version")
async def version_database(version_info: VersionInfo):
    """
    Version the ChromaDB database using DVC.
    This endpoint should be called after significant updates to the database.
    """
    try:
        dvc_manager = DVCManager()
        success = dvc_manager.version_database({
            'source': version_info.source,
            'profiles_added': version_info.profiles_added,
            'description': version_info.description
        })
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to version database")
            
        return {"message": "Database successfully versioned"}
        
    except Exception as e:
        logger.error(f"Error in version_database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/versions")
async def get_version_history(max_entries: int = 10):
    """
    Get the version history of the ChromaDB database.
    """
    try:
        dvc_manager = DVCManager()
        history = dvc_manager.get_version_history(max_entries)
        return {"versions": history}
        
    except Exception as e:
        logger.error(f"Error in get_version_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/restore/{commit_hash}")
async def restore_version(commit_hash: str):
    """
    Restore the ChromaDB database to a specific version.
    """
    try:
        dvc_manager = DVCManager()
        success = dvc_manager.restore_version(commit_hash)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restore version")
            
        return {"message": f"Successfully restored to version {commit_hash}"}
        
    except Exception as e:
        logger.error(f"Error in restore_version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/update_credibility_stats")
async def update_credibility_stats(force: bool = False):
    """
    Update the credibility statistics from the current database.
    
    Args:
        force: Force update even if not needed
    """
    try:
        was_updated = credibility_calculator.update_stats_if_needed(force=force)
        return {
            "success": True,
            "message": "Credibility statistics updated" if was_updated else "No update needed",
            "was_updated": was_updated
        }
    except Exception as e:
        logger.error(f"Error updating credibility stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)