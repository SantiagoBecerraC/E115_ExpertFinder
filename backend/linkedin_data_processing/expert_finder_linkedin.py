import argparse
import json
import os
import re

import chromadb
import torch
from google.cloud import aiplatform
from sentence_transformers import CrossEncoder, SentenceTransformer
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from utils.chroma_db_utils import ChromaDBManager
from vertexai.generative_models import GenerationConfig, GenerativeModel


def search_profiles(query, filters=None, top_k=5, chroma_dir="chroma_db"):
    """
    Search for profiles using semantic search with advanced filtering capabilities.

    Args:
        query (str): The search query
        filters (dict, optional): Metadata filters with multiple conditions
        top_k (int): Number of results to return
        chroma_dir (str): Directory where ChromaDB data is persisted (not used when ChromaDBManager is used)

    Returns:
        list: Matching profiles with similarity scores
    """
    # Initialize embedding model
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Use ChromaDBManager instead of direct ChromaDB connection
    # This ensures we're using the same path and collection as LinkedInVectorizer
    try:
        print("Connecting to ChromaDB using ChromaDBManager")
        chroma_manager = ChromaDBManager(collection_name="linkedin")
        collection = chroma_manager.collection
        print(f"Collection has {collection.count()} documents")
    except Exception as e:
        print(f"Error accessing collection: {str(e)}")
        return []

    # Generate query embedding
    query_embedding = embedding_model.encode(query)

    # Prepare where clause with advanced filtering
    where_clauses = []

    if filters:
        for key, value in filters.items():
            # Handle different types of filters
            if isinstance(value, list):
                # Handle lists of values
                if len(value) > 1:
                    # Multiple values: OR condition within the same field
                    where_clauses.append({"$or": [{key: v} for v in value]})
                elif len(value) == 1:
                    # Single value in a list: use direct equality
                    where_clauses.append({key: value[0]})
                # Skip empty lists
            elif isinstance(value, dict):
                # Handle special operators
                if "$in" in value:
                    # IN condition
                    if len(value["$in"]) > 1:
                        where_clauses.append({"$or": [{key: v} for v in value["$in"]]})
                    elif len(value["$in"]) == 1:
                        where_clauses.append({key: value["$in"][0]})
                elif "$gte" in value:
                    # Greater than or equal - convert to float/int
                    try:
                        numeric_value = float(value["$gte"])
                        # Use int if it's a whole number
                        if numeric_value.is_integer():
                            numeric_value = int(numeric_value)
                        where_clauses.append({key: {"$gte": numeric_value}})
                    except (ValueError, TypeError):
                        # If conversion fails, use the original value
                        where_clauses.append({key: {"$gte": value["$gte"]}})
                elif "$lte" in value:
                    # Less than or equal - convert to float/int
                    try:
                        numeric_value = float(value["$lte"])
                        # Use int if it's a whole number
                        if numeric_value.is_integer():
                            numeric_value = int(numeric_value)
                        where_clauses.append({key: {"$lte": numeric_value}})
                    except (ValueError, TypeError):
                        # If conversion fails, use the original value
                        where_clauses.append({key: {"$lte": value["$lte"]}})
                elif "$gt" in value:
                    # Greater than - convert to float/int
                    try:
                        numeric_value = float(value["$gt"])
                        # Use int if it's a whole number
                        if numeric_value.is_integer():
                            numeric_value = int(numeric_value)
                        where_clauses.append({key: {"$gt": numeric_value}})
                    except (ValueError, TypeError):
                        # If conversion fails, use the original value
                        where_clauses.append({key: {"$gt": value["$gt"]}})
                elif "$lt" in value:
                    # Less than - convert to float/int
                    try:
                        numeric_value = float(value["$lt"])
                        # Use int if it's a whole number
                        if numeric_value.is_integer():
                            numeric_value = int(numeric_value)
                        where_clauses.append({key: {"$lt": numeric_value}})
                    except (ValueError, TypeError):
                        # If conversion fails, use the original value
                        where_clauses.append({key: {"$lt": value["$lt"]}})
            else:
                # Simple equality filter
                where_clauses.append({key: value})

    # Combine all where clauses with AND
    where_condition = None
    if where_clauses:
        if len(where_clauses) > 1:
            where_condition = {"$and": where_clauses}
        else:
            # If there's only one clause, no need for $and
            where_condition = where_clauses[0]

    try:
        # Debug output
        print(f"Using where condition: {where_condition}")

        # Search in ChromaDB with combined filters
        results = collection.query(query_embeddings=[query_embedding.tolist()], n_results=top_k, where=where_condition)

        # Format results
        matches = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for i, (doc_id, document, metadata, distance) in enumerate(
                zip(results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0])
            ):
                # Calculate similarity score (convert distance to similarity)
                similarity = 1 - distance

                matches.append(
                    {
                        "rank": i + 1,
                        "urn_id": doc_id,
                        "name": metadata.get("name"),
                        "current_title": metadata.get("current_title"),
                        "current_company": metadata.get("current_company"),
                        "location": metadata.get("location"),
                        "industry": metadata.get("industry"),
                        "education_level": metadata.get("education_level"),
                        "career_level": metadata.get("career_level"),
                        "years_experience": metadata.get("years_experience"),
                        "similarity": similarity,
                        "profile_summary": document[:300] + "..." if len(document) > 300 else document,
                    }
                )

        return matches

    except Exception as e:
        print(f"Error searching profiles: {str(e)}")
        return []


class ExpertFinderAgent:
    def __init__(
        self,
        chroma_dir="chroma_db",
        project_id=None,
        location="us-central1",
        reranker_model_name="BAAI/bge-reranker-v2-m3",
    ):
        """
        Initialize the Expert Finder Agent with Vertex AI and a reranker.

        Args:
            chroma_dir (str): Directory where ChromaDB data is persisted
            project_id (str): Google Cloud project ID (will use environment variable if not provided)
            location (str): Google Cloud region
            reranker_model_name (str): Name of the HuggingFace reranker model to use
        """
        self.chroma_dir = chroma_dir

        # Get project ID from environment variable if not provided
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.reranker_model_name = reranker_model_name

        # Initialize Vertex AI
        try:
            # Initialize Vertex AI SDK
            aiplatform.init(project=self.project_id, location=self.location)

            # Initialize the Gemini 1.5 Flash model
            # self.model = GenerativeModel("gemini-1.5-flash-001")
            # print(f"✅ Successfully connected to Vertex AI Gemini 1.5 Flash in project {self.project_id}")
            # Connect to your custom model endpoint
            self.model = GenerativeModel(
                "projects/expertfinder-452203/locations/us-central1/endpoints/8431764346786283520",
                # generation_config={"candidate_count": 1}
            )
            print(
                f"✅ Successfully connected to Vertex AI expert-finder-v2 finetuned model in project {self.project_id}"
            )
        except Exception as e:
            print(f"❌ Error initializing Vertex AI: {str(e)}")
            print("Make sure you have set up Google Cloud credentials correctly")
            print("Run: gcloud auth application-default login")
            self.model = None

        # Initialize the reranker model
        try:
            print(f"Loading reranker model: {reranker_model_name}")
            self.reranker = CrossEncoder(reranker_model_name, max_length=512)
            print("✅ Successfully loaded reranker model")
        except Exception as e:
            print(f"❌ Error loading reranker model: {str(e)}")
            print("Falling back to similarity scores without reranking")
            self.reranker = None

    def parse_query(self, user_query):
        """
        Parse the user query to extract search terms and filters using Gemini 1.5 Flash.

        Args:
            user_query (str): Natural language query from the user

        Returns:
            tuple: (search_query, filters)
        """
        if not self.model:
            # Fallback to simple parsing if Vertex AI is not available
            return user_query, {}

        system_prompt = """
        You are an AI assistant that helps parse user queries about finding LinkedIn experts.
        Extract the following information from the user's query:
        1. The main search query (skills, expertise, or role they're looking for)
        2. Any filters that should be applied (location, company, industry, education level, career level, years of experience)
        
        Format your response as a JSON object with these fields:
        {
            "search_query": "The main search terms",
            "filters": {
                "location": ["Location filter if specified"],  # Use array even for single values
                "industry": ["Industry filter if specified"],  # Use array even for single values
                "current_company": ["Company name if specified"],  # Use array for companies mentioned
                "education_level": ["Education level filter if specified"],  # PhD, Masters, Bachelors, Other
                "career_level": ["Career level filter if specified"],  # Executive, Director, Manager, Senior, Other
                "years_experience": {"$gte": "10"}  # If years of experience is mentioned with a comparison
            }
        }
        
        Notes:
        - IMPORTANT: If the user mentions a company name (like Google, Microsoft, Meta, etc.), use the "current_company" filter, NOT industry
        - Companies should be categorized as "current_company" while industries are broader sectors like "Technology", "Finance", etc.
        - For location, industry, current_company, education_level, and career_level, always use arrays even for single values
        - If multiple values are mentioned for a field, include all of them in the array
        - For years_experience, use comparison operators ($gte, $lte) if appropriate
        - Only include filter fields that are explicitly mentioned in the query
        """

        prompt = f"{system_prompt}\n\nUser query: {user_query}\n\nJSON response:"

        try:
            # Configure generation parameters for structured output
            generation_config = GenerationConfig(
                temperature=0.1,  # Low temperature for more deterministic results
                max_output_tokens=1024,
                top_p=0.95,
                top_k=40,
            )

            response = self.model.generate_content(prompt, generation_config=generation_config)

            # Extract JSON from the response
            json_text = response.text.strip()

            # Handle potential formatting issues
            if not json_text.startswith("{"):
                # Try to find JSON in the text
                match = re.search(r"({.*})", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                else:
                    raise ValueError("Could not extract JSON from response")

            # Parse the JSON response
            parsed_data = json.loads(json_text)

            # Extract search query and filters
            search_query = parsed_data.get("search_query", "")
            filters = parsed_data.get("filters", {})

            # Remove any None or empty string values from filters
            filters = {k: v for k, v in filters.items() if v}

            # Ensure string values are converted to lists for certain fields
            for key in ["location", "industry", "education_level", "career_level"]:
                if key in filters and isinstance(filters[key], str):
                    filters[key] = [filters[key]]

            # Handle years_experience if it's a string
            if "years_experience" in filters and isinstance(filters["years_experience"], str):
                try:
                    # Try to convert to integer and use as $gte
                    years = int(filters["years_experience"])
                    filters["years_experience"] = {"$gte": years}  # Use numeric value directly, not string
                except ValueError:
                    # If not a number, treat as a regular string
                    filters["years_experience"] = [filters["years_experience"]]

            return search_query, filters

        except Exception as e:
            print(f"Error parsing query: {str(e)}")
            # Fallback to simple parsing if Gemini fails
            return user_query, {}

    def search_profiles_with_reranking(self, query, filters=None, initial_k=20, final_k=5):
        """
        Search for profiles using semantic search, then rerank the results.

        Args:
            query (str): The search query
            filters (dict, optional): Metadata filters (e.g., {"industry": "Internet"})
            initial_k (int): Number of initial results to retrieve
            final_k (int): Number of results to return after reranking

        Returns:
            list: Reranked matching profiles with similarity scores
        """
        try:
            # Get initial results from ChromaDB
            initial_results = search_profiles(query, filters, initial_k, self.chroma_dir)

            if not initial_results:
                return []

            if not self.reranker:
                # If reranker is not available, just return the top final_k results
                return initial_results[:final_k]

            print(f"Reranking {len(initial_results)} initial results...")

            try:
                # Prepare pairs for reranking
                pairs = []
                for result in initial_results:
                    # Create a pair of query and profile text
                    pairs.append([query, result["profile_summary"]])

                # Get scores from the reranker
                scores = self.reranker.predict(pairs)

                # Add reranker scores to the results
                for i, result in enumerate(initial_results):
                    result["rerank_score"] = float(scores[i])

                # Sort by reranker score (descending)
                reranked_results = sorted(initial_results, key=lambda x: x["rerank_score"], reverse=True)

                # Update ranks
                for i, result in enumerate(reranked_results):
                    result["rank"] = i + 1

                # Return the top final_k results
                return reranked_results[:final_k]
            except Exception as e:
                print(f"Error during reranking: {str(e)}")
                # If reranking fails, return the original results sorted by similarity
                return sorted(initial_results, key=lambda x: x["similarity"], reverse=True)[:final_k]

        except Exception as e:
            print(f"Error in search_profiles_with_reranking: {str(e)}")
            return []

    def generate_response(self, user_query, search_results):
        """
        Generate a response summarizing the search results using Gemini 1.5 Flash.

        Args:
            user_query (str): Original user query
            search_results (list): Results from the search_profiles function

        Returns:
            str: Generated response summarizing the experts found
        """
        if not self.model:
            # Fallback to simple response if Vertex AI is not available
            if not search_results:
                return "I couldn't find any experts matching your criteria."
            return f"I found {len(search_results)} experts matching your query. The top match is {search_results[0]['name']}, who is a {search_results[0]['current_title']} at {search_results[0]['current_company']}."

        if not search_results:
            return "I couldn't find any experts matching your criteria. Please try a different search query or filters."

        # Prepare the context for Gemini
        context = "Here are the top experts I found:\n\n"

        for result in search_results:
            context += f"Expert {result['rank']}:\n"
            context += f"Name: {result['name']}\n"
            context += f"Current Position: {result['current_title']} at {result['current_company']}\n"
            context += f"Location: {result['location']}\n"
            context += f"Industry: {result['industry']}\n"
            context += f"Education Level: {result['education_level']}\n"
            context += f"Career Level: {result['career_level']}\n"

            # Include both scores if reranking was used
            if "rerank_score" in result:
                context += f"Initial Similarity: {result['similarity']:.2f}\n"
                context += f"Relevance Score: {result['rerank_score']:.2f}\n"
            else:
                context += f"Relevance Score: {result['similarity']:.2f}\n"

            context += f"Profile Summary: {result['profile_summary']}\n\n"

        system_prompt = """
        You are an AI assistant that helps find LinkedIn experts based on user queries.
        Summarize the search results in a helpful, concise way.
        
        For each expert, mention:
        1. Their name and current position
        2. Why they might be a good match for the query (based on their experience, skills, etc.)
        3. Any standout qualifications or achievements
        
        Start with a brief introduction summarizing what the user asked for and how many results you found.
        Then list each expert with their key details.
        End with a brief conclusion.
        
        Keep your response conversational and helpful.
        """

        prompt = f"{system_prompt}\n\nQuery: {user_query}\n\nSearch Results:\n{context}\n\nResponse:"

        try:
            # Configure generation parameters for a more natural response
            generation_config = GenerationConfig(
                temperature=0.7,  # Slightly higher temperature for more natural responses
                max_output_tokens=2048,
                top_p=0.95,
                top_k=40,
            )

            response = self.model.generate_content(prompt, generation_config=generation_config)

            return response.text

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            # Fallback to simple response if Gemini fails
            return f"I found {len(search_results)} experts matching your query. The top match is {search_results[0]['name']}, who is a {search_results[0]['current_title']} at {search_results[0]['current_company']}."

    def find_experts(self, user_query, initial_k=20, final_k=5):
        """
        Main function to find experts based on a natural language query.

        Args:
            user_query (str): Natural language query from the user
            initial_k (int): Number of initial results to retrieve
            final_k (int): Number of results to return after reranking

        Returns:
            str: Generated response summarizing the experts found
        """
        print(f"Processing query: '{user_query}'")

        # Parse the query to extract search terms and filters
        search_query, filters = self.parse_query(user_query)

        print(f"Parsed search query: '{search_query}'")
        if filters:
            print(f"Parsed filters: {filters}")

        # Perform the search with reranking
        search_results = self.search_profiles_with_reranking(
            search_query, filters, initial_k=initial_k, final_k=final_k
        )

        print(f"Found {len(search_results)} matching experts after reranking")

        # Generate a response summarizing the results
        response = self.generate_response(user_query, search_results)

        return response

    def generate_json_response(self, user_query, search_results):
        """
        Generate a JSON response summarizing the search results using Gemini.

        Args:
            user_query (str): Original user query
            search_results (list): Results from the search_profiles function

        Returns:
            list: List of expert profiles in JSON format
        """
        if not self.model:
            # Fallback to simple response if Vertex AI is not available
            return [self._format_expert_json(expert) for expert in search_results]

        if not search_results:
            return []

        # Prepare the context for Gemini
        context = "Here are the top experts I found:\n\n"

        for result in search_results:
            context += f"Expert {result['rank']}:\n"
            context += f"ID: {result.get('urn_id', '')}\n"
            context += f"Name: {result.get('name', '')}\n"
            context += f"Current Position: {result.get('current_title', '')} at {result.get('current_company', '')}\n"
            context += f"Location: {result.get('location', '')}\n"
            context += f"Industry: {result.get('industry', '')}\n"
            context += f"Education Level: {result.get('education_level', '')}\n"
            context += f"Career Level: {result.get('career_level', '')}\n"
            context += f"Years Experience: {result.get('years_experience', '')}\n"

            # Include both scores if reranking was used
            if "rerank_score" in result:
                context += f"Initial Similarity: {result['similarity']:.2f}\n"
                context += f"Relevance Score: {result['rerank_score']:.2f}\n"
            else:
                context += f"Relevance Score: {result['similarity']:.2f}\n"

            context += f"Profile Summary: {result['profile_summary']}\n\n"

        system_prompt = """
        You are an AI assistant that helps find LinkedIn experts based on user queries.
        Extract relevant information from the search results and format it as a JSON array.
        
        For each expert, include these fields:
        - id: The expert's unique identifier
        - name: Full name of the expert
        - title: Current job title
        - company: Current company
        - location: Geographic location
        - skills: Extract 3-5 key skills based on their profile summary and experience
        - years_experience: Years of professional experience (numeric value)
        - education_level: Highest level of education
        - credibility_level: A numeric value from 1-5 based on experience and education
        - similarity: The similarity/relevance score
        - rerank_score: The reranking score if available
        - summary: A brief 1-2 sentence summary of their expertise

        Return ONLY the JSON array with no additional text or explanation.
        """

        prompt = f"{system_prompt}\n\nQuery: {user_query}\n\nSearch Results:\n{context}\n\nJSON Response:"

        try:
            # Configure generation parameters for structured JSON output
            generation_config = GenerationConfig(
                temperature=0.1,  # Low temperature for more deterministic results
                max_output_tokens=4096,
                top_p=0.95,
                top_k=40,
            )

            response = self.model.generate_content(prompt, generation_config=generation_config)

            # Extract JSON from the response
            json_text = response.text.strip()

            # Handle potential formatting issues
            if not json_text.startswith("["):
                # Try to find JSON array in the text
                match = re.search(r"(\[.*\])", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                else:
                    raise ValueError("Could not extract JSON array from response")

            # Parse the JSON response
            experts_data = json.loads(json_text)
            return experts_data

        except Exception as e:
            print(f"Error generating JSON response: {str(e)}")
            # Fallback to simple formatting if Gemini fails
            return [self._format_expert_json(expert) for expert in search_results]

    def _format_expert_json(self, expert):
        """Fallback method to format expert data as JSON if LLM fails."""
        # Extract years of experience (default to 0 if not available)
        years_experience = 0
        try:
            years_experience = int(expert.get("years_experience", "0"))
        except (ValueError, TypeError):
            pass

        return {
            "id": expert.get("urn_id", ""),
            "name": expert.get("name", ""),
            "title": expert.get("current_title", ""),
            "company": expert.get("current_company", ""),
            "location": expert.get("location", ""),
            "skills": [],  # No skills extraction in fallback
            "years_experience": years_experience,
            "education_level": expert.get("education_level", ""),
            "credibility_level": expert.get("career_level", ""),
            "similarity": expert.get("similarity", 0),
            "rerank_score": expert.get("rerank_score", 0) if "rerank_score" in expert else None,
            "summary": (
                expert.get("profile_summary", "")[:150] + "..."
                if len(expert.get("profile_summary", "")) > 150
                else expert.get("profile_summary", "")
            ),
        }

    def find_experts_json(self, user_query, initial_k=20, final_k=5):
        """
        Find experts based on a natural language query and return structured JSON.

        Args:
            user_query (str): Natural language query
            initial_k (int): Number of initial results to retrieve
            final_k (int): Number of results to return after reranking

        Returns:
            list: JSON-formatted expert profiles
        """
        print(f"Processing query: '{user_query}'")

        # Parse the query to extract search terms and filters
        search_query, filters = self.parse_query(user_query)

        print(f"Parsed search query: '{search_query}'")
        if filters:
            print(f"Parsed filters: {filters}")

        # Perform the search with reranking
        search_results = self.search_profiles_with_reranking(
            search_query, filters, initial_k=initial_k, final_k=final_k
        )

        print(f"Found {len(search_results)} matching experts after reranking")

        # Use the LLM to generate a structured JSON response
        expert_data = self.generate_json_response(user_query, search_results)

        return expert_data


def main():
    parser = argparse.ArgumentParser(description="Expert Finder Agent with Reranking")
    parser.add_argument("--query", required=True, help="Natural language query to find experts")
    parser.add_argument("--chroma_dir", default="chroma_db", help="Directory where ChromaDB data is persisted")
    parser.add_argument("--initial_k", type=int, default=20, help="Number of initial results to retrieve")
    parser.add_argument("--final_k", type=int, default=5, help="Number of results to return after reranking")
    parser.add_argument("--project_id", help="Google Cloud project ID")
    parser.add_argument("--location", default="us-central1", help="Google Cloud region")
    parser.add_argument("--reranker", default="BAAI/bge-reranker-v2-m3", help="HuggingFace reranker model name")
    parser.add_argument("--json", action="store_true", help="Return results as JSON instead of text")

    args = parser.parse_args()

    # Check if Google Cloud credentials are set up
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("Please set it or run: gcloud auth application-default login")

    # Initialize the agent
    agent = ExpertFinderAgent(
        chroma_dir=args.chroma_dir,
        project_id=args.project_id,
        location=args.location,
        reranker_model_name=args.reranker,
    )

    # Find experts based on the query
    if args.json:
        response = agent.find_experts_json(args.query, args.initial_k, args.final_k)
        print("\n" + "=" * 50)
        print("Expert Finder Results (JSON):")
        print("=" * 50)
        print(json.dumps(response, indent=2))
        print("=" * 50)
    else:
        response = agent.find_experts(args.query, args.initial_k, args.final_k)
        print("\n" + "=" * 50)
        print("Expert Finder Results:")
        print("=" * 50)
        print(response)
        print("=" * 50)


def test_search():
    """
    Test function to verify that different filter combinations work correctly.
    """
    print("Testing search with different filter combinations...")

    # Test case 1: Single value in a list
    filters1 = {"education_level": ["PhD"]}
    print("\nTest 1: Single value in a list")
    print(f"Filters: {filters1}")
    results1 = search_profiles("machine learning", filters1, top_k=3)
    print(f"Found {len(results1)} results")
    if results1:
        for result in results1:
            print(f"  - {result['name']} ({result['education_level']}): {result['current_title']}")

    # Test case 2: Multiple values in a list
    filters2 = {"education_level": ["PhD", "Masters"]}
    print("\nTest 2: Multiple values in a list")
    print(f"Filters: {filters2}")
    results2 = search_profiles("machine learning", filters2, top_k=3)
    print(f"Found {len(results2)} results")
    if results2:
        for result in results2:
            print(f"  - {result['name']} ({result['education_level']}): {result['current_title']}")

    # Test case 3: Multiple filter fields
    filters3 = {"education_level": ["PhD"], "industry": ["Technology", "Software"]}
    print("\nTest 3: Multiple filter fields")
    print(f"Filters: {filters3}")
    results3 = search_profiles("machine learning", filters3, top_k=3)
    print(f"Found {len(results3)} results")
    if results3:
        for result in results3:
            print(
                f"  - {result['name']} ({result['education_level']}, {result['industry']}): {result['current_title']}"
            )

    # Test case 4: Numeric comparison
    filters4 = {"years_experience": {"$gte": "10"}}
    print("\nTest 4: Numeric comparison")
    print(f"Filters: {filters4}")
    results4 = search_profiles("machine learning", filters4, top_k=3)
    print(f"Found {len(results4)} results")
    if results4:
        for result in results4:
            print(f"  - {result['name']} (Experience: {result['years_experience']} years): {result['current_title']}")

    # Test case 5: Numeric comparison with integer
    filters5 = {"years_experience": {"$gte": 10}}  # Integer directly, not string
    print("\nTest 5: Numeric comparison with integer")
    print(f"Filters: {filters5}")
    results5 = search_profiles("machine learning", filters5, top_k=3)
    print(f"Found {len(results5)} results")
    if results5:
        for result in results5:
            print(f"  - {result['name']} (Experience: {result['years_experience']} years): {result['current_title']}")


if __name__ == "__main__":
    main()
    # Uncomment to run tests
    # test_search()
