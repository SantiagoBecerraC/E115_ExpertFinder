"""
Interface for Google Scholar data extraction using SerpAPI.
Provides functionality to search articles, get author details, and citations.
Requires a SerpAPI key for authentication.
"""

# Import the SerpAPI search client
from serpapi import GoogleSearch


class GoogleScholar:
    """Handles Google Scholar API interactions through SerpAPI."""

    def __init__(self, api_key):
        """Initialize with SerpAPI key."""
        # Store API key for use in all requests
        self.api_key = api_key

    def search_articles(self, query, start_year, end_year, num_results, offset):
        """
        Search for articles on Google Scholar.

        Args:
            query: Search term
            start_year: Start of date range
            end_year: End of date range
            num_results: Number of results to return
            offset: Pagination offset

        Returns:
            Dict with article data including titles, snippets, and publication info
        """
        # Set up search parameters for Google Scholar
        params = {
            "engine": "google_scholar",    # Specify Google Scholar search engine
            "q": query,                    # Search query
            "hl": "en",                    # Set language to English
            "as_ylo": start_year,          # Start year for filtering
            "as_yhi": end_year,            # End year for filtering
            "limit": num_results,          # Number of results per request
            "api_key": self.api_key,       # Authentication
            "start": offset               # Pagination offset
        }

        # Create search instance and execute
        search = GoogleSearch(params)
        # Return results as a dictionary
        return search.get_dict()

    def get_author_details(self, author_id):
        """
        Get author information from Google Scholar.

        Args:
            author_id: Author's unique identifier

        Returns:
            Dict with author's name, affiliations, website, and research interests
        """
        # Set up parameters for author profile request
        params = {
            "engine": "google_scholar_author",  # Use author profile engine
            "author_id": author_id,            # Author's Google Scholar ID
            "hl": "en",                        # Set language to English
            "api_key": self.api_key            # Authentication
        }

        # Execute search and get author profile
        search = GoogleSearch(params)
        return search.get_dict()

    def get_citations(self, citation_id):
        """
        Get citation information for an article.

        Args:
            citation_id: Article's citation identifier

        Returns:
            Dict with citation formats and details
        """
        # Set up parameters for citation request
        params = {
            "engine": "google_scholar_cite",    # Use citation engine
            "q": citation_id,                   # Article's citation ID
            "api_key": self.api_key             # Authentication
        }

        # Get citation formats for the article
        search = GoogleSearch(params)
        return search.get_dict()