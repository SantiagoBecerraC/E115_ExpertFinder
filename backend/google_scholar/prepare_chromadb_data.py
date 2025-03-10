"""
Script to prepare normalized dataset from Google Scholar JSON files for ChromaDB.
Combines article and author information into a single document suitable for vector storage.
"""

import json
import glob
import hashlib
from pathlib import Path
import pandas as pd
import datetime

def generate_unique_id(prefix, content_dict):
    """
    Generate a unique ID based on content using SHA-256 hash.
    
    Args:
        prefix: String prefix for the ID (e.g., 'article' or 'author')
        content_dict: Dictionary of content to hash
        
    Returns:
        String containing unique ID with prefix
    """
    # Convert dictionary values to string and concatenate
    content_str = '_'.join(str(value) for value in content_dict.values() if value)
    
    # Generate SHA-256 hash
    hash_object = hashlib.sha256(content_str.encode())
    hash_str = hash_object.hexdigest()[:12]  # Take first 12 characters of hash
    
    return f"{prefix}_{hash_str}"

def load_json_files(data_dir):
    """
    Load all JSON files from the data directory.
    
    Args:
        data_dir: Path to directory containing JSON files
        
    Returns:
        List of dictionaries containing the data from all JSON files
    """
    all_data = []
    json_files = glob.glob(str(data_dir / "Google_Scholar_Data_*.json"))
    
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_data.append(data)
    
    return all_data

def normalize_combined_data(article_data, authors_data, query):
    """
    Create a normalized document combining article and author information.
    
    Args:
        article_data: Dictionary containing article information
        authors_data: List of dictionaries containing author information
        query: Search query used to find the article
        
    Returns:
        Dictionary with normalized data for ChromaDB
    """
    # Create content dictionary for ID generation
    content_for_id = {
        "title": article_data.get("Article Title", ""),
        "year": article_data.get("Publication Year", ""),
        "url": article_data.get("Journal URL", ""),
        "authors": article_data.get("Scholar Profile (If available)", "")
    }
    
    unique_id = generate_unique_id("scholar", content_for_id)
    
    # Process author information
    author_details = []
    for author in authors_data:
        if author.get("Article ID") == article_data.get("Article ID"):
            author_details.append({
                "name": author.get("Author Name", ""),
                "affiliations": author.get("Affiliations", ""),
                "interests": author.get("Interests", ""),
                "website": author.get("Website", "")
            })
    
    # Combine article and author information in content
    content = f"""
Title: {article_data.get('Article Title', '')}
Abstract: {article_data.get('Article Snippet', '')}
Publication Info: {article_data.get('Publication Summary', '')}

Authors:
{format_author_details(author_details)}
    """.strip()
    
    # Add timestamp
    timestamp = datetime.datetime.now().isoformat()
    
    return {
        "id": unique_id,
        "title": article_data.get("Article Title", ""),
        "content": content,
        "metadata": {
            "query": query,
            "year": article_data.get("Publication Year"),
            "url": article_data.get("Journal URL"),
            "citations": article_data.get("Number of Citations"),
            "publication_info": article_data.get("Publication Summary"),
            "authors": [author.get("name") for author in author_details],
            "author_affiliations": [author.get("affiliations") for author in author_details if author.get("affiliations")],
            "author_interests": list(set(interest.strip() 
                                      for author in author_details 
                                      for interest in (author.get("interests", "").split(",") if author.get("interests") else [])
                                      if interest.strip())),
            "original_article_id": article_data.get("Article ID"),
            "timestamp": timestamp
        }
    }

def format_author_details(author_details):
    """
    Format author details into a readable string.
    
    Args:
        author_details: List of dictionaries containing author information
        
    Returns:
        Formatted string with author information
    """
    if not author_details:
        return "No author information available"
    
    formatted_authors = []
    for author in author_details:
        author_info = []
        if author.get("name"):
            author_info.append(f"Name: {author['name']}")
        if author.get("affiliations"):
            author_info.append(f"Affiliations: {author['affiliations']}")
        if author.get("interests"):
            author_info.append(f"Research Interests: {author['interests']}")
        if author.get("website"):
            author_info.append(f"Website: {author['website']}")
        
        formatted_authors.append("\\n".join(author_info))
    
    return "\\n\\n".join(formatted_authors)

def prepare_chromadb_data():
    """
    Main function to prepare data for ChromaDB.
    Processes all JSON files and creates normalized documents.
    
    Returns:
        List of normalized documents ready for ChromaDB
    """
    # Get data directory
    data_dir = Path(__file__).parent / 'data'
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Load all JSON files
    all_data = load_json_files(data_dir)
    
    # Initialize list for normalized documents
    normalized_docs = []
    
    # Process each JSON file
    for data in all_data:
        query = data.get("Query", "")
        articles = data.get("Articles", [])
        authors = data.get("Authors", [])
        
        # Create combined documents
        for article in articles:
            normalized_docs.append(normalize_combined_data(article, authors, query))
    
    # Save normalized data to JSON
    output_file = data_dir / 'normalized_data_for_chroma.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized_docs, f, indent=2, ensure_ascii=False)
    
    print(f"Normalized {len(normalized_docs)} documents")
    print(f"Data saved to: {output_file}")
    
    return normalized_docs

if __name__ == "__main__":
    try:
        normalized_docs = prepare_chromadb_data()
        print("Data preparation completed successfully")
    except Exception as e:
        print(f"Error preparing data: {str(e)}") 