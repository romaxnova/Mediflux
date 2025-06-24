#!/usr/bin/env python3

import requests
import json

def test_failed_names():
    """Test the names that failed in our previous test"""
    
    # Names that failed due to AI parsing issues
    failed_names = [
        "find Isabelle Car-Darny",
        "find Jeremie Treutenaere", 
        "find Alice De Saint Vincent Chenard",
        "find Thomas Bihel"  # Let's test this too
    ]
    
    print("TESTING FAILED NAMES WITH IMPROVED AI PARSING")
    print("=" * 60)
    
    for name_query in failed_names:
        print(f"\n{'='*60}")
        print(f"TESTING: {name_query}")
        print('='*60)
        
        try:
            response = requests.post(
                "http://localhost:9000/mcp/execute",
                json={"query": name_query},
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if successful
                success = data.get("choices", [{}])[0].get("data", {}).get("structured_data", {}).get("success", False)
                results = data.get("choices", [{}])[0].get("data", {}).get("structured_data", {}).get("data", {}).get("results", [])
                
                print(f"✅ SUCCESS: Found {len(results)} results" if success else "❌ FAILED: No results")
                
                # Extract AI interpretation details
                search_metadata = data.get("choices", [{}])[0].get("data", {}).get("structured_data", {}).get("data", {}).get("search_metadata", {})
                ai_interpretation = search_metadata.get("ai_interpretation", {})
                
                print(f"AI Confidence: {ai_interpretation.get('confidence', 'N/A')}")
                print(f"Extracted Name: {ai_interpretation.get('extracted_entities', {}).get('practitioner_name', 'N/A')}")
                print(f"Reasoning: {ai_interpretation.get('reasoning', 'N/A')}")
                
                # Show results
                for i, result in enumerate(results[:3], 1):  # Show max 3 results
                    print(f"\nResult {i}:")
                    print(f"  Name: {result.get('name', 'N/A')}")
                    print(f"  Specialty: {result.get('specialty', 'N/A')}")
                    print(f"  Organization: {result.get('address', {}).get('organization_name', 'N/A')}")
                    print(f"  Location: {result.get('address', {}).get('organization_address', {}).get('city', 'N/A')}")
                    print(f"  Active: {result.get('active', 'N/A')}")
                    print(f"  RPPS: {result.get('rpps_id', 'N/A')}")
                        
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(response.text[:200])
                
        except Exception as e:
            print(f"❌ REQUEST FAILED: {e}")

if __name__ == "__main__":
    test_failed_names()
