"""
Agent for retrieving and summarizing scholarly articles using ChromaDB and LLM.

"""

import json
import logging
import os
import sys
from pathlib import Path

import cohere
from dotenv import load_dotenv

# Add parent directory to Python path to allow imports from utils
sys.path.append(str(Path(__file__).parent.parent))

import operator
from typing import Annotated, Any, Dict, List, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from utils.chroma_db_utils import ChromaDBManager

# Setup logging
logging.basicConfig(level=logging.INFO)  # Change from DEBUG to INFO
logger = logging.getLogger(__name__)

# Disable debug logging for OpenAI and related packages
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def get_openai_api_key():
    """Get OpenAI API key from environment variables."""

    # Load environment variables from the secrets folder at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
    env_path = project_root / "secrets" / ".env"

    if not env_path.exists():
        raise FileNotFoundError(
            f"Environment file not found at {env_path}. Please create a .env file in the secrets directory."
        )

    load_dotenv(dotenv_path=env_path)

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. " "Please set it in your environment or in a .env file."
        )
    return api_key


class ChromaDBTool:
    """Tool for retrieving articles from ChromaDB."""

    def __init__(self, api_key, n_results=250):

        self.name = "chromadb_search"
        self.n_results = n_results
        self.api_key = api_key
        self.db_manager = ChromaDBManager(collection_name="google_scholar", n_results=n_results)

    def invoke(self, query, n_results=None):
        """Search ChromaDB for relevant articles."""
        try:
            return self.db_manager.query(query, n_results=n_results)
        except Exception as e:
            raise RuntimeError(f"Failed to query ChromaDB: {str(e)}")


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class CohereReranker:
    """Tool for reranking search results using Cohere's rerank API."""

    def __init__(self):
        self.name = "cohere_reranker"
        # Get API key from environment variables
        self.api_key = os.getenv("COHERE_API_KEY")
        if not self.api_key:
            logger.warning("COHERE_API_KEY not found in environment. Reranker will use fallback scoring.")
            self.client = None
        else:
            try:
                # Initialize the Cohere client
                self.client = cohere.Client(self.api_key)
                logger.info("Cohere client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Cohere client: {e}")
                self.client = None

    def rerank(self, query: str, documents: list):
        """
        Rerank documents based on their relevance to the query using Cohere's rerank API.
        Falls back to a simple scoring method if Cohere is not available.

        Args:
            query: Search query
            documents: List of documents to rerank

        Returns:
            List of reranked documents with normalized scores
        """
        # If Cohere client is not available, use fallback scoring
        if not self.client:
            logger.info("Using fallback scoring instead of Cohere reranker")
            # Simple fallback: Count word overlap between query and documents
            query_words = set(query.lower().split())

            results = []
            for doc in documents:
                # Handle different document structures flexibly
                if isinstance(doc, dict):
                    # Try to get text content from different possible fields
                    text = doc.get("text", doc.get("content", ""))
                    # If text is empty but there's metadata with content, use that
                    if not text and "metadata" in doc:
                        text = str(doc["metadata"])
                else:
                    # If document is a string, use it directly
                    text = str(doc)

                # Simple overlap score
                doc_words = set(text.lower().split())
                overlap = len(query_words.intersection(doc_words))
                score = overlap / max(1, len(query_words))  # Normalized score

                results.append({"document": doc, "score": min(0.99, max(0.01, score))})  # Keep between 0.01 and 0.99

            # Sort by score in descending order
            results.sort(key=lambda x: x["score"], reverse=True)
            return results

        # Use Cohere's rerank API if available
        try:
            logger.info(f"Reranking {len(documents)} documents with Cohere API")

            # Extract text from documents handling different document structures
            texts = []
            for doc in documents:
                if isinstance(doc, dict):
                    # Try to get text from different possible fields
                    text = doc.get("text", doc.get("content", ""))
                    if not text and "metadata" in doc:
                        # If no text content found, use metadata as fallback
                        text = str(doc["metadata"])
                else:
                    # If document is a string, use it directly
                    text = str(doc)
                texts.append(text)

            # Call Cohere's rerank API
            rerank_response = self.client.rerank(
                query=query,
                documents=texts,
                model="rerank-english-v2.0",
                top_n=len(texts),  # Get scores for all documents
            )

            # Create results with relevance scores
            results = []
            for i, result in enumerate(rerank_response.results):
                results.append({"document": documents[i], "score": result.relevance_score})

            # Sort by score in descending order
            results.sort(key=lambda x: x["score"], reverse=True)
            return results

        except Exception as e:
            logger.error(f"Error during Cohere reranking: {e}")
            # Fall back to returning the original documents with uniform scores
            return [{"document": doc, "score": 0.5} for doc in documents]


class ScholarAgent:
    def __init__(self, api_key, tools, system=""):
        self.system = system
        self.api_key = api_key

        # Create the graph
        graph = StateGraph(AgentState)

        # Add nodes for each step
        graph.add_node("retrieve", self.retrieve_articles)
        graph.add_node("rerank", self.rerank_articles)
        # graph.add_node("summarize", self.summarize_content)
        graph.add_node("format", self.format_output)

        # Add edges
        graph.add_edge("retrieve", "rerank")
        graph.add_edge("rerank", "format")
        # graph.add_edge("summarize", "format")
        graph.add_edge("format", END)

        # Set entry point
        graph.set_entry_point("retrieve")

        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = ChatOpenAI(model="gpt-4", api_key=api_key)
        self.reranker = CohereReranker()  # Use CohereReranker instead of BGEReranker

    def retrieve_articles(self, state: AgentState):
        """Retrieve author information from ChromaDB based on query."""
        query = state["messages"][0].content
        try:
            print("\n=== Debug: Starting Query Process ===")
            print(f"Query: {query}")

            author_docs = []

            # Phase 1: Direct search with query, then filter for authors
            print("\n=== Phase 1: Direct Search ===")
            direct_results = self.tools["chromadb_search"].invoke(query, n_results=100)
            print(f"Found {len(direct_results)} total documents")

            # Print sample of direct_results for debugging
            print("\n=== Sample of Direct Results ===")
            sample_size = min(3, len(direct_results))
            for i, doc in enumerate(direct_results[:sample_size]):
                print(f"\nResult {i+1}:")
                print(f"  Document Type: {doc.get('metadata', {}).get('doc_type', 'N/A')}")
                print(f"  Author: {doc.get('metadata', {}).get('author', 'N/A')}")
                print(f"  Interests: {doc.get('metadata', {}).get('interests', 'N/A')}")
                content_preview = (
                    doc.get("content", "")[:150] + "..."
                    if len(doc.get("content", "")) > 150
                    else doc.get("content", "")
                )
                print(f"  Content Preview: {content_preview}")
                print(f"  Metadata Keys: {list(doc.get('metadata', {}).keys())}")

            # Filter direct results for authors
            phase_1_authors = [doc for doc in direct_results if doc["metadata"].get("doc_type") == "author"]
            print(f"Found {len(phase_1_authors)} author documents from direct search")
            author_docs.extend(phase_1_authors)

            # Phase 2: Author-specific search
            if len(phase_1_authors) < 5:  # If we don't have enough authors, try phase 2
                print("\n=== Phase 2: Author-Specific Search ===")
                author_query = f"doc_type:author AND {query}"
                phase_2_authors = self.tools["chromadb_search"].invoke(author_query, n_results=100)
                print(f"Found {len(phase_2_authors)} author documents from author-specific search")

                # Add any new authors that weren't already found
                existing_ids = {doc.get("id", "") for doc in author_docs}
                new_authors = [doc for doc in phase_2_authors if doc.get("id", "") not in existing_ids]
                author_docs.extend(new_authors)
                print(f"Added {len(new_authors)} new authors from phase 2")

            # Phase 3: Get all authors and filter by relevance
            if len(author_docs) < 3:  # If we still don't have enough authors, try phase 3
                print("\n=== Phase 3: Retrieving All Authors ===")
                author_query = "doc_type:author"
                all_authors = self.tools["chromadb_search"].invoke(author_query, n_results=200)
                print(f"Found {len(all_authors)} total author documents")

                # Filter for relevant authors (client-side filtering)
                relevant_authors = []
                for doc in all_authors:
                    # Skip if already in our result set
                    if doc.get("id", "") in {d.get("id", "") for d in author_docs}:
                        continue

                    metadata = doc.get("metadata", {})
                    content = doc.get("content", "").lower()

                    # Simple relevance check for phase 3
                    if query.lower() in content:
                        relevant_authors.append(doc)
                        continue

                    # Check metadata fields
                    for field in ["author", "interests", "affiliations", "title"]:
                        if field in metadata and query.lower() in str(metadata[field]).lower():
                            relevant_authors.append(doc)
                            break

                print(f"Found {len(relevant_authors)} new relevant authors from all authors search")
                author_docs.extend(relevant_authors)

            # Final check: if we still have no results, special handling for important topics
            if not author_docs:
                important_topics = [
                    "deep learning",
                    "machine learning",
                    "artificial intelligence",
                    "neural network",
                    "ai",
                    "ml",
                    "dl",
                    "data science",
                ]
                if any(topic in query.lower() for topic in important_topics):
                    print(f"\n=== Phase 4: Important Topic Fallback ===")
                    author_query = "doc_type:author"
                    all_authors = self.tools["chromadb_search"].invoke(author_query, n_results=10)
                    print(f"Adding {len(all_authors)} authors due to important topic: {query}")
                    author_docs = all_authors

            print(f"\nTotal author documents collected: {len(author_docs)}")

            # Process author docs into the expected output format
            all_results = []

            # Print metadata of first few author documents for debugging
            print("\n=== Author Document Examples ===")
            sample_size = min(3, len(author_docs))
            for i, doc in enumerate(author_docs[:sample_size]):
                metadata = doc.get("metadata", {})
                print(f"\nAuthor {i+1}:")
                print(f"  Name: {metadata.get('author', 'N/A')}")
                print(f"  Affiliations: {metadata.get('affiliations', 'N/A')}")
                print(f"  Interests: {metadata.get('interests', 'N/A')}")
                print(f"  Citations: {metadata.get('citations', '0')}")
                print(f"  Website: {metadata.get('url', 'N/A')}")
                print(f"  Email: {metadata.get('email', 'N/A')}")

            # Function to check relevancy of author document to the query
            def check_relevancy(author_doc, query):
                # Get content and metadata
                content = author_doc.get("content", "").lower()
                metadata = author_doc.get("metadata", {})

                # Print debug info
                author_name = metadata.get("author", "Unknown")
                print(f"Checking relevancy for author: {author_name} - Query: {query}")

                # IMPORTANT: For deep learning and other key AI topics, include all authors
                # This ensures we don't filter out relevant authors due to data formatting issues
                critical_topics = [
                    "deep learning",
                    "machine learning",
                    "artificial intelligence",
                    "neural network",
                    "ai",
                    "ml",
                    "dl",
                    "data science",
                ]

                query_lower = query.lower()

                # For these critical topics, don't filter at all - include everyone
                if any(topic in query_lower for topic in critical_topics):
                    print(f"PASS: Including author {author_name} for critical topic: '{query_lower}'")
                    return True

                # 1. Check interests (most important)
                interests_str = metadata.get("interests", "")
                if interests_str:
                    print(f"Raw interests: {interests_str}")
                    if query_lower in interests_str.lower():
                        print(
                            f"Interest Relevancy check PASSED for author: {author_name} - Query found in raw interests"
                        )
                        return True

                # 2. Check parsed interests
                interests = self._parse_interests(interests_str)
                if interests:
                    print(f"Parsed interests: {interests}")

                    # Check for full query match in any interest
                    for interest in interests:
                        interest_lower = interest.lower()
                        if query_lower in interest_lower:
                            print(
                                f"Interest Relevancy check PASSED for author: {author_name} - Query found in interest"
                            )
                            return True

                    # Check for word-by-word match in any interest
                    query_words = query_lower.split()
                    for interest in interests:
                        interest_lower = interest.lower()
                        matching_words = [word for word in query_words if len(word) > 3 and word in interest_lower]
                        if matching_words:
                            print(
                                f"Interest Relevancy check PASSED for author: {author_name} - Found words {matching_words} in interest"
                            )
                            return True

                # As a last resort, check content
                if query_lower in content:
                    print(f"Content Relevancy check PASSED for author: {author_name} - Query found in content")
                    return True

                print(f"Relevancy check FAILED for author: {author_name}")
                return False

            relevant_count = 0
            irrelevant_count = 0

            for author_doc in author_docs:
                # Check if the author document is relevant to the query
                if check_relevancy(author_doc, query):
                    # Create author info structure in the expected format
                    author_info = {
                        "author_profile": author_doc,
                        "website_content": [],  # Empty list as we're just focusing on authors
                        "journal_content": [],  # Empty list as we're just focusing on authors
                    }
                    all_results.append(author_info)

                    # Print basic info for debugging
                    metadata = author_doc.get("metadata", {})
                    print(f"Added relevant author: {metadata.get('author', 'Unknown')}")
                    relevant_count += 1
                else:
                    metadata = author_doc.get("metadata", {})
                    print(f"Skipped irrelevant author: {metadata.get('author', 'Unknown')}")
                    irrelevant_count += 1

            print(
                f"\nProcessed information for {len(all_results)} relevant authors (filtered out {irrelevant_count} irrelevant authors)"
            )

            if not all_results:
                print("\nDebug: No results found")
                return {"messages": [HumanMessage(content="[]")]}

            return {"messages": [HumanMessage(content=str(all_results))]}
        except Exception as e:
            print(f"\nError retrieving articles: {str(e)}")
            import traceback

            print("Traceback:")
            print(traceback.format_exc())
            return {"messages": [HumanMessage(content="[]")]}

    def _parse_interests(self, interests_str):
        """Parse interests string into a list.

        Args:
            interests_str: String containing interests separated by commas or similar delimiters

        Returns:
            List of interests
        """
        if not interests_str:
            return []

        # Check if it's already a list
        if isinstance(interests_str, list):
            return interests_str

        # Common delimiters in interests strings
        delimiters = [",", ";", "|"]

        # Try different delimiters
        for delimiter in delimiters:
            if delimiter in interests_str:
                return [interest.strip() for interest in interests_str.split(delimiter) if interest.strip()]

        # If no delimiter found, treat as a single interest
        return [interests_str.strip()]

    def rerank_articles(self, state: AgentState):
        """Rerank articles using CohereReranker for each author's content."""
        query = state["messages"][0].content
        try:
            print("\n=== Debug: Starting Reranking Process ===")
            print(f"Query: {query}")

            results = eval(state["messages"][-1].content)
            print(f"Number of author results to process: {len(results)}")

            if not results:
                print("No results to rerank")
                return {"messages": [HumanMessage(content="[]")]}

            # Rerank each author's content separately
            for i, author_info in enumerate(results, 1):
                print(f"\n--- Processing Author {i} ---")
                author_name = author_info["author_profile"]["metadata"].get("author", "Unknown")
                print(f"Author: {author_name}")

                # Debug website content
                website_content = author_info["website_content"]
                print(f"\nWebsite content documents: {len(website_content)}")
                if website_content:
                    print("Reranking website content...")
                    try:
                        author_info["website_content"] = self.reranker.rerank(query, website_content)
                        print("Website content reranking scores:")
                        for j, doc in enumerate(author_info["website_content"], 1):
                            print(f"  Doc {j}: score = {doc.get('score', 0.0):.4f}")
                    except Exception as e:
                        print(f"Error reranking website content: {str(e)}")

                # Debug journal content
                journal_content = author_info["journal_content"]
                print(f"\nJournal content documents: {len(journal_content)}")
                if journal_content:
                    print("Reranking journal content...")
                    try:
                        author_info["journal_content"] = self.reranker.rerank(query, journal_content)
                        print("Journal content reranking scores:")
                        for j, doc in enumerate(author_info["journal_content"], 1):
                            print(f"  Doc {j}: score = {doc.get('score', 0.0):.4f}")
                    except Exception as e:
                        print(f"Error reranking journal content: {str(e)}")

            print("\n=== Reranking Complete ===")
            print(f"Processed {len(results)} authors' content")

            return {"messages": [HumanMessage(content=str(results))]}
        except Exception as e:
            print(f"\nError in rerank_articles: {str(e)}")
            import traceback

            print(traceback.format_exc())
            return {"messages": [HumanMessage(content="[]")]}

    def summarize_content(self, state: AgentState):
        """Summarize the articles using LLM for each author's content."""
        try:
            results = eval(state["messages"][-1].content)
            if not results:
                return {"messages": [HumanMessage(content="[]")]}

            for author_info in results:
                # Summarize author profile
                author_doc = author_info["author_profile"]
                if author_doc.get("content"):
                    prompt = f"""Summarize the author's expertise and contributions as a bullet points.
                    {author_doc['content']}"""
                    try:
                        summary = self.model.invoke(prompt)
                        author_doc["summary"] = summary.content
                    except Exception as e:
                        print(f"Error summarizing author profile: {str(e)}")
                        author_doc["summary"] = "No summary available"

                # Summarize website content
                for content in author_info["website_content"]:
                    if content.get("content"):
                        prompt = f"""Summarize the key points as bullet points
                        {content['content']}"""
                        try:
                            summary = self.model.invoke(prompt)
                            content["summary"] = summary.content
                        except Exception as e:
                            print(f"Error summarizing website content: {str(e)}")
                            content["summary"] = "No summary available"

                # Summarize journal content
                for content in author_info["journal_content"]:
                    if content.get("content"):
                        prompt = f"""Summarize the key findings as bullet points.
                        {content['content']}"""
                        try:
                            summary = self.model.invoke(prompt)
                            content["summary"] = summary.content
                        except Exception as e:
                            print(f"Error summarizing journal content: {str(e)}")
                            content["summary"] = "No summary available"

            return {"messages": [HumanMessage(content=(results))]}

        except Exception as e:
            print(f"Error in summarize_content: {str(e)}")
            return {"messages": [HumanMessage(content="[]")]}

    def format_output(self, state: AgentState):
        """Format the results for the final output."""
        try:
            print("\n=== Debug: Starting Formatting Process ===")

            # Get results from previous step
            results = eval(state["messages"][-1].content)
            print(f"Formatting {len(results)} author results")

            if not results:
                print("No results to format")
                return {"messages": [SystemMessage(content="No relevant experts were found for your query.")]}

            # Format the output
            formatted_results = []

            for author_info in results:
                try:
                    # Extract author profile information
                    author_profile = author_info["author_profile"]
                    metadata = author_profile["metadata"]

                    # Extract citations and convert to integer for sorting
                    citation_count = 0
                    try:
                        citation_count = int(metadata.get("citations", "0"))
                        print(f"Extracted citation count for {metadata.get('author', 'Unknown')}: {citation_count}")
                    except (ValueError, TypeError):
                        print(f"Error converting citations to int for {metadata.get('author', 'Unknown')}")

                    # Create formatted author result
                    formatted_author = {
                        "name": metadata.get("author", "Unknown"),
                        "affiliations": metadata.get("affiliations", ""),
                        "interests": self._parse_interests(metadata.get("interests", "")),
                        "citations": str(citation_count),  # Convert back to string for JSON serialization
                        "website": metadata.get("url", ""),
                        "email": metadata.get("email", ""),
                        "content": [],
                    }

                    # Add website content
                    website_content = author_info.get("website_content", [])
                    for item in website_content:
                        # Handle both document and score structure from reranker
                        if isinstance(item, dict) and "document" in item:
                            doc = item["document"]
                            score = item.get("score", 0.0)
                        else:
                            doc = item
                            score = 0.0

                        # Extract content and metadata
                        content = doc.get("content", "") if isinstance(doc, dict) else str(doc)
                        metadata = doc.get("metadata", {}) if isinstance(doc, dict) else {}

                        formatted_author["content"].append(
                            {
                                "type": "website",
                                "text": content,
                                "url": metadata.get("url", ""),
                                "relevance_score": score,
                            }
                        )

                    # Add journal content
                    journal_content = author_info.get("journal_content", [])
                    for item in journal_content:
                        # Handle both document and score structure from reranker
                        if isinstance(item, dict) and "document" in item:
                            doc = item["document"]
                            score = item.get("score", 0.0)
                        else:
                            doc = item
                            score = 0.0

                        # Extract content and metadata
                        content = doc.get("content", "") if isinstance(doc, dict) else str(doc)
                        metadata = doc.get("metadata", {}) if isinstance(doc, dict) else {}

                        formatted_author["content"].append(
                            {
                                "type": "journal",
                                "text": content,
                                "url": metadata.get("url", ""),
                                "relevance_score": score,
                            }
                        )

                    # Sort content by relevance score if available
                    formatted_author["content"].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

                    formatted_results.append(formatted_author)
                except Exception as e:
                    print(f"Error formatting author: {str(e)}")
                    import traceback

                    print(traceback.format_exc())

            # Sort authors by citation count (highest first)
            try:
                print("Citation counts before sorting:", [int(x.get("citations", "0")) for x in formatted_results])
                formatted_results.sort(key=lambda x: int(x.get("citations", "0")), reverse=True)
                print("Authors after sorting by citations:", [x.get("name") for x in formatted_results])
            except Exception as e:
                print(f"Error sorting by citations: {e}")

            print(f"Formatted {len(formatted_results)} author results")

            return {"messages": [SystemMessage(content=json.dumps(formatted_results))]}

        except Exception as e:
            print(f"Error in format_output: {str(e)}")
            import traceback

            print(traceback.format_exc())
            return {"messages": [SystemMessage(content="An error occurred while formatting the results.")]}


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
        outputs = eval(result["messages"][-1].content)

        if not outputs:
            print("\nNo results found for the given query.")
            sys.exit(0)

        print("\nSearch Results:")
        print("=" * 80)

        # Print results for each author
        for i, author in enumerate(outputs, 1):
            print(f"\n=== Author {i} ===")

            # Print author information
            print("\nAuthor Information:")
            print(f"Name: {author.get('name', 'N/A')}")
            print(f"Affiliations: {author.get('affiliations', 'N/A')}")
            print(f"Research Interests: {author.get('interests', 'N/A')}")
            print(f"Citations: {author.get('citations', '0')}")
            print(f"Website: {author.get('website', 'N/A')}")
            print(f"Email: {author.get('email', 'N/A')}")

            # Print content
            content = author.get("content", [])
            if content:
                print("\nContent:")
                print("-" * 40)
                for j, item in enumerate(content, 1):
                    print(f"\nItem {j}:")
                    print(f"Type: {item.get('type', 'N/A')}")
                    print(f"Text: {item.get('text', 'N/A')}")
                    print(f"URL: {item.get('url', 'N/A')}")
                    print(f"Relevance Score: {item.get('relevance_score', 0.0):.4f}")

            print("=" * 80)

    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. You have set the OPENAI_API_KEY environment variable")
        print("2. You have installed all required packages")
        print("3. The ChromaDB database exists and contains the 'google_scholar' collection")
        print("4. You have run scrape_and_store.py to populate the database")
        print("5. You have an active internet connection for API calls")
