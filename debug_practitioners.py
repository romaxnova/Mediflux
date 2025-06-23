#!/usr/bin/env python3
"""
Debug Practitioner Search Issues
===============================
"""

import requests
import json
import sys
import os

# Add the project root to the path
sys.path.append('/Users/romanstadnikov/Library/OpenManus/workspace/mediflux')

def test_direct_fhir_api():
    """Test direct FHIR API calls"""
    print("🔍 Testing Direct FHIR API Calls")
    print("=" * 40)
    
    # Test Organization API (known to work)
    print("\n1. Testing Organization API:")
    org_url = "https://annuaire.sante.fr/fhir/v1/Organization?_count=5&address-city=Lyon"
    try:
        response = requests.get(org_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total: {data.get('total', 'N/A')}")
            print(f"   Entries: {len(data.get('entry', []))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test PractitionerRole API
    print("\n2. Testing PractitionerRole API:")
    prac_url = "https://annuaire.sante.fr/fhir/v1/PractitionerRole?_count=5&address-city=Lyon"
    try:
        response = requests.get(prac_url, timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total: {data.get('total', 'N/A')}")
            print(f"   Entries: {len(data.get('entry', []))}")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")

def test_ai_interpretation():
    """Test AI query interpretation for practitioner queries"""
    print("\n🤖 Testing AI Query Interpretation")
    print("=" * 40)
    
    from core_orchestration.ai_query_interpreter import AIQueryInterpreter
    
    interpreter = AIQueryInterpreter()
    
    test_queries = [
        "find a cardiologist in Lyon",
        "je cherche un dermatologue à Nice",
        "cardiologue à Paris"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = interpreter.interpret_query(query)
            print(f"   Intent: {result.get('intent')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Entities: {result.get('extracted_entities', {})}")
            print(f"   FHIR Params: {result.get('fhir_params', {})}")
        except Exception as e:
            print(f"   Error: {e}")

def test_practitioner_mcp():
    """Test practitioner MCP directly"""
    print("\n🏥 Testing Practitioner MCP Directly")
    print("=" * 40)
    
    try:
        from core_orchestration.practitioner_role_mcp import PractitionerRoleMCP
        
        mcp = PractitionerRoleMCP()
        
        # Test with simple query
        query = "cardiologist in Lyon"
        print(f"\nTesting query: {query}")
        
        result = mcp.process_query(query)
        print(f"   Success: {result.get('success', False)}")
        print(f"   Message: {result.get('message', 'No message')}")
        print(f"   Results: {len(result.get('data', {}).get('results', []))}")
        
        if result.get('data', {}).get('results'):
            first_result = result['data']['results'][0]
            print(f"   First result: {first_result.get('name', 'No name')}")
        
    except Exception as e:
        print(f"   Error importing/testing PractitionerRoleMCP: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🩺 Mediflux Practitioner Debug Tool")
    print("=" * 50)
    
    test_direct_fhir_api()
    test_ai_interpretation() 
    test_practitioner_mcp()

if __name__ == "__main__":
    main()
