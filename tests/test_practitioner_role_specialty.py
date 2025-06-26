#!/usr/bin/env python3
"""
Test PractitionerRole resource - specialty-based search
This tests the second major FHIR resource after we fixed Practitioner name search
"""

import requests
import json

def test_practitioner_role_specialty():
    """Test practitioner role searches by specialty"""
    
    print("=== TESTING PRACTITIONER ROLE SPECIALTY SEARCH ===")
    
    test_queries = [
        "find kinésithérapeutes in Paris",
        "search for dentists in 75017", 
        "I need a physiotherapist",
        "show me pharmacists in Lyon",
        "find osteopaths near me",
        "search for sage-femmes in Marseille"
    ]
    
    url = "http://localhost:9000/mcp/execute"
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")
        print('='*60)
        
        try:
            response = requests.post(url, json={"query": query}, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract results
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    choice = choices[0]
                    structured_data = choice.get("data", {}).get("structured_data", {})
                    
                    if structured_data.get("success"):
                        results = structured_data.get("data", {}).get("results", [])
                        ai_interpretation = structured_data.get("data", {}).get("search_metadata", {}).get("ai_interpretation", {})
                        
                        print(f"✅ SUCCESS: Found {len(results)} results")
                        print(f"AI Confidence: {ai_interpretation.get('confidence', 'N/A')}")
                        print(f"Search Strategy: {ai_interpretation.get('search_strategy', {}).get('primary', 'N/A')}")
                        print(f"Extracted Specialty: {ai_interpretation.get('extracted_entities', {}).get('specialty', 'N/A')}")
                        
                        # Show first 3 results
                        for j, result in enumerate(results[:3], 1):
                            print(f"\nResult {j}:")
                            print(f"  Name: {result.get('name', 'N/A')}")
                            print(f"  Specialty: {result.get('specialty', 'N/A')}")
                            print(f"  Profession Code: {result.get('profession_code', 'N/A')}")
                            print(f"  Organization: {result.get('organization_name', 'N/A')}")
                            location = result.get('address', {}).get('organization_address', {}).get('city', 'N/A')
                            print(f"  Location: {location}")
                            print(f"  Active: {result.get('active', 'N/A')}")
                    else:
                        print("❌ FAILED:")
                        print(structured_data.get("message", "No error message"))
                else:
                    print("❌ FAILED: No choices in response")
                    print(json.dumps(data, indent=2))
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(response.text[:500])
        
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n{'='*60}")
    print("SPECIALTY SEARCH TESTING COMPLETE")
    print('='*60)

if __name__ == "__main__":
    test_practitioner_role_specialty()
