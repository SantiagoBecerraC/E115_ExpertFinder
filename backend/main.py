from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional
import os
import logging
from agent.scholar_agent import create_scholar_agent, ChromaDBTool
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

# Pydantic models for request/response
class SearchQuery(BaseModel):
    query: str
    max_results: Optional[int] = 5

    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @validator('max_results')
    def max_results_must_be_positive(cls, v):
        if v is not None and v < 1:
            return 5  # Default to 5 if invalid
        return v

class Expert(BaseModel):
    name: str
    source: str
    citations: Optional[int] = None
    interests: Optional[List[str]] = None
    publications: Optional[List[str]] = None

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
        
        # Run the agent with the properly formatted message
        agent_result = scholar_agent.graph.invoke({"messages": [message]})
        logger.info(f"Agent result: {agent_result}")
        
        # Print formatted results
        results = eval(str(agent_result['messages'][-1].content))
        
        # Process and format the results
        experts = []
        for expert_data in results:
            logger.info(f"Processing expert data: {expert_data}")
            expert = Expert(
                name=expert_data.get("name", ""),
                source=expert_data.get("source", "scholar"),
                citations=expert_data.get("citations"),
                interests=expert_data.get("interests", "").split(",") if isinstance(expert_data.get("interests"), str) else expert_data.get("interests", []),
                publications=expert_data.get("publications", [])
            )
            experts.append(expert)
        
        logger.info(f"Returning {len(experts)} experts")
        return {
            "status": "success",
            "experts": experts
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 