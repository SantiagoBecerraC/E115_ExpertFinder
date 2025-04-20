#!/usr/bin/env python3
"""
Command-line interface for LinkedIn data processing and search pipeline.
Orchestrates the entire workflow from data processing to vectorization and search.
"""

import os
import argparse
import sys
from pathlib import Path
from google.cloud import storage

# Add parent directory to path
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
sys.path.append(str(parent_dir))

# Import local modules
from linkedin_data_processing.process_linkedin_profiles import (
    initialize_gcp_client,
    download_unprocessed_profiles_from_gcp,
    download_profiles_from_gcp,
    process_profiles_and_upload_to_gcp,
    get_credibility_distribution
)
from linkedin_data_processing.linkedin_vectorizer import LinkedInVectorizer
from linkedin_data_processing.expert_finder_linkedin import ExpertFinderAgent
from linkedin_data_processing.dynamic_credibility import OnDemandCredibilityCalculator

def process_command(args):
    """Process LinkedIn profiles and upload to GCP."""
    # Download profiles from GCP to temporary directory
    storage_client = initialize_gcp_client()
    if not storage_client:
        print("Failed to initialize GCP client. Exiting.")
        return False

    if args.force:
        # Download all profiles if force flag is set
        temp_dir = download_profiles_from_gcp(storage_client)
    else:
        # Download only unprocessed profiles
        temp_dir = download_unprocessed_profiles_from_gcp(storage_client)
            
    if temp_dir:
        # Process and upload directly to GCP
        success = process_profiles_and_upload_to_gcp(temp_dir)
        return success
    else:
        print("No new profiles to process.")
        return True

def vectorize_command(args):
    """Vectorize processed LinkedIn profiles to ChromaDB."""
    # Initialize vectorizer
    vectorizer = LinkedInVectorizer(collection_name=args.collection)
    
    # Add profiles to ChromaDB
    processed_count = vectorizer.add_profiles_to_chroma(args.profiles_dir)
    
    return processed_count > 0

def search_command(args):
    """Search for LinkedIn profiles."""
    # Parse filters if provided
    filters = {}
    if args.industry:
        filters["industry"] = args.industry
    if args.location:
        filters["location"] = args.location
    if args.education_level:
        filters["education_level"] = args.education_level
    if args.career_level:
        filters["career_level"] = args.career_level
    if args.years_experience:
        filters["years_experience"] = {"$gte": args.years_experience}
    
    # Choose between simple search and agent search
    if args.agent:
        # Use the ExpertFinderAgent for enhanced search with reranking
        agent = ExpertFinderAgent(chroma_dir=None)  # No need for chroma_dir
        response = agent.find_experts(args.query, initial_k=args.initial_k, final_k=args.top_k)
        
        print("\n" + "="*50)
        print("Expert Finder Results:")
        print("="*50)
        print(response)
        print("="*50)
    else:
        # Use simple search with the vectorizer
        vectorizer = LinkedInVectorizer(collection_name=args.collection)
        results = vectorizer.search_profiles(args.query, filters, n_results=args.top_k)
        
        print(f"\nFound {len(results)} matching profiles:")
        for result in results:
            print(f"\n{result['rank']}. {result['name']} ({result['similarity']:.2f})")
            print(f"   {result['current_title']} at {result['current_company']}")
            print(f"   Location: {result['location']}")
            print(f"   Industry: {result['industry']}")
            print(f"   Summary: {result['profile_summary'][:150]}...")
    
    return True

def pipeline_command(args):
    """Run the entire LinkedIn processing pipeline."""
    print("Starting LinkedIn processing pipeline...")
    
    # Step 1: Process profiles
    print("\n=== Step 1: Processing LinkedIn profiles ===")
    process_success = process_command(args)
    if not process_success:
        print("Profile processing failed. Stopping pipeline.")
        return False
    
    # Step 2: Vectorize profiles
    print("\n=== Step 2: Vectorizing LinkedIn profiles ===")
    vectorize_success = vectorize_command(args)
    if not vectorize_success and not args.continue_on_error:
        print("Profile vectorization failed. Stopping pipeline.")
        return False
    
    # Step 3: Search (if query provided)
    if args.query:
        print("\n=== Step 3: Searching LinkedIn profiles ===")
        search_command(args)
    
    print("\nLinkedIn processing pipeline completed successfully!")
    return True

def reset_collection_command(args):
    """Reset the ChromaDB collection for LinkedIn profiles."""
    vectorizer = LinkedInVectorizer(collection_name=args.collection)
    vectorizer.chroma_manager.reset_collection()
    print(f"Reset collection '{args.collection}'")
    return True

def update_credibility_stats_command(args):
    """Update the credibility statistics from the database."""
    print("Updating credibility statistics...")
    
    # Initialize credibility calculator
    calculator = OnDemandCredibilityCalculator(stats_file=args.stats_file)
    
    # Update stats
    success = calculator.fetch_profiles_and_update_stats()
    
    if success:
        print("✅ Credibility statistics updated successfully.")
        # Show some summary data
        print(f"Stats file location: {calculator.stats_manager.stats_file}")
        print(f"Total profiles: {calculator.stats_manager.stats['total_profiles']}")
        
        # Experience distribution
        exp_dist = calculator.stats_manager.stats["metrics"]["experience"]["distribution"]
        print("\nExperience distribution:")
        for bracket, count in exp_dist.items():
            print(f"  {bracket} years: {count} profiles")
        
        # Education distribution
        edu_dist = calculator.stats_manager.stats["metrics"]["education"]["distribution"]
        print("\nEducation distribution:")
        for level, count in edu_dist.items():
            print(f"  {level}: {count} profiles")
    else:
        print("❌ Failed to update credibility statistics.")
    
    return success

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Data Processing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--collection", default="linkedin", 
                     help="Name of the ChromaDB collection")
    
    # Process command
    process_parser = subparsers.add_parser("process", parents=[common_parser],
                                         help="Process LinkedIn profiles and upload to GCP")
    process_parser.add_argument("--force", action="store_true",
                              help="Force processing of all profiles, even if already processed")
    
    # Vectorize command
    vectorize_parser = subparsers.add_parser("vectorize", parents=[common_parser],
                                           help="Vectorize processed LinkedIn profiles to ChromaDB")
    vectorize_parser.add_argument("--profiles_dir", default="/tmp/processed_profiles", 
                               help="Directory containing processed LinkedIn profiles")
    
    # Search command
    search_parser = subparsers.add_parser("search", parents=[common_parser],
                                        help="Search for LinkedIn profiles")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--industry", help="Filter by industry")
    search_parser.add_argument("--location", help="Filter by location")
    search_parser.add_argument("--education_level", help="Filter by education level")
    search_parser.add_argument("--career_level", help="Filter by career level")
    search_parser.add_argument("--years_experience", type=int, help="Filter by minimum years of experience")
    search_parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    search_parser.add_argument("--initial_k", type=int, default=20, help="Number of initial results for reranking")
    search_parser.add_argument("--agent", action="store_true", help="Use ExpertFinderAgent with reranking")
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", parents=[common_parser],
                                          help="Run the entire LinkedIn processing pipeline")
    pipeline_parser.add_argument("--force", action="store_true",
                              help="Force processing of all profiles, even if already processed")
    pipeline_parser.add_argument("--profiles_dir", default="/tmp/processed_profiles", 
                               help="Directory containing processed LinkedIn profiles")
    pipeline_parser.add_argument("--query", help="Optional search query to run after processing")
    pipeline_parser.add_argument("--continue_on_error", action="store_true",
                               help="Continue pipeline even if a step fails")
    pipeline_parser.add_argument("--top_k", type=int, default=5, help="Number of search results to return")
    pipeline_parser.add_argument("--initial_k", type=int, default=20, help="Number of initial results for reranking")
    
    # Add reset command
    subparsers.add_parser("reset", parents=[common_parser],
                         help="Reset the collection by deleting and recreating it")
    
    # Add new update-credibility-stats command
    cred_stats_parser = subparsers.add_parser("update-credibility-stats", parents=[common_parser],
                                            help="Update the credibility statistics from the database")
    cred_stats_parser.add_argument("--stats-file", 
                                 help="Path to the stats file (default is in the package directory)")
    
    args = parser.parse_args()
    
    # Execute the specified command
    if args.command == "process":
        process_command(args)
    elif args.command == "vectorize":
        vectorize_command(args)
    elif args.command == "search":
        search_command(args)
    elif args.command == "pipeline":
        pipeline_command(args)
    elif args.command == "reset":
        reset_collection_command(args)
    elif args.command == "update-credibility-stats":
        update_credibility_stats_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()