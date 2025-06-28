#!/usr/bin/env python3
"""
Test MCP Server Medication Integration
Tests the complete flow through the MCP server endpoint
"""

import requests
import json

def test_mcp_medication_search():
    """Test medication search through MCP server endpoint"""
    print("=== Testing MCP Server Medication Integration ===\n")
    
    # MCP server endpoint
    url = "http://localhost:9000/mcp/execute"
    
    # Test cases
    test_queries = [
        "find Doliprane",
        "search for medications with paracetamol", 
        "what is Aspirin",
        "médicament Ibuprofen",
        "prix Doliprane 1000mg"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Testing: '{query}'")
        
        try:
            # Make request to MCP server
            response = requests.post(url, json={
                "prompt": query
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract results
                choices = data.get("choices", [])
                if choices:
                    choice = choices[0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    
                    # Extract structured data
                    result_data = choice.get("data", {})
                    results = result_data.get("results", [])
                    search_type = result_data.get("search_type", "unknown")
                    
                    print(f"   ✅ Success: {len(results)} results")
                    print(f"   ✅ Search type: {search_type}")
                    print(f"   ✅ Message: {content[:100]}...")
                    
                    if results and search_type == "medication":
                        first_result = results[0]
                        medication_name = first_result.get("name", "Unknown")
                        print(f"   ✅ First medication: {medication_name}")
                        print(f"   ✅ Resource type: {first_result.get('resource_type', 'unknown')}")
                    
                else:
                    print(f"   ❌ No choices in response")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   ❌ Response: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: MCP server not running on localhost:9000")
            print(f"   💡 Start server with: python mcp_server_smart.py")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print()  # Empty line between tests
    
    print("=== MCP Server Test Complete ===")

if __name__ == "__main__":
    test_mcp_medication_search()
