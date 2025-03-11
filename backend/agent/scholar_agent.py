"""
Agent for retrieving and summarizing scholarly articles using ChromaDB and LLM.
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add parent directory to Python path to allow imports from utils
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from utils.chroma_db_utils import ChromaDBManager

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

def get_openai_api_key():
    """Get OpenAI API key from environment variables."""

    # Load environment variables from the secrets folder at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
    env_path = project_root / 'secrets' / '.env'
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at {env_path}. Please create a .env file in the secrets directory.")
    
    load_dotenv(dotenv_path=env_path)   
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in your environment or in a .env file."
        )
    return api_key

class ChromaDBTool:
    """Tool for retrieving articles from ChromaDB."""
    
    def __init__(self, api_key, n_results=5):

        
        self.name = "chromadb_search"
        self.n_results = n_results
        self.api_key = api_key
        self.db_manager = ChromaDBManager(collection_name="google_scholar", n_results=n_results)
    
    def invoke(self, query):
        """Search ChromaDB for relevant articles."""
        try:
            return self.db_manager.query(query)
        except Exception as e:
            raise RuntimeError(f"Failed to query ChromaDB: {str(e)}")

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class ScholarAgent:
    def __init__(self, api_key, tools, system=""):
        self.system = system
        self.api_key = api_key
        
        # Create the graph
        graph = StateGraph(AgentState)
        
        # Add nodes for each step
        graph.add_node("retrieve", self.retrieve_articles)
        graph.add_node("summarize", self.summarize_content)
        graph.add_node("format", self.format_output)
        
        # Add edges
        graph.add_edge("retrieve", "summarize")
        graph.add_edge("summarize", "format")
        graph.add_edge("format", END)
        
        # Set entry point
        graph.set_entry_point("retrieve")
        
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = ChatOpenAI(model="gpt-4", api_key=api_key)
    
    def retrieve_articles(self, state: AgentState):
        """Retrieve articles from ChromaDB."""
        query = state['messages'][0].content
        results = self.tools['chromadb_search'].invoke(query)
        print(results)
        return {'messages': [HumanMessage(content=str(results))]}
    
    def summarize_content(self, state: AgentState):
        """Summarize the articles using LLM."""
        results = eval(state['messages'][-1].content)
        summaries = []
        
        for article in results:
            prompt = f"""Summarize the key topics in 2-3 sentences:
            {article['content']}"""
            summary = self.model.invoke(prompt)
            article['summary'] = summary.content
            summaries.append(article)
        
        return {'messages': [HumanMessage(content=str(summaries))]}
    
    def format_output(self, state: AgentState):
        """Format the final output."""
        results = eval(state['messages'][-1].content)
        formatted_output = []
        
        for article in results:
            metadata = article['metadata']
            output = {
                'author': metadata.get('author_name', 'N/A'),
                'citations': metadata.get('citations_count', '0'),
                'website': metadata.get('website', 'N/A'),
                'summary': article['summary']
            }
            formatted_output.append(output)
        
        return {'messages': [HumanMessage(content=str(formatted_output))]}

def create_scholar_agent():
    """Create and initialize the scholar agent."""
    try:
        # Get API key
        api_key = get_openai_api_key()
        
        prompt = """You are a scholarly research assistant. Your task is to:
        1. Search for relevant academic articles
        2. Provide concise summaries
        3. Present results sorted by citation count
        Focus on extracting key findings and contributions from each article.
        """
        
        # Initialize tool and agent with API key
        tool = ChromaDBTool(api_key=api_key, n_results=5)
        agent = ScholarAgent(api_key=api_key, tools=[tool], system=prompt)
        return agent
    except Exception as e:
        raise RuntimeError(f"Failed to create scholar agent: {str(e)}")

if __name__ == "__main__":
    try:
        # Create agent
        agent = create_scholar_agent()
        
        # Example query
        query = "What are the recent advances in deep learning?"
        messages = [HumanMessage(content=query)]
        
        # Get results
        result = agent.graph.invoke({"messages": messages})
        
        # Print formatted results
        outputs = eval(result['messages'][-1].content)
        print("\nSearch Results (sorted by citations):")
        print("=" * 80)
        
        for i, output in enumerate(outputs, 1):
            print(output)
            print(f"\nResult {i}:")
            print(f"Authors: {output['author']}")
            print(f"Citations: {output['citations']}")
            print(f"Website: {output['website']}")
            print(f"Summary: {output['summary']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. You have set the OPENAI_API_KEY environment variable")
        backend_root = Path(__file__).parent.parent
        db_path = backend_root / "database"
        print(f"2. The ChromaDB database exists at '{db_path}' and contains the 'google_scholar' collection")
        print("3. You have loaded data using load_to_chromadb.py before querying")
        print("4. You have an active internet connection for API calls") 