#!/usr/bin/env python3

import requests
import json

def test_sophie_prach_search():
    """Test the exact query that's failing"""
    
    print("=== TESTING SOPHIE PRACH SEARCH ===")
    
    # Test our smart MCP server
    url = "http://localhost:9000/mcp/execute"
    payload = {"query": "Dr Sophie Prach"}
    
    print(f"Sending request to: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("=== RESPONSE STRUCTURE ===")
            print(json.dumps(data, indent=2))
            
            # Extract results if available
            choices = data.get("choices", [])
            if choices and len(choices) > 0:
                choice = choices[0]
                structured_data = choice.get("data", {}).get("structured_data", {})
                
                if structured_data.get("success"):
                    results = structured_data.get("data", {}).get("results", [])
                    print(f"\n=== FOUND {len(results)} RESULTS ===")
                    
                    for i, result in enumerate(results):
                        print(f"\nResult {i+1}:")
                        print(f"  ID: {result.get('id', 'N/A')}")
                        print(f"  Name: {result.get('name', 'N/A')}")
                        print(f"  Specialty: {result.get('specialty', 'N/A')}")
                        print(f"  Active: {result.get('active', 'N/A')}")
                        print(f"  Resource Type: {result.get('resource_type', 'N/A')}")
                        print(f"  Address: {result.get('address', 'N/A')}")
                else:
                    print("Search failed:")
                    print(structured_data.get("message", "No error message"))
            else:
                print("No choices in response")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_sophie_prach_search()
