"""
Agent for retrieving and summarizing scholarly articles using ChromaDB and LLM.

"""

import logging
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import json

# Add parent directory to Python path to allow imports from utils
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Dict, Any, List
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from utils.chroma_db_utils import ChromaDBManager

# Setup logging
logging.basicConfig(level=logging.INFO)  # Change from DEBUG to INFO
logger = logging.getLogger(__name__)

# Disable debug logging for OpenAI and related packages
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)
logging.getLogger('langchain').setLevel(logging.WARNING)

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


class BGEReranker:
    """Tool for reranking search results using BGE reranker model."""
    
    def __init__(self):
        self.name = "bge_reranker"
        self.model_name = "BAAI/bge-reranker-base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device)
    
    def sigmoid(self, x):
        """Convert score to probability between 0 and 1."""
        return 1 / (1 + torch.exp(-x))
    
    def rerank(self, query: str, documents: list) -> list:
        """
        Rerank documents based on their relevance to the query.
        Scores are normalized to [0,1] range using sigmoid function.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            
        Returns:
            List of reranked documents with normalized scores
        """
        if not documents:
            return documents
            
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
            
            logits = self.model(**inputs).logits
            
            # Handle both single and multiple document cases
            if logits.dim() == 0:  # Single document
                logits = logits.unsqueeze(0)  # Add batch dimension
            else:
                logits = logits.squeeze()
                
            # Convert logits to probabilities using sigmoid
            scores = self.sigmoid(logits).cpu().tolist()
            raw_scores = logits.cpu().tolist()
            
            # Ensure scores is always a list
            if not isinstance(scores, list):
                scores = [scores]
                raw_scores = [raw_scores]
            
            # Add normalized scores to documents and sort
            for doc, score, raw_score in zip(documents, scores, raw_scores):
                doc['rerank_score'] = float(score)  # Convert to float for better printing
                doc['raw_score'] = float(raw_score)  # Keep raw score for reference
            
            documents.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Print score interpretation guide
            """ print("\n=== Relevance Score Guide ===")
            print("Scores are normalized to 0-1 range where:")
            print("- 0.8 - 1.0: Extremely relevant")
            print("- 0.6 - 0.8: Highly relevant")
            print("- 0.4 - 0.6: Moderately relevant")
            print("- 0.2 - 0.4: Somewhat relevant")
            print("- 0.0 - 0.2: Less relevant")
            print("(Raw scores are also preserved in raw_score field)") """
            
            return documents


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
        """Retrieve articles from ChromaDB in two steps:
        1. Get website and journal content, grouped by author
        2. Get author information and combine with their content
        """
        query = state['messages'][0].content
        try:
            print("\n=== Debug: Starting Query Process ===")
            print(f"Query: {query}")
            
            # Step 1: Get website and journal content
            print("\n=== Step 1: Retrieving Website and Journal Content ===")
            content_results = self.tools['chromadb_search'].invoke(query)
            print(f"Initial results from ChromaDB: {len(content_results)} documents")
            
            # Debug print first result if available
            if content_results:
                first_doc = content_results[0]
                print("\nExample document structure:")
                print(f"Document type: {first_doc['metadata'].get('doc_type', 'N/A')}")
                print(f"Author: {first_doc['metadata'].get('author', 'N/A')}")
                print(f"Content preview: {first_doc['content'][:100]}...")
            
            # Filter for website and journal content
            content_results = [r for r in content_results if r['metadata'].get('doc_type') in ['website_content', 'journal_content']]
            print(f"\nAfter filtering for website/journal content: {len(content_results)} documents")
            
            # Group content by author
            author_content_map = {}
            for result in content_results:
                author = result['metadata'].get('author')
                if author:
                    if author not in author_content_map:
                        author_content_map[author] = {
                            'website_content': [],
                            'journal_content': []
                        }
                    content_type = result['metadata'].get('doc_type')
                    author_content_map[author][content_type].append(result)
                    print(f"\nAdded {content_type} document for author: {author}")
            
            print(f"\nContent grouped for {len(author_content_map)} authors")
            print("Authors found:", list(author_content_map.keys()))
            
            # Step 2: Get author information and combine with their content
            print("\n=== Step 2: Retrieving Author Information ===")
            all_results = []
            
            for author in author_content_map:
                print(f"\nProcessing author: {author}")
                # Get author profile
                author_query = f"author:{author}"
                author_docs = self.tools['chromadb_search'].invoke(author_query)
                print(f"Found {len(author_docs)} author documents for {author}")
                
                author_docs = [d for d in author_docs if d['metadata'].get('doc_type') == 'author']
                print(f"After filtering for author type: {len(author_docs)} documents")
                
                if author_docs:
                    author_doc = author_docs[0]  # Take the first author document
                    author_info = {
                        'author_profile': author_doc,
                        'website_content': author_content_map[author]['website_content'],
                        'journal_content': author_content_map[author]['journal_content']
                    }
                    all_results.append(author_info)
                    print(f"Added author info for {author}")
                    print(f"Website content: {len(author_content_map[author]['website_content'])} documents")
                    print(f"Journal content: {len(author_content_map[author]['journal_content'])} documents")
                else:
                    print(f"Warning: No author profile found for {author}")
            
            print(f"\nProcessed information for {len(all_results)} authors")
            
            if not all_results:
                print("\nDebug: No results found")
                print("Content results length:", len(content_results))
                print("Author map size:", len(author_content_map))
                return {'messages': [HumanMessage(content="[]")]}
            
            # Print detailed information
            print("\n=== Retrieved Documents ===")
            for i, result in enumerate(all_results, 1):
                print(f"\n=== Author {i} ===")
                
                # Print author information
                author_doc = result['author_profile']
                metadata = author_doc['metadata']
                print("\nAuthor Information:")
                print(f"  Name: {metadata.get('author', 'N/A')}")
                print(f"  Affiliations: {metadata.get('affiliations', 'N/A')}")
                print(f"  Interests: {metadata.get('interests', 'N/A')}")
                print(f"  Citations: {metadata.get('citations', '0')}")
                print(f"  Website: {metadata.get('website', 'N/A')}")
                
                # Print website content
                website_content = result['website_content']
                if website_content:
                    print(f"\nWebsite Content ({len(website_content)} documents):")
                    for j, content in enumerate(website_content, 1):
                        print(f"\n  Document {j}:")
                        print(f"  Content Preview: {content['content'][:200]}...")
                        print(f"  URL: {content['metadata'].get('url', 'N/A')}")
                
                # Print journal content
                journal_content = result['journal_content']
                if journal_content:
                    print(f"\nJournal Content ({len(journal_content)} documents):")
                    for j, content in enumerate(journal_content, 1):
                        print(f"\n  Document {j}:")
                        print(f"  Content Preview: {content['content'][:200]}...")
                        print(f"  URL: {content['metadata'].get('url', 'N/A')}")
                
                print("=" * 80)
                
            return {'messages': [HumanMessage(content=str(all_results))]}
        except Exception as e:
            print(f"\nError retrieving articles: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return {'messages': [HumanMessage(content="[]")]}
    
    def rerank_articles(self, state: AgentState):
        """Rerank articles using BGE reranker for each author's content."""
        query = state['messages'][0].content
        try:
            print("\n=== Debug: Starting Reranking Process ===")
            print(f"Query: {query}")
            
            results = eval(state['messages'][-1].content)
            print(f"Number of author results to process: {len(results)}")
            
            if not results:
                print("No results to rerank")
                return {'messages': [HumanMessage(content="[]")]}
            
            # Rerank each author's content separately
            for i, author_info in enumerate(results, 1):
                print(f"\n--- Processing Author {i} ---")
                author_name = author_info['author_profile']['metadata'].get('author', 'Unknown')
                print(f"Author: {author_name}")
                
                # Debug website content
                website_content = author_info['website_content']
                print(f"\nWebsite content documents: {len(website_content)}")
                if website_content:
                    print("Reranking website content...")
                    try:
                        author_info['website_content'] = self.reranker.rerank(query, website_content)
                        print("Website content reranking scores:")
                        for j, doc in enumerate(author_info['website_content'], 1):
                            print(f"  Doc {j}: score = {doc.get('rerank_score', 0.0):.4f} (raw: {doc.get('raw_score', 0.0):.4f})")
                    except Exception as e:
                        print(f"Error reranking website content: {str(e)}")
                
                # Debug journal content
                journal_content = author_info['journal_content']
                print(f"\nJournal content documents: {len(journal_content)}")
                if journal_content:
                    print("Reranking journal content...")
                    try:
                        author_info['journal_content'] = self.reranker.rerank(query, journal_content)
                        print("Journal content reranking scores:")
                        for j, doc in enumerate(author_info['journal_content'], 1):
                            print(f"  Doc {j}: score = {doc.get('rerank_score', 0.0):.4f} (raw: {doc.get('raw_score', 0.0):.4f})")
                    except Exception as e:
                        print(f"Error reranking journal content: {str(e)}")
            
            print("\n=== Reranking Complete ===")
            print(f"Processed {len(results)} authors' content")
            
            return {'messages': [HumanMessage(content=str(results))]}
        except Exception as e:
            print(f"\nError in rerank_articles: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return {'messages': [HumanMessage(content="[]")]}
    
    def summarize_content(self, state: AgentState):
        """Summarize the articles using LLM for each author's content."""
        try:
            results = eval(state['messages'][-1].content)
            if not results:
                return {'messages': [HumanMessage(content="[]")]}
            
            for author_info in results:
                # Summarize author profile
                author_doc = author_info['author_profile']
                if author_doc.get('content'):
                    prompt = f"""Summarize the author's expertise and contributions as a bullet points.
                    {author_doc['content']}"""
                    try:
                        summary = self.model.invoke(prompt)
                        author_doc['summary'] = summary.content
                    except Exception as e:
                        print(f"Error summarizing author profile: {str(e)}")
                        author_doc['summary'] = "No summary available"
                
                # Summarize website content
                for content in author_info['website_content']:
                    if content.get('content'):
                        prompt = f"""Summarize the key points as bullet points
                        {content['content']}"""
                        try:
                            summary = self.model.invoke(prompt)
                            content['summary'] = summary.content
                        except Exception as e:
                            print(f"Error summarizing website content: {str(e)}")
                            content['summary'] = "No summary available"
                
                # Summarize journal content
                for content in author_info['journal_content']:
                    if content.get('content'):
                        prompt = f"""Summarize the key findings as bullet points.
                        {content['content']}"""
                        try:
                            summary = self.model.invoke(prompt)
                            content['summary'] = summary.content
                        except Exception as e:
                            print(f"Error summarizing journal content: {str(e)}")
                            content['summary'] = "No summary available"
            
            return {'messages': [HumanMessage(content=(results))]}
        
        except Exception as e:
            print(f"Error in summarize_content: {str(e)}")
            return {'messages': [HumanMessage(content="[]")]}
    
    def format_output(self, state: AgentState):
        """Format the final output with author-grouped structure."""
        try:
            results = eval(str(state['messages'][-1].content))
            if not results:
                return {'messages': [HumanMessage(content="[]")]}
            
            formatted_output = []
            for author_info in results:
                author_doc = author_info['author_profile']
                author_metadata = author_doc['metadata']
                
                # Format author information
                author_output = {
                    'name': author_metadata.get('author', 'N/A'),
                    'affiliations': author_metadata.get('affiliations', 'N/A'),
                    'interests': author_metadata.get('interests', 'N/A'),
                    'citations': author_metadata.get('citations', '0'),
                    'author_summary': author_doc.get('summary', 'No summary available'),
                }
                
                # Format website content
                author_output['website_content'] = []
                for content in author_info['website_content']:
                    website_item = {
                        'url': content['metadata'].get('url', 'N/A'),
                        'summary': content.get('summary', 'No summary available'),
                        'rerank_score': content.get('rerank_score', 0.0)
                    }
                    author_output['website_content'].append(website_item)
                
                # Format journal content
                author_output['journal_content'] = []
                for content in author_info['journal_content']:
                    journal_item = {
                        'url': content['metadata'].get('url', 'N/A'),
                        'summary': content.get('summary', 'No summary available'),
                        'rerank_score': content.get('rerank_score', 0.0)
                    }
                    author_output['journal_content'].append(journal_item)
                
                formatted_output.append(author_output)
            
            return {'messages': [HumanMessage(content=(formatted_output))]}
        
        except Exception as e:
            print(f"Error in format_output: {str(e)}")
            return {'messages': [HumanMessage(content="[]")]}


def create_scholar_agent(tools: List[Any], system: str = "") -> ScholarAgent:
    """Create a new ScholarAgent instance."""
    api_key = get_openai_api_key()
    
    # Create default tools if none provided
    if not tools:
        # Initialize ChromaDBTool with default n_results=5
        tools = [ChromaDBTool(api_key=api_key, n_results=5)]
    
    return ScholarAgent(api_key=api_key, tools=tools, system=system)


if __name__ == "__main__":
    try:
        # Create ChromaDB tool with validated max_results
        chroma_tool = ChromaDBTool(api_key=os.getenv("OPENAI_API_KEY"), n_results=5)
        
        # Create scholar agent
        agent = create_scholar_agent(tools=[chroma_tool])
        
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
            
        print("\nSearch Results:")
        print("=" * 80)
        
        # Print results for each author
        for i, author in enumerate(outputs, 1):
            print(f"\n=== Author {i} ===")
            print("\nAuthor Information:")
            print(f"Name: {author.get('name', 'N/A')}")
            print(f"Affiliations: {author.get('affiliations', 'N/A')}")
            print(f"Research Interests: {author.get('interests', 'N/A')}")
            print(f"Citations: {author.get('citations', '0')}")
            print(f"Website: {author.get('website', 'N/A')}")
            print(f"Summary: {author.get('author_summary', 'No summary available')}")
            
            # Print website content
            website_content = author.get('website_content', [])
            if website_content:
                print("\nWebsite Content:")
                print("-" * 40)
                for j, content in enumerate(website_content, 1):
                    print(f"\nContent {j}:")
                    print(f"URL: {content.get('url', 'N/A')}")
                    print(f"Summary: {content.get('summary', 'No summary available')}")
                    print(f"Relevance Score: {content.get('rerank_score', 0.0):.4f}")
            
            # Print journal content
            journal_content = author.get('journal_content', [])
            if journal_content:
                print("\nJournal Content:")
                print("-" * 40)
                for j, content in enumerate(journal_content, 1):
                    print(f"\nContent {j}:")
                    print(f"URL: {content.get('url', 'N/A')}")
                    print(f"Summary: {content.get('summary', 'No summary available')}")
                    print(f"Relevance Score: {content.get('rerank_score', 0.0):.4f}")
            
            print("=" * 80)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. You have set the OPENAI_API_KEY environment variable")
        print("2. You have installed all required packages")
        print("3. The ChromaDB database exists and contains the 'google_scholar' collection")
        print("4. You have run scrape_and_store.py to populate the database")
        print("5. You have an active internet connection for API calls") 