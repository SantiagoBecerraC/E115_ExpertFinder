"""
Utility for vectorizing LinkedIn profiles using ChromaDBManager.
Creates and manages a LinkedIn profiles collection in the shared ChromaDB database.
"""

import os
import json
import glob
import shutil
from tqdm import tqdm
from pathlib import Path
import sys
from typing import List, Dict, Any, Set, Optional
from google.cloud import storage

# Add parent directory to path to import utils
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
sys.path.append(str(parent_dir))

from utils.chroma_db_utils import ChromaDBManager


class LinkedInVectorizer:
    """Manages vectorization of LinkedIn profiles into ChromaDB."""

    def __init__(self, collection_name: str = "linkedin"):
        """
        Initialize the LinkedIn vectorizer.

        Args:
            collection_name: Name of the ChromaDB collection for LinkedIn profiles
        """
        self.collection_name = collection_name
        self.chroma_manager = ChromaDBManager(collection_name=collection_name)
        self.storage_client = None
        self._initialize_gcp_client()

    def _initialize_gcp_client(self):
        """Initialize and return GCP storage client."""
        try:
            # Use environment variable for authentication
            self.storage_client = storage.Client()
            print("✅ Successfully connected to GCP using environment credentials")
        except Exception as e:
            print(f"❌ Error initializing GCP client: {str(e)}")
            print("Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly")

    def create_profile_text(self, profile: dict) -> str:
        """
        Create a text representation of a profile for embedding.

        Args:
            profile (dict): Processed profile data

        Returns:
            str: Text representation of the profile
        """
        sections = []

        # Basic info
        basic_info = f"Name: {profile.get('full_name', '')}\n"
        if profile.get("headline"):
            basic_info += f"Headline: {profile.get('headline')}\n"
        basic_info += f"Location: {profile.get('location_name', '')}\n"
        if profile.get("industry"):
            basic_info += f"Industry: {profile.get('industry')}\n"
        sections.append(basic_info)

        # Summary
        if profile.get("summary"):
            sections.append(f"Summary: {profile.get('summary')}")

        # Current position
        if profile.get("current_title") and profile.get("current_company"):
            sections.append(f"Current Position: {profile.get('current_title')} at {profile.get('current_company')}")

        # Experience
        if "experiences" in profile and profile["experiences"]:
            exp_texts = []
            for exp in profile["experiences"]:
                exp_text = f"{exp.get('title')} at {exp.get('company')}"
                if exp.get("description"):
                    exp_text += f": {exp.get('description')}"
                exp_texts.append(exp_text)
            sections.append("Experience: " + "\n".join(exp_texts))

        # Education
        if "educations" in profile and profile["educations"]:
            edu_texts = []
            for edu in profile["educations"]:
                edu_text = f"{edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('school', '')}"
                edu_texts.append(edu_text)
            sections.append("Education: " + "\n".join(edu_texts))

        # Skills
        if "skills" in profile and profile["skills"]:
            sections.append("Skills: " + ", ".join(profile["skills"]))

        # Publications
        if "publications" in profile and profile["publications"]:
            pub_texts = []
            for pub in profile["publications"]:
                pub_text = f"{pub.get('name', '')}"
                if pub.get("description"):
                    pub_text += f": {pub.get('description')}"
                pub_texts.append(pub_text)
            sections.append("Publications: " + "\n".join(pub_texts))

        # Projects
        if "projects" in profile and profile["projects"]:
            proj_texts = []
            for proj in profile["projects"]:
                proj_text = f"{proj.get('title', '')}"
                if proj.get("description"):
                    proj_text += f": {proj.get('description')}"
                proj_texts.append(proj_text)
            sections.append("Projects: " + "\n".join(proj_texts))

        return "\n\n".join(sections)

    def get_profiles_in_collection(self) -> Set[str]:
        """
        Get a set of URN IDs already in the ChromaDB collection.

        Returns:
            set: Set of URN IDs already in ChromaDB
        """
        try:
            # Query the collection with a simple query to get all IDs
            # This is a workaround since ChromaDBManager doesn't expose get_ids directly
            results = self.chroma_manager.collection.get(include=["metadatas"])

            if results and results["ids"]:
                return set(results["ids"])
            return set()

        except Exception as e:
            print(f"Error getting profiles from ChromaDB: {str(e)}")
            return set()

    def download_profiles_from_gcp(self, profiles_dir: str) -> bool:
        """
        Download processed LinkedIn profiles from GCP.

        Args:
            profiles_dir: Directory to store downloaded profiles

        Returns:
            bool: True if profiles were downloaded successfully
        """
        if not self.storage_client:
            print("GCP client not initialized. Cannot download profiles.")
            return False

        try:
            bucket_name = "expert-finder-bucket-1"
            gcp_folder = "linkedin_data_processing/processed_profiles"
            bucket = self.storage_client.bucket(bucket_name)

            # Create local directory if it doesn't exist
            os.makedirs(profiles_dir, exist_ok=True)

            # Get profiles already in ChromaDB
            existing_profiles = self.get_profiles_in_collection()
            print(f"Found {len(existing_profiles)} profiles already in ChromaDB")

            # List all processed profiles in GCP
            blobs = list(bucket.list_blobs(prefix=gcp_folder))
            processed_files = [blob for blob in blobs if blob.name.endswith("_processed.json")]

            print(f"Found {len(processed_files)} processed profiles in GCP")

            # Filter out profiles already in ChromaDB
            new_blobs = []
            for blob in processed_files:
                # Extract URN ID from filename
                basename = os.path.basename(blob.name)
                urn_id = basename.replace("_processed.json", "")

                if urn_id not in existing_profiles:
                    new_blobs.append(blob)

            print(f"Found {len(new_blobs)} new processed profiles to download")

            if not new_blobs:
                print("No new profiles to download.")
                return False

            # Download only new files with progress bar
            for blob in tqdm(new_blobs, desc="Downloading new processed profiles"):
                local_path = os.path.join(profiles_dir, os.path.basename(blob.name))
                blob.download_to_filename(local_path)

            print(f"Downloaded {len(new_blobs)} new processed profiles to {profiles_dir}")
            return True

        except Exception as e:
            print(f"Error downloading processed profiles: {str(e)}")
            return False

    def add_profiles_to_chroma(self, profiles_dir: str = "/tmp/processed_profiles") -> int:
        """
        Download and process LinkedIn profiles from GCP and add them to ChromaDB.

        Args:
            profiles_dir: Directory to store downloaded profiles

        Returns:
            int: Number of profiles added to ChromaDB
        """
        try:
            # Download profiles from GCP
            download_success = self.download_profiles_from_gcp(profiles_dir)
            if not download_success:
                print("Failed to download profiles or no new profiles available.")
                return 0

            # Get all processed JSON files
            json_files = glob.glob(os.path.join(profiles_dir, "*_processed.json"))
            print(f"Found {len(json_files)} processed files to vectorize")

            if not json_files:
                print("No profile files found to process.")
                return 0

            # Process each file
            documents = []
            ids = []
            metadatas = []

            for file_path in tqdm(json_files, desc="Preparing profiles for vectorization"):
                try:
                    # Load profile data
                    with open(file_path, "r", encoding="utf-8") as f:
                        profile = json.load(f)

                    # Skip if no URN ID
                    if not profile.get("urn_id"):
                        continue

                    # Create text representation
                    profile_text = self.create_profile_text(profile)

                    # Create metadata for filtering
                    metadata = {
                        "urn_id": profile.get("urn_id"),
                        "name": profile.get("full_name", ""),
                        "current_title": profile.get("current_title", ""),
                        "current_company": profile.get("current_company", ""),
                        "location": profile.get("location_name", ""),
                        "industry": profile.get("industry", ""),
                        "education_level": profile.get("education_level", ""),
                        "career_level": profile.get("career_level", ""),
                        "years_experience": str(profile.get("total_years_experience", 0)),
                    }

                    # Add to our lists
                    documents.append(profile_text)
                    ids.append(profile.get("urn_id"))
                    metadatas.append(metadata)

                except Exception as e:
                    print(f"Error preparing {file_path} for vectorization: {str(e)}")

            # Add documents to ChromaDB in batches to prevent memory issues
            if documents:
                batch_size = 100  # Adjust based on document size and available memory
                for i in range(0, len(documents), batch_size):
                    end_idx = min(i + batch_size, len(documents))
                    print(f"Adding batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} ({i}-{end_idx})")

                    self.chroma_manager.add_documents(
                        documents=documents[i:end_idx], ids=ids[i:end_idx], metadatas=metadatas[i:end_idx]
                    )

                print(f"Successfully added {len(documents)} new profiles to ChromaDB")

                # Get updated collection stats
                stats = self.chroma_manager.get_collection_stats()
                print(f"ChromaDB collection '{self.collection_name}' now has {stats['document_count']} documents")

                # Clean up temporary directory
                try:
                    print(f"Cleaning up temporary directory: {profiles_dir}")
                    shutil.rmtree(profiles_dir)
                    print(f"✅ Temporary directory {profiles_dir} has been removed")
                except Exception as e:
                    print(f"⚠️ Warning: Could not remove temporary directory: {str(e)}")

                return len(documents)

            print("No profiles to add to ChromaDB")
            return 0

        except Exception as e:
            print(f"Error in vectorization process: {str(e)}")
            return 0

    def search_profiles(
        self, query: str, filters: Optional[Dict[str, Any]] = None, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for LinkedIn profiles using the ChromaDB collection.

        Args:
            query: Search query
            filters: Optional filters to apply (dict format compatible with ChromaDB)
            n_results: Number of results to return

        Returns:
            List of matching profiles
        """
        try:
            # Convert filters to ChromaDB format if needed
            where_clause = None
            if filters:
                where_clauses = []

                for key, value in filters.items():
                    if isinstance(value, list):
                        # Multiple values: OR condition within the same field
                        if len(value) > 1:
                            where_clauses.append({"$or": [{key: v} for v in value]})
                        elif len(value) == 1:
                            # Single value in a list: use direct equality
                            where_clauses.append({key: value[0]})
                    elif isinstance(value, dict):
                        # Handle special operators like $gte
                        where_clauses.append({key: value})
                    else:
                        # Simple equality filter
                        where_clauses.append({key: value})

                # Combine all where clauses with AND
                if where_clauses:
                    if len(where_clauses) > 1:
                        where_clause = {"$and": where_clauses}
                    else:
                        # If there's only one clause, no need for $and
                        where_clause = where_clauses[0]

            # Query the collection using ChromaDBManager's collection directly
            results = self.chroma_manager.collection.query(query_texts=[query], n_results=n_results, where=where_clause)

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

    def get_metadata_values(self, field_name: str) -> List[str]:
        """
        Get all unique values for a specific metadata field from ChromaDB.
        Useful for UI dropdowns and filtering options.

        Args:
            field_name: The metadata field name to extract values for

        Returns:
            Sorted list of unique values for the specified field
        """
        try:
            # Get all items from the collection
            result = self.chroma_manager.collection.get(include=["metadatas"])

            if not result or not result["metadatas"]:
                print(f"No data found in the collection")
                return []

            # Extract all values for the specified field
            values = []
            for metadata in result["metadatas"]:
                if field_name in metadata and metadata[field_name] is not None:
                    values.append(metadata[field_name])

            # Get unique values and sort them
            unique_values = sorted(list(set(values)))

            print(f"Found {len(unique_values)} unique values for '{field_name}'")
            return unique_values

        except Exception as e:
            print(f"Error getting metadata values: {str(e)}")
            return []

    def test_search(self, query: str, n_results: int = 5, filters: Optional[Dict[str, Any]] = None):
        """
        Basic search test function for quick debugging and testing.

        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional filters to apply
        """
        print(f"Searching for: '{query}'")
        if filters:
            print(f"With filters: {filters}")

        # Perform search
        results = self.search_profiles(query, filters, n_results)

        # Print results
        print(f"\nFound {len(results)} matching profiles:")
        for result in results:
            print(f"\n{result['rank']}. {result['name']} ({result['similarity']:.2f})")
            print(f"   {result['current_title']} at {result['current_company']}")
            print(f"   Location: {result['location']}")
            print(f"   Industry: {result['industry']}")
            print(f"   Education: {result['education_level']}")
            print(f"   Summary: {result['profile_summary'][:150]}...")


# Add this at the end of the file for command-line testing

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Vectorizer Search Test")
    parser.add_argument("--query", default="machine learning", help="Search query")
    parser.add_argument("--collection", default="linkedin", help="ChromaDB collection name")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--industry", help="Filter by industry")
    parser.add_argument("--location", help="Filter by location")
    parser.add_argument("--education", help="Filter by education level")
    parser.add_argument("--experience", type=int, help="Filter by minimum years of experience")

    args = parser.parse_args()

    # Create vectorizer
    vectorizer = LinkedInVectorizer(collection_name=args.collection)

    # Build filters
    filters = {}
    if args.industry:
        filters["industry"] = args.industry
    if args.location:
        filters["location"] = args.location
    if args.education:
        filters["education_level"] = args.education
    if args.experience:
        filters["years_experience"] = {"$gte": str(args.experience)}

    # Run test search
    vectorizer.test_search(args.query, args.top_k, filters)
