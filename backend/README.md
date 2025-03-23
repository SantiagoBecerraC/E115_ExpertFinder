# Expert Finder API

This is the backend API for the Expert Finder application, which provides endpoints to search for experts from various sources.

## Setup

1. Make sure you're in the backend directory:
```bash
cd backend
```

2. Activate the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /
Welcome message endpoint that provides API information and available endpoints.

### POST /search
Search for experts based on a query.

Request body:
```json
{
    "query": "your search query",
    "max_results": 5  // optional, defaults to 5
}
```

Response:
```json
[
    {
        "name": "Expert Name",
        "title": "Expert Title",
        "source": "linkedin|scholar",
        "company": "Company Name",  // for LinkedIn
        "location": "Location",     // for LinkedIn
        "skills": ["skill1", "skill2"],  // for LinkedIn
        "citations": 1000,         // for Google Scholar
        "interests": ["interest1", "interest2"],  // for Google Scholar
        "publications": 25         // for Google Scholar
    }
]
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc` 