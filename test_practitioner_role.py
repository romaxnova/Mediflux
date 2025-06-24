#!/usr/bin/env python3

import requests
import json

def test_practitioner_role_search():
    """Test practitioner role search by specialty"""
    
    print("=== TESTING PRACTITIONER ROLE BY SPECIALTY ===")
    
    # Test our smart MCP server
    url = "http://localhost:9000/mcp/execute"
    
    test_queries = [
        "find kinésithérapeutes in Paris",
        "trouve des ostéopathes à Lyon", 
        "dentistes dans le 16e arrondissement",
        "sage-femmes à Marseille"
    ]
    
    for query in test_queries:
        print(f"\n=== TESTING: {query} ===")
        payload = {"query": query}
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract results if available
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    choice = choices[0]
                    structured_data = choice.get("data", {}).get("structured_data", {})
                    
                    if structured_data.get("success"):
                        results = structured_data.get("data", {}).get("results", [])
                        print(f"✅ Found {len(results)} results")
                        
                        if results:
                            # Show first result
                            result = results[0]
                            print(f"Sample result:")
                            print(f"  Name: {result.get('name', 'N/A')}")
                            print(f"  Specialty: {result.get('specialty', 'N/A')}")
                            print(f"  City: {result.get('address', {}).get('organization_address', {}).get('city', 'N/A')}")
                    else:
                        print("❌ Search failed:")
                        print(structured_data.get("message", "No error message"))
                else:
                    print("❌ No choices in response")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_practitioner_role_search()
