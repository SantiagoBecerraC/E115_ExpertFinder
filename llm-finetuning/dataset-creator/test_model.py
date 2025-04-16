import os
import vertexai
from vertexai.generative_models import GenerativeModel

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"

# Initialize Vertex AI
vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)

# Test model access
try:
    print(f"Testing access to Gemini model in project: {GCP_PROJECT}")
    model = GenerativeModel("gemini-1.5-flash-001")
    
    # Test query
    query = "Who are the top researchers in natural language processing?"
    print(f"\nSending test query: {query}")
    
    response = model.generate_content([query])
    print("\nModel Response:")
    print(response.text)
    
    print("\nSuccess! Model access is working correctly.")
except Exception as e:
    print(f"\nError accessing model: {e}")
    print("\nPlease check:")
    print("1. Service account permissions in IAM")
    print("2. Vertex AI API is enabled")
    print("3. You have accepted the terms for Gemini models")
    print("4. Your project has billing enabled") 