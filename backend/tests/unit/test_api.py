import requests
import json

BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    print("\nTesting root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))

def test_search_endpoint():
    print("\nTesting search endpoint...")
    payload = {
        "query": "What are the recent advances in deep learning?",
        "max_results": 3
    }
    response = requests.post(f"{BASE_URL}/search", json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))

def test_search_endpoint_invalid():
    print("\nTesting search endpoint with invalid data...")
    payload = {
        "query": "",  # Empty query
        "max_results": -1  # Invalid max_results
    }
    response = requests.post(f"{BASE_URL}/search", json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    try:
        test_root_endpoint()
        test_search_endpoint()
        test_search_endpoint_invalid()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Make sure the FastAPI server is running.")
        print("Run: uvicorn main:app --reload") 