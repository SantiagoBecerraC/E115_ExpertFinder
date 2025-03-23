"""
Agent for retrieving and summarizing scholarly articles using ChromaDB and LLM.

"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

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

class BGEReranker:
    """Tool for reranking search results using BGE reranker model."""
    
    def __init__(self):
        self.name = "bge_reranker"
        self.model_name = "BAAI/bge-reranker-base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device)
    
    def rerank(self, query: str, documents: list) -> list:
        """
        Rerank documents based on their relevance to the query.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            
        Returns:
            List of reranked documents with scores
        """
        pairs = []
        for doc in documents:
            pairs.append([query, doc['content']])
        
        # Tokenize and get scores
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=512
            ).to(self.device)
            
            scores = self.model(**inputs).logits.squeeze().tolist()
            
            # Handle single document case
            if not isinstance(scores, list):
                scores = [scores]
            
            # Add scores to documents and sort
            for doc, score in zip(documents, scores):
                doc['rerank_score'] = score
            
            documents.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            return documents

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
        graph.add_node("rerank", self.rerank_articles)
        graph.add_node("summarize", self.summarize_content)
        graph.add_node("format", self.format_output)
        
        # Add edges
        graph.add_edge("retrieve", "rerank")
        graph.add_edge("rerank", "summarize")
        graph.add_edge("summarize", "format")
        graph.add_edge("format", END)
        
        # Set entry point
        graph.set_entry_point("retrieve")
        
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = ChatOpenAI(model="gpt-4", api_key=api_key)
        self.reranker = BGEReranker()
    
    def retrieve_articles(self, state: AgentState):
        """Retrieve articles from ChromaDB."""
        query = state['messages'][0].content
        try:
            results = self.tools['chromadb_search'].invoke(query)
            
            # Pretty print the results
            print("\n=== Retrieved Articles ===")
            print(f"Query: {query}")
            print(f"Number of results: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"\n=== Result {i} ===")
                print("\nDocument Content Preview:")
                print(f"{result['content'][:200]}...")
                
                print("\nComplete Metadata:")
                metadata = result['metadata']
                for key, value in sorted(metadata.items()):
                    print(f"  {key}: {value}")
                
                print("\nDocument Fields:")
                for key, value in sorted(result.items()):
                    if key != 'metadata' and key != 'content':
                        print(f"  {key}: {value}")
                        
                print("=" * 80)
            
            if not results:
                return {'messages': [HumanMessage(content="[]")]}
            return {'messages': [HumanMessage(content=str(results))]}
        except Exception as e:
            print(f"Error retrieving articles: {str(e)}")
            return {'messages': [HumanMessage(content="[]")]}
    
    def rerank_articles(self, state: AgentState):
        """Rerank articles using BGE reranker."""
        query = state['messages'][0].content
        try:
            results = eval(state['messages'][-1].content)
            if not results:
                return {'messages': [HumanMessage(content="[]")]}
            reranked_results = self.reranker.rerank(query, results)
            return {'messages': [HumanMessage(content=str(reranked_results))]}
        except Exception as e:
            print(f"Error reranking articles: {str(e)}")
            return {'messages': [HumanMessage(content="[]")]}
    
    def summarize_content(self, state: AgentState):
        """Summarize the articles using LLM."""
        try:
            results = eval(state['messages'][-1].content)
            if not results:
                return {'messages': [HumanMessage(content="[]")]}
            
            summaries = []
            for article in results:
                if not article.get('content'):
                    continue
                    
                prompt = f"""Summarize the key topics in 2-3 sentences:
                {article['content']}"""
                try:
                    summary = self.model.invoke(prompt)
                    article['summary'] = summary.content
                    summaries.append(article)
                except Exception as e:
                    print(f"Error summarizing article: {str(e)}")
                    continue
            
            return {'messages': [HumanMessage(content=str(summaries))]}
        except Exception as e:
            print(f"Error in summarize_content: {str(e)}")
            return {'messages': [HumanMessage(content="[]")]}
    
    def format_output(self, state: AgentState):
        """Format the final output."""
        try:
            results = eval(state['messages'][-1].content)
            if not results:
                return {'messages': [HumanMessage(content="[]")]}
                
            formatted_output = []
            for article in results:
                if not article.get('metadata'):
                    continue
                    
                metadata = article['metadata']
                # Handle different document types
                if metadata.get('doc_type') == 'author':
                    output = {
                        'type': 'author',
                        'name': metadata.get('author', 'N/A'),
                        'affiliations': metadata.get('affiliations', 'N/A'),
                        'interests': metadata.get('interests', 'N/A'),
                        'citations': metadata.get('citations', '0'),
                        'website': metadata.get('website', 'N/A'),
                        'summary': article.get('summary', 'No summary available'),
                        'rerank_score': article.get('rerank_score', 0.0)
                    }
                else:  # website_content or journal_content
                    output = {
                        'type': metadata.get('doc_type', 'N/A'),
                        'author': metadata.get('author', 'N/A'),
                        'url': metadata.get('url', 'N/A'),
                        'chunk_index': metadata.get('chunk_index', '0'),
                        'summary': article.get('summary', 'No summary available'),
                        'rerank_score': article.get('rerank_score', 0.0)
                    }
                formatted_output.append(output)
            
            return {'messages': [HumanMessage(content=str(formatted_output))]}
        except Exception as e:
            print(f"Error in format_output: {str(e)}")
            return {'messages': [HumanMessage(content="[]")]}

def create_scholar_agent():
    """Create and initialize the scholar agent."""
    try:
        # Get API key
        api_key = get_openai_api_key()
        
        prompt = """You are a scholarly research assistant. Your task is to:
        1. Search for relevant academic content including:
           - Author profiles with their expertise and interests
           - Website content from author pages
           - Journal content from publications
        2. Provide concise summaries of the content
        3. Present results sorted by relevance score
        4. For author profiles, include their research interests and affiliations
        5. For website and journal content, extract key findings and contributions
        
        Format the results based on the document type:
        - For authors: Show their expertise, affiliations, and research interests
        - For website content: Focus on current research projects and activities
        - For journal content: Emphasize key findings and methodologies
        """
        
        # Initialize tool and agent with API key
        tool = ChromaDBTool(api_key=api_key, n_results=10)
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
        
        if not outputs:
            print("\nNo results found for the given query.")
            sys.exit(0)
            
        print("\nSearch Results (sorted by reranking score):")
        print("=" * 80)
        
        # Group results by type
        authors = [r for r in outputs if r.get('type') == 'author']
        website_content = [r for r in outputs if r.get('type') == 'website_content']
        journal_content = [r for r in outputs if r.get('type') == 'journal_content']
        
        # Print author results
        if authors:
            print("\nRelevant Authors:")
            print("-" * 40)
            for i, author in enumerate(authors, 1):
                print(f"\nAuthor {i}:")
                print(f"Name: {author.get('name', 'N/A')}")
                print(f"Affiliations: {author.get('affiliations', 'N/A')}")
                print(f"Research Interests: {author.get('interests', 'N/A')}")
                print(f"Citations: {author.get('citations', '0')}")
                if author.get('website'):
                    print(f"Website: {author['website']}")
                print(f"Summary: {author.get('summary', 'No summary available')}")
                print(f"Relevance Score: {author.get('rerank_score', 0.0):.4f}")
        
        # Print website content
        if website_content:
            print("\nWebsite Content:")
            print("-" * 40)
            for i, content in enumerate(website_content, 1):
                print(f"\nContent {i}:")
                print(f"Author: {content.get('author', 'N/A')}")
                print(f"URL: {content.get('url', 'N/A')}")
                print(f"Summary: {content.get('summary', 'No summary available')}")
                print(f"Relevance Score: {content.get('rerank_score', 0.0):.4f}")
        
        # Print journal content
        if journal_content:
            print("\nJournal Content:")
            print("-" * 40)
            for i, content in enumerate(journal_content, 1):
                print(f"\nContent {i}:")
                print(f"Author: {content.get('author', 'N/A')}")
                print(f"URL: {content.get('url', 'N/A')}")
                print(f"Summary: {content.get('summary', 'No summary available')}")
                print(f"Relevance Score: {content.get('rerank_score', 0.0):.4f}")
                
        if not any([authors, website_content, journal_content]):
            print("\nNo relevant results found in any category.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. You have set the OPENAI_API_KEY environment variable")
        print("2. You have installed all required packages")
        print("3. The ChromaDB database exists and contains the 'google_scholar' collection")
        print("4. You have run scrape_and_store.py to populate the database")
        print("5. You have an active internet connection for API calls") 