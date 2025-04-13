from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, model_validator, ConfigDict, BeforeValidator
from typing import List, Optional, Union, Any, Annotated
import os
import logging
from agent.scholar_agent import create_scholar_agent, ChromaDBTool
from linkedin_data_processing.expert_finder_linkedin import ExpertFinderAgent
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Expert Finder API",
    description="API for finding experts from various sources",
    version="1.0.0"
)

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

@app.get("/")
async def root():
    return {
        "message": "Welcome to Expert Finder API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.post("/search")
async def search_experts(search_query: SearchQuery):
    try:
        logger.info(f"Received search query: {search_query.query}")
        
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
        scholar_data = eval(str(scholar_result['messages'][-1].content))
        
        # Debug logging
        logger.info(f"Scholar data type: {type(scholar_data)}")
        if scholar_data:
            logger.info(f"First expert data: {scholar_data[0]}")
            logger.info(f"Interests type: {type(scholar_data[0].get('interests'))}")
            logger.info(f"Interests value: {scholar_data[0].get('interests')}")
        
        for expert_data in scholar_data:
            # Create Expert object with debug logging
            try:
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
                
                # Create the Expert object
                expert = Expert(
                    id=f"scholar_{len(scholar_experts)}",
                    name=expert_data.get("name", ""),
                    title=expert_data.get("affiliations", ""),  # Using affiliations as title
                    source="scholar",
                    citations=expert_data.get("citations", 0),
                    interests=interests_list,  # Pass the converted list
                    publications=[],  # Not available in current format
                    summary=expert_data.get("author_summary", "")
                )
                
                # Log the interests field after creating the Expert object
                logger.info(f"Expert interests after creation: {expert.interests}")
                logger.info(f"Expert interests type after creation: {type(expert.interests)}")
                
                # Add the expert to the list
                scholar_experts.append(expert)
            except Exception as e:
                logger.error(f"Error creating Expert object: {str(e)}")
                logger.error(f"Expert data: {expert_data}")
                # Continue with the next expert instead of raising an exception
                continue
        
        # Search for LinkedIn experts using the existing ExpertFinderAgent
        logger.info("Searching LinkedIn experts...")
        linkedin_agent = ExpertFinderAgent(
            chroma_dir=os.getenv("CHROMA_DIR", "chroma_db"),
            project_id=os.getenv("GCP_PROJECT"),
            location=os.getenv("GCP_LOCATION", "us-central1")
        )
        
        # Get LinkedIn search results
        linkedin_response = linkedin_agent.find_experts(
            search_query.query,
            initial_k=search_query.max_results * 2,  # Get more initial results for better selection
            final_k=search_query.max_results
        )
        
        # Extract LinkedIn experts from the response
        linkedin_experts = []
        
        # The response is a text summary, so we need to extract the expert data
        # This is a simplified approach - in a real implementation, you might want to
        # modify the ExpertFinderAgent to return structured data
        try:
            # Try to extract expert data from the response
            # This is a simplified approach and might need adjustment based on the actual response format
            import re
            
            # Look for patterns like "Name: John Doe" in the response
            name_matches = re.findall(r"Name: ([^\n]+)", linkedin_response)
            title_matches = re.findall(r"Current Position: ([^\n]+)", linkedin_response)
            company_matches = re.findall(r"at ([^\n]+)", linkedin_response)
            location_matches = re.findall(r"Location: ([^\n]+)", linkedin_response)
            
            # Create experts from the extracted data
            for i in range(min(len(name_matches), search_query.max_results)):
                name = name_matches[i] if i < len(name_matches) else "Unknown"
                title = title_matches[i] if i < len(title_matches) else "Unknown"
                company = company_matches[i] if i < len(company_matches) else "Unknown"
                location = location_matches[i] if i < len(location_matches) else "Unknown"
                
                linkedin_experts.append(Expert(
                    id=f"linkedin_{len(linkedin_experts)}",
                    name=name,
                    title=title,
                    source="linkedin",
                    company=company,
                    location=location,
                    skills=[],  # Skills would need to be extracted similarly
                    summary=linkedin_response  # Use the full response as summary for now
                ))
        except Exception as e:
            logger.error(f"Error extracting LinkedIn expert data: {str(e)}")
            # If extraction fails, create a single expert with the full response
            linkedin_experts.append(Expert(
                id="linkedin_0",
                name="LinkedIn Expert",
                title="Professional",
                source="linkedin",
                summary=linkedin_response
            ))
        
        # Combine results from both sources
        all_experts = scholar_experts + linkedin_experts
        
        return {
            "experts": all_experts,
            "total": len(all_experts),
            "scholar_count": len(scholar_experts),
            "linkedin_count": len(linkedin_experts)
        }
        
    except Exception as e:
        logger.error(f"Error in search_experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 