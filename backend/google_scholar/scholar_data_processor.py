import json
from collections import defaultdict
from pathlib import Path


def process_scholar_data(json_file):
    """
    Read and process Google Scholar data from a JSON file.
    Returns a dictionary with author and article information.
    """
    try:
        # Read JSON file
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Check if the data has the expected structure
        if "search_query" not in data and "Query" not in data:
            print(f"Error: Missing 'search_query' or 'Query' in {json_file}")
            # Return empty structure for backward compatibility
            return {"articles": [], "authors": []}

        # Initialize result structure - a dictionary of authors with their articles
        processed_data = {}
        
        # Extract search query for context
        search_query = data.get("search_query", data.get("Query", ""))
        
        # Process articles from new format
        if "Articles" in data:
            all_articles = []  # For backward compatibility
            
            for article in data["Articles"]:
                # Extract authors
                authors_list = []
                if isinstance(article.get("Authors", []), list):
                    # Handle case where Authors is a list of strings
                    if all(isinstance(a, str) for a in article.get("Authors", [])):
                        authors_list = article.get("Authors", [])
                    # Handle case where Authors is a list of dictionaries with Author Name field
                    elif all(isinstance(a, dict) for a in article.get("Authors", [])):
                        authors_list = [a.get("Author Name", "") for a in article.get("Authors", []) if a.get("Author Name")]
                
                # Create article info for backward compatibility
                article_info = {
                    "title": article.get("Article Title", article.get("Title", "")),
                    "snippet": article.get("Article Snippet", article.get("Snippet", "")),
                    "url": article.get("Journal URL", article.get("Link", "")),
                    "authors": authors_list,
                    "year": article.get("Publication Year", article.get("Year", "")),
                    "journal": article.get("Publication Summary", article.get("Publication", "")),
                    "citation_count": article.get("Number of Citations", article.get("Cited_By", 0))
                }
                all_articles.append(article_info)
                
                # Process each author for the detailed structure
                for author_name in authors_list:
                    # Initialize author if not seen before
                    if author_name not in processed_data:
                        # Find author details if available
                        author_details = {}
                        if isinstance(article.get("Authors", []), list) and all(isinstance(a, dict) for a in article.get("Authors", [])):
                            for author_dict in article.get("Authors", []):
                                if author_dict.get("Author Name") == author_name:
                                    author_details = author_dict
                                    break
                        
                        processed_data[author_name] = {
                            "author_info": {
                                "author": author_name,
                                "affiliations": author_details.get("Affiliations", ""),
                                "interests": author_details.get("Interests", "").split(", ") if isinstance(author_details.get("Interests", ""), str) else [],
                                "h_index": 0,     # Will be populated if available
                                "i10_index": 0,   # Will be populated if available
                            },
                            "articles": []
                        }
                    
                    # Add this article to the author's list
                    author_article_info = {
                        "title": article_info["title"],
                        "url": article_info["url"],
                        "snippet": article_info["snippet"],
                        "publication_year": article_info["year"],
                        "publication_venue": article_info["journal"],
                        "citations_count": article_info["citation_count"],
                        "publication_summary": f"{article_info['journal']} ({article_info['year']})",
                        "authors": authors_list,
                        "citations": []  # Will be populated if available
                    }
                    
                    processed_data[author_name]["articles"].append(author_article_info)
            
            # For backward compatibility, create a result with articles and authors lists
            processed_authors = []
            for author_name, author_data in processed_data.items():
                processed_authors.append({
                    "name": author_name,
                    "affiliations": author_data["author_info"]["affiliations"],
                    "interests": author_data["author_info"]["interests"],
                    "h_index": author_data["author_info"]["h_index"],
                    "i10_index": author_data["author_info"]["i10_index"]
                })
            
            return {
                "articles": all_articles,
                "authors": processed_authors,
                "detailed": processed_data  # Keep the detailed structure for system tests
            }
        
        # Handle the direct format with articles and authors already separated
        if "articles" in data and "authors" in data:
            return {
                "articles": data["articles"],
                "authors": data["authors"]
            }
            
        # Backward compatibility - if we don't find the expected structure, return empty lists
        return {"articles": [], "authors": []}

    except Exception as e:
        print(f"Error processing file {json_file}: {e}")
        if 'data' in locals():
            print(f"Available keys in data: {data.keys() if isinstance(data, dict) else 'Not a dictionary'}")
        # Return empty structure for backward compatibility
        return {"articles": [], "authors": []}


def prepare_chroma_data(authors_data, query=""):
    """
    Prepare data in format ready for ChromaDB without actually loading it.
    Returns two lists of dictionaries for authors and articles collections.
    """
    authors_collection_data = []
    articles_collection_data = []

    # Process authors and their articles
    for author_name, data in authors_data.items():
        try:
            author_info = data["author_info"]
            author_articles = data["articles"]

            # Calculate total citations for author
            total_citations = sum(
                article["citations_count"] for article in author_articles
            )

            # Prepare author metadata
            author_metadata = {
                **author_info,
                "citations": total_citations,
                "num_articles": len(author_articles),
            }

            # Prepare author document text including articles
            article_titles = [
                article["title"] for article in author_articles if article["title"]
            ]
            author_text = f"Query: {query}. {author_info['author']}. {author_info['affiliations']}. Interests: {author_info['interests']}. Publications: {'; '.join(article_titles)}"

            authors_collection_data.append(
                {
                    "id": f"author_{hash(author_name)}",
                    "content": author_text,
                    "metadata": author_metadata,
                }
            )

            # Process articles for this author
            for article in author_articles:
                if not article["title"]:  # Skip articles without titles
                    continue

                # Prepare article document text
                article_text = (
                    f"Query: {query}{article['title']}. {article['snippet']}. {article['publication_summary']}. "
                )

                # Add article metadata with citations
                article_metadata = {
                    **article,
                    "author_name": author_name,
                    "citation_details": [
                        citation["Citation Details"]
                        for citation in article.get("citations", [])
                    ],
                }

                articles_collection_data.append(
                    {
                        "id": f"article_{hash(article['title'])}",
                        "content": article_text,
                        "metadata": article_metadata,
                    }
                )

        except Exception as e:
            print(f"Error processing author {author_name}: {e}")
            continue

    return {"authors": authors_collection_data, "articles": articles_collection_data}


def save_to_json(data, output_file):
    # Create parent directory if it doesn't exist
    from pathlib import Path
    
    # Convert string path to Path object if necessary
    output_path = Path(output_file) if not isinstance(output_file, Path) else output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main():
    try:
        # Find all JSON files in the google-scholar-data directory
        data_dir = Path(__file__).parent.parent.parent.parent / "google-scholar-data"
        json_files = list(data_dir.glob("Google_Scholar_Data_*.json"))

        if not json_files:
            print(f"No Google Scholar data files found in {data_dir}")
            return

        print(f"Found {len(json_files)} files to process")

        # Initialize combined data structure
        combined_authors_data = {}

        # Process each JSON file
        for json_file in json_files:
            print(f"\nProcessing file: {json_file}")

            # Process the data from this file
            authors_data = process_scholar_data(json_file)

            if not authors_data:
                print("No data was processed from this file. Skipping...")
                continue

            # Merge the data into combined_authors_data
            for author_name, author_data in authors_data.items():
                if author_name not in combined_authors_data:
                    combined_authors_data[author_name] = author_data
                else:
                    # Merge articles lists, avoiding duplicates based on title
                    existing_titles = {
                        article["title"]
                        for article in combined_authors_data[author_name]["articles"]
                    }
                    new_articles = [
                        article
                        for article in author_data["articles"]
                        if article["title"] not in existing_titles
                    ]
                    combined_authors_data[author_name]["articles"].extend(new_articles)

        if not combined_authors_data:
            print(
                "No data was processed from any file. Please check the input file format."
            )
            return

        # Prepare data for ChromaDB
        print("\nPreparing combined data for ChromaDB...")
        chroma_ready_data = prepare_chroma_data(combined_authors_data)

        # Create output directory and save processed data
        output_dir = data_dir / "processed_data"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save files inside the processed_data directory
        save_to_json(combined_authors_data, output_dir / "data.processed.json")
        save_to_json(chroma_ready_data, output_dir / "data.chroma.json")

        print(
            f"\nOriginal processed data saved to: {output_dir / 'data.processed.json'}"
        )
        print(f"ChromaDB-ready data saved to: {output_dir / 'data.chroma.json'}")
        print(f"Total authors: {len(chroma_ready_data['authors'])}")
        print(f"Total articles: {len(chroma_ready_data['articles'])}")
        print("\nSummary of processed files:")
        for json_file in json_files:
            print(f"- {json_file.name}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
