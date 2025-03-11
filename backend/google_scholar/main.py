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


# Load environment variables from the secrets folder at project root
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # Go up four levels to reach EXPERTFINDER-UV1
env_path = project_root / 'secrets' / '.env'

load_dotenv(dotenv_path=env_path)

# Get API key from environment variables
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY not found in environment variables")

# Create data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "google-scholar-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def extract_data(query, start_year, end_year, num_results, results_per_page):
    # Initialize a list to hold articles data
    articles_data = []
    total_fetched = 0
    offset = 0

    while total_fetched < num_results:
        # Calculate the number of results to fetch in this iteration
        results_to_fetch = min(num_results - total_fetched, results_per_page)

        # Use the scholar client to search for articles based on the query and year range
        articles_response = scholar_client.search_articles(
            query, start_year, end_year, results_to_fetch, offset
        )

        # Loop through each article in the response
        for article in articles_response.get("organic_results", []):
            # Extract relevant information from the article
            title = article.get("title")
            snippet = article.get("snippet")
            publication_info = article.get("publication_info", {})
            publication_summary = publication_info.get("summary")

            # Extract the publication year using regex
            year_match = re.findall(r"(\d{4})", publication_info.get("summary"))
            year = year_match[0] if year_match else None
            journal_url = article.get("link")
            cited_by = article.get("inline_links", {}).get("cited_by", {}).get("total", 0)

            # Extract authors' names and their details
            authors = []
            for author in publication_info.get("authors", []):
                author_details = scholar_client.get_author_details(author["author_id"])
                author_name = author_details.get("author", {}).get("name")
                affiliations = author_details.get("author", {}).get("affiliations")
                website = author_details.get("author", {}).get("website")
                interests = [
                    interest["title"]
                    for interest in author_details.get("author", {}).get("interests", [])
                ]

                # Append author details to the authors list
                authors.append({
                    "Author Name": author_name,
                    "Affiliations": affiliations,
                    "Website": website,
                    "Interests": ", ".join(interests),
                })

            # Create a nested structure for each article
            article_data = {
                "Article Title": title,
                "Article Snippet": snippet,
                "Publication Summary": publication_summary,
                "Publication Year": year,
                "Journal URL": journal_url,
                "Number of Citations": cited_by,
                "Authors": authors,  # Include authors as a nested list
                "Citations": [],  # Initialize an empty list for citations
            }

            # Get citations for the current article
            citation_id = article.get("result_id")
            citations_response = scholar_client.get_citations(citation_id)
            for citation in citations_response.get("citations", []):
                # Append citation data to the article's citations list if the citation type is MLA
                if citation.get("title") == "MLA":
                    article_data["Citations"].append({
                        "Citation": citation.get("title"),
                        "Citation Details": citation.get("snippet"),
                    })

            # Append the article data to the articles_data list
            articles_data.append(article_data)

        total_fetched += len(articles_response.get("organic_results", []))
        offset += results_per_page  # Increment offset by the number of results per page

        if not articles_response.get("serpapi_pagination", {}).get("next"):
            break  # No more pages to fetch

    # Return the collected articles data
    return articles_data  # Return only articles_data

def save_to_excel(articles_data, query, start_year, end_year, num_results):
    # Create a timestamp for the output file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create an Excel writer object to save data to an Excel file
    with pd.ExcelWriter(f'Google_Scholar_Data_{query.split(" ")[0]}_{timestamp}.xlsx') as writer:
        # Save the search query information to a separate sheet
        pd.DataFrame([{
            "Query Text": query,
            "Publication Year From": start_year,
            "Publication Year To": end_year,
            "No of results": num_results,
        }]).to_excel(writer, sheet_name="SearchQuery", index=False)

        # Save articles data to its respective sheet
        pd.DataFrame(articles_data).to_excel(writer, sheet_name="Articles", index=False)

        # Autofit the columns in each sheet for better readability
        for sheet in writer.sheets.values():
            sheet.autofit()

def save_to_json(articles_data, query):
    # Create a dictionary to hold all data
    all_data = {
        "Query": query,
        "Publication_Year_From": start_year,
        "Publication_Year_To": end_year,
        "Results_Fetched": num_results,
        "Articles": articles_data,  # Articles data includes nested author details
    }

    # Save the combined data to a JSON file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f'Google_Scholar_Data_{query.split(" ")[0]}_{timestamp}.json'

     # Write data to JSON file
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, indent=4, ensure_ascii=False)

    print(f"Data saved to: {filename}")
    

if __name__ == "__main__":
    # Define search parameters
    query = "XXXX"  # Search query
    start_year = "2022"  # Start year for filtering
    end_year = "2025"  # End year for filtering
    num_results = 50  # Total results to fetch
    results_per_page = 10  # Results per page (max 20)

    # Example usage:
    for keyword in keywords_list:
        query = keyword
        # Initialize Google Scholar client
        scholar_client = GoogleScholar(SERPAPI_API_KEY)

        # Extract data from Google Scholar
        articles_data = extract_data(
            query, start_year, end_year, num_results, results_per_page
        )

        # Save extracted data to JSON
        save_to_json(articles_data, query)
        
