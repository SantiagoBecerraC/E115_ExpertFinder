import os
from dotenv import load_dotenv
from linkedin_data_processing.expert_finder_linkedin import ExpertFinderAgent

# Load environment variables
load_dotenv()

def main():
    # Initialize the LinkedIn expert finder agent
    agent = ExpertFinderAgent(
        chroma_dir=os.getenv("CHROMA_DIR", "chroma_db"),
        project_id=os.getenv("GCP_PROJECT"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )
    
    # Test query
    query = "machine learning experts in San Francisco"
    
    print(f"Searching for: {query}")
    
    # Find experts
    response = agent.find_experts(query, initial_k=10, final_k=5)
    
    # Print the response
    print("\n" + "="*50)
    print("LinkedIn Expert Finder Results:")
    print("="*50)
    print(response)
    print("="*50)

if __name__ == "__main__":
    main() 