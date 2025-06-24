#!/usr/bin/env python3

import requests
import json
import time

def test_practitioner_name(name):
    """Test a specific practitioner name search"""
    
    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"{'='*60}")
    
    url = "http://localhost:9000/mcp/execute"
    payload = {"query": f"find {name}"}
    
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
                    print(f"✅ SUCCESS: Found {len(results)} results")
                    
                    # Show AI interpretation
                    ai_interp = structured_data.get("data", {}).get("search_metadata", {}).get("ai_interpretation", {})
                    confidence = ai_interp.get("confidence", 0)
                    reasoning = ai_interp.get("reasoning", "No reasoning provided")
                    extracted_name = ai_interp.get("extracted_entities", {}).get("practitioner_name", "None")
                    
                    print(f"AI Confidence: {confidence}")
                    print(f"Extracted Name: {extracted_name}")
                    print(f"Reasoning: {reasoning}")
                    
                    # Show results summary
                    for i, result in enumerate(results[:3]):  # Show first 3 results
                        print(f"\nResult {i+1}:")
                        print(f"  Name: {result.get('name', 'N/A')}")
                        print(f"  Specialty: {result.get('specialty', 'N/A')}")
                        print(f"  Organization: {result.get('address', {}).get('organization_name', 'N/A')}")
                        print(f"  Location: {result.get('address', {}).get('organization_address', {}).get('city', 'N/A')}")
                        print(f"  Active: {result.get('active', 'N/A')}")
                        print(f"  RPPS: {result.get('rpps_id', 'N/A')}")
                        
                    if len(results) > 3:
                        print(f"  ... and {len(results) - 3} more results")
                        
                else:
                    print(f"❌ FAILED: {structured_data.get('message', 'No error message')}")
                    print("Raw response:")
                    print(json.dumps(data, indent=2))
            else:
                print("❌ FAILED: No choices in response")
                print("Raw response:")
                print(json.dumps(data, indent=2))
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            print(response.text[:500])
    
    except Exception as e:
        print(f"❌ REQUEST FAILED: {e}")

def main():
    """Test multiple practitioner names"""
    
    # Names extracted from FHIR API
    test_names = [
        "Sophie Prach",           # Already working
        "Francoise Brun",        # New test
        "Isabelle Car-Darny",    # New test (hyphenated)
        "Lea Petit",             # New test (simple name)
        "Corinne Mollet",        # New test
        "Celine Mendez",         # New test
        "Jeremie Treutenaere",   # New test (male name)
        "Justine Ayello",        # New test (mixed case)
        "Marie Le Bihan",        # New test (compound last name)
        "Alice De Saint Vincent Chenard"  # New test (complex name)
    ]
    
    print("COMPREHENSIVE PRACTITIONER NAME SEARCH TEST")
    print("=" * 80)
    print(f"Testing {len(test_names)} different practitioner names")
    print("=" * 80)
    
    success_count = 0
    
    for i, name in enumerate(test_names):
        test_practitioner_name(name)
        
        # Add small delay between requests to be respectful
        if i < len(test_names) - 1:
            time.sleep(1)
    
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Tested {len(test_names)} names")
    # Note: Success counting would require parsing each result, keeping simple for now

if __name__ == "__main__":
    main()
