import requests
import json

# Based on our tests, these connection URLs work
sqlite_connection_url = "sqlite:///C:/Users/akshaySisodia/Desktop/projects/Agentic-Text2SQL/sample_huge.db"
relative_url = "sqlite:///sample_huge.db"

# API endpoint to test database connection
api_url = "http://localhost:8000/api/v1/database/test"

# Test payload with the working connection URL
payload = {
    "db_type": "sqlite",
    "db_name": "sample_huge",
    "database_url": sqlite_connection_url
}

# Print what we're going to send
print(f"Testing API with payload:")
print(json.dumps(payload, indent=2))

try:
    # Send POST request to the API
    response = requests.post(api_url, json=payload)
    
    # Print response
    print(f"\nResponse Status: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    # Try the relative URL if the first one fails
    if not response.json().get("success", False):
        print("\nTrying with relative URL...")
        payload["database_url"] = relative_url
        response = requests.post(api_url, json=payload)
        print(f"Response Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
except Exception as e:
    print(f"Error calling API: {str(e)}")
    print("\nMake sure the backend server is running at: http://localhost:8000")
    print("You can start it with: uvicorn main:app --reload")

print("\nRecommended connection URL for your SQLite database:")
print(sqlite_connection_url) 