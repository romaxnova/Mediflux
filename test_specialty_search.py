#!/usr/bin/env python3

import requests
import json

def test_specialty_search():
    """Test specialty-based search"""
    
    print("=== TESTING SPECIALTY SEARCH ===")
    
    # Test our smart MCP server
    url = "http://localhost:9000/mcp/execute"
    payload = {"query": "find kinésithérapeutes in Paris"}
    
    print(f"Sending request to: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("=== RESPONSE STRUCTURE ===")
            
            # Extract results if available
            choices = data.get("choices", [])
            if choices and len(choices) > 0:
                choice = choices[0]
                structured_data = choice.get("data", {}).get("structured_data", {})
                
                if structured_data.get("success"):
                    results = structured_data.get("data", {}).get("results", [])
                    print(f"\n=== FOUND {len(results)} RESULTS ===")
                    
                    for i, result in enumerate(results[:3]):  # Show first 3
                        print(f"\nResult {i+1}:")
                        print(f"  ID: {result.get('id', 'N/A')}")
                        print(f"  Name: {result.get('name', 'N/A')}")
                        print(f"  Specialty: {result.get('specialty', 'N/A')}")
                        print(f"  Profession Code: {result.get('profession_code', 'N/A')}")
                        print(f"  Active: {result.get('active', 'N/A')}")
                        print(f"  Organization: {result.get('address', {}).get('organization_name', 'N/A')}")
                        print(f"  Location: {result.get('address', {}).get('organization_address', {}).get('city', 'N/A')}")
                        
                    # Check AI interpretation
                    ai_interp = structured_data.get("data", {}).get("search_metadata", {}).get("ai_interpretation", {})
                    print(f"\n=== AI INTERPRETATION ===")
                    print(f"Intent: {ai_interp.get('intent', 'N/A')}")
                    print(f"Confidence: {ai_interp.get('confidence', 'N/A')}")
                    print(f"Extracted specialty: {ai_interp.get('extracted_entities', {}).get('specialty', 'N/A')}")
                    print(f"Extracted location: {ai_interp.get('extracted_entities', {}).get('location', {})}")
                    print(f"Search strategy: {ai_interp.get('search_strategy', {})}")
                    print(f"Reasoning: {ai_interp.get('reasoning', 'N/A')}")
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
    test_specialty_search()
