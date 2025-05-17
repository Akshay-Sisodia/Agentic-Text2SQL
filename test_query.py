"""Test the API endpoints with a simple query."""

import requests
import json

def main():
    """Run a test query."""
    print("Testing agent info endpoint...")
    try:
        response = requests.get('http://localhost:8000/api/v1/agent/info')
        print(f"Agent info status: {response.status_code}")
        print(f"Agent info response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error with agent info: {str(e)}")
    
    print("\nTesting query endpoint...")
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/process',
            json={
                'query': 'List all customers',
                'db_type': 'sqlite',
                'db_path': 'sample_huge.db',
                'agent_type': 'base'
            }
        )
        print(f"Query status: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            # Print just a summary of the response to avoid overwhelming output
            data = response.json()
            print(f"Generated SQL: {data['user_response']['sql_generation']['sql']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error with query: {str(e)}")

if __name__ == "__main__":
    main() 