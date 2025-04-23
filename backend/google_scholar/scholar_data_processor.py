import json
from collections import defaultdict
from pathlib import Path


def process_scholar_data(json_file):
    # Read JSON file
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dictionary to store author information with their articles
    authors_with_articles = defaultdict(lambda: {"author_info": {}, "articles": []})

    # Get articles from the correct key in the JSON structure
    articles = data.get("Articles", [])  # Use get() with default empty list
    if not articles and isinstance(
        data, list
    ):  # If data is directly a list of articles
        articles = data

    if not articles:
        print(f"Warning: No articles found in {json_file}")
        print(
            f"Available keys in data: {list(data.keys()) if isinstance(data, dict) else 'Data is a list'}"
        )
        return {}

    # Process each article
    for article in articles:
        try:
            article_info = {
                "title": article.get("Article Title", ""),
                "snippet": article.get("Article Snippet", ""),
                "year": article.get("Publication Year", ""),
                "journal_url": article.get("Journal URL", ""),
                "citations_count": article.get("Number of Citations", 0),
                "publication_summary": article.get("Publication Summary", ""),
                "citations": article.get("Citations", []),
            }

            # Process authors
            authors = article.get("Authors", [])
            for author in authors:
                if not author.get("Author Name"):
                    continue

                author_name = author["Author Name"]

                # Update author information if not already stored
                if not authors_with_articles[author_name]["author_info"]:
                    authors_with_articles[author_name]["author_info"] = {
                        "author": author_name,
                        "affiliations": author.get("Affiliations", ""),
                        "website": author.get("Website", ""),
                        "interests": author.get("Interests", ""),
                    }

                # Add article to author's list of articles
                authors_with_articles[author_name]["articles"].append(article_info)

        except Exception as e:
            print(f"Error processing article: {e}")
            print(f"Article data: {article}")
            continue

    # Convert defaultdict to regular dict
    return dict(authors_with_articles)


def prepare_chroma_data(authors_data):
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
            author_text = f"{author_info['author']}. {author_info['affiliations']}. Interests: {author_info['interests']}. Publications: {'; '.join(article_titles)}"

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

                article_text = f"{article['title']}. {article['snippet']}. {article['publication_summary']}"

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
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
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
