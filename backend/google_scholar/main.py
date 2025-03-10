"""
Google Scholar data extraction tool that fetches articles, authors, and citations.
Saves results to Excel and JSON files.

Required packages: pandas, openpyxl, python-dotenv, serpapi
Environment: SERPAPI_API_KEY in serpapi.env file
"""

# Standard library imports
import os
import re
import json
import datetime
from pathlib import Path
from keywords_list import keywords_list


# Third-party imports
import pandas as pd
from dotenv import load_dotenv

# Local application imports
from SerpAPI_GoogleScholar import GoogleScholar

# Load environment variables
load_dotenv()

# Create data directory
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

def extract_data(query, start_year, end_year, num_results, results_per_page):
    """
    Extract article data from Google Scholar.

    Args:
        query: Search term
        start_year: Start of date range
        end_year: End of date range
        num_results: Total results to fetch
        results_per_page: Results per page (1-20)

    Returns:
        Tuple of (articles, authors, citations) lists
    """
    # Initialize data containers
    articles_data = []    # Store article information
    authors_data = []     # Store author profiles
    citations_data = []   # Store citation formats

    # Track pagination
    total_fetched = 0     # Count of articles retrieved
    offset = 0            # Current page offset
    article_id = 0       

    # Fetch articles until we reach the requested number
    while total_fetched < num_results:
        # Calculate how many results to get in this iteration
        results_to_fetch = min(num_results - total_fetched, results_per_page)

        # Fetch batch of articles from Google Scholar
        articles_response = scholar_client.search_articles(query, start_year, end_year, results_to_fetch, offset)

        # Process each article in the response
        for article in articles_response.get("organic_results", []):
            article_id += 1
            # Extract basic article metadata
            title = article.get("title")
            snippet = article.get("snippet")
            publication_info = article.get("publication_info", {})
            publication_summary = publication_info.get("summary")

            # Extract publication year from summary using regex
            year_match = re.findall(r'(\d{4})', publication_info.get("summary"))
            year = year_match[0] if year_match else None
            
            # Get article URL and citation count
            journal_url = article.get("link")
            cited_by = article.get("inline_links", {}).get("cited_by", {}).get("total", 0)

            # Extract list of author names
            authors = [author['name'] for author in publication_info.get("authors", [])]

            # Store article information
            articles_data.append({
                "Article ID": article_id,
                "Article Title": title,
                "Article Snippet": snippet,
                "Publication Summary": publication_summary,
                "Publication Year": year,
                "Journal URL": journal_url,
                "Number of Citations": cited_by,
                "Scholar Profile (If available)": ", ".join(authors)
            })

            # Process each author of the article
            for author in publication_info.get("authors", []):
                # Fetch detailed author profile
                author_details = scholar_client.get_author_details(author['author_id'])
                
                # Extract author information
                author_name = author_details.get("author", {}).get("name")
                affiliations = author_details.get("author", {}).get("affiliations")
                website = author_details.get("author", {}).get("website")
                interests = [interest['title'] for interest in author_details.get("author", {}).get("interests", [])]

                # Store author profile
                authors_data.append({
                    "Article ID": article_id,
                    "Author Name": author_name,
                    "Affiliations": affiliations,
                    "Website": website,
                    "Interests": ", ".join(interests)
                })

                # Fetch and store citation formats
                citation_id = article.get("result_id")
                citations_response = scholar_client.get_citations(citation_id)
                
                # Store MLA citation format if available
                for citation in citations_response.get("citations", []):
                    if citation.get("title") == 'MLA':
                        citations_data.append({
                            "Article ID": article_id,
                            "Article Title": article.get("title"),
                            "Citation": citation.get("title"),
                            "Citation Details": citation.get("snippet")
                        })

        # Update pagination counters
        total_fetched += len(articles_response.get("organic_results", []))
        offset += results_per_page

        # Stop if no more results available
        if not articles_response.get("serpapi_pagination", {}).get("next"):
            break

    return articles_data, authors_data, citations_data

def remove_duplicates(data, key):
    """
    Remove duplicates from a list of dictionaries.

    Args:
        data: List of dictionaries
        key: Key to check for duplicates

    Returns:
        List with duplicates removed
    """
    # Track seen values using a set for O(1) lookup
    seen = set()
    unique_data = []

    # Keep only first occurrence of each unique value
    for item in data:
        identifier = item[key]
        if identifier not in seen:
            seen.add(identifier)
            unique_data.append(item)
    return unique_data

def save_to_excel(articles_data, authors_data, citations_data):
    """
    Save data to Excel file with sheets for articles, authors, and citations.

    Args:
        articles_data: List of article information
        authors_data: List of author information
        citations_data: List of citation information
    """
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'Google_Scholar_Data_{query.split(" ")[0]}_{timestamp}.xlsx'

    # Create Excel file with multiple sheets
    with pd.ExcelWriter(filename) as writer:
        # Save search parameters
        pd.DataFrame([{
            "Query Text": query,
            "Publication Year From": start_year,
            "Publication Year To": end_year,
            "No of results": num_results
        }]).to_excel(writer, sheet_name='SearchQuery', index=False)

        # Save data to respective sheets
        pd.DataFrame(articles_data).to_excel(writer, sheet_name='Articles', index=False)
        pd.DataFrame(authors_data).to_excel(writer, sheet_name='Authors', index=False)
        pd.DataFrame(citations_data).to_excel(writer, sheet_name='Citations', index=False)

        # Auto-adjust column widths
        for sheet in writer.sheets.values():
            sheet.autofit()

def save_to_json(articles_data, authors_data, citations_data):
    """
    Save data to JSON file in the data directory.

    Args:
        articles_data: List of article information
        authors_data: List of author information
        citations_data: List of citation information
    """
    # Prepare data structure
    all_data = {
        "Query": query,
        "Articles": articles_data,
        "Authors": authors_data,
        "Citations": citations_data
    }

    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f'Google_Scholar_Data_{query.split(" ")[0]}_{timestamp}.json'

    # Write data to JSON file
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(all_data, json_file, indent=4, ensure_ascii=False)
    
    print(f"Data saved to: {filename}")

if __name__ == "__main__":
    # Define search parameters
    query = 'XXXX'                # Search query
    start_year = '2022'             # Start year for filtering
    end_year = '2025'               # End year for filtering
    num_results = 50                # Total results to fetch
    results_per_page = 10           # Results per page (max 20)
  
    #keywords_list = ['machine learning deep learning']

    # Example usage:
    for keyword in keywords_list:
        query = keyword
        # Initialize Google Scholar client
        scholar_client = GoogleScholar(SERPAPI_API_KEY)

        # Extract data from Google Scholar
        articles_data, authors_data, citations_data = extract_data(
        query, start_year, end_year, num_results, results_per_page
        )

        # Remove duplicate entries
        articles_data = remove_duplicates(articles_data, "Article Title")
        authors_data = remove_duplicates(authors_data, "Author Name")
        citations_data = remove_duplicates(citations_data, "Citation")

        # Save extracted data to JSON
        save_to_json(articles_data, authors_data, citations_data)