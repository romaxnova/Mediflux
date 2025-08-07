"""
Frontend-Backend Integration Test
Test the orchestrator through the actual API endpoints
"""

import asyncio
import requests
import json

async def test_frontend_backend_integration():
    """Test the frontend-backend connection with realistic queries"""
    print("🌐 FRONTEND-BACKEND INTEGRATION TEST")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test queries that represent real user interactions
    test_queries = [
        {
            "message": "Combien coûte le Doliprane?",
            "expected_intent": "simulate_cost",
            "description": "Reimbursement query"
        },
        {
            "message": "Meilleur parcours pour mal de dos à Paris",
            "expected_intent": "care_pathway", 
            "description": "Care pathway query"
        },
        {
            "message": "trouve moi un somnifière sans ordonnance",
            "expected_intent": "medication_info",
            "description": "Medication info query"
        },
        {
            "message": "Je cherche un cardiologue à Lyon",
            "expected_intent": "practitioner_search",
            "description": "Practitioner search"
        },
        {
            "message": "Analyser ma carte tiers payant",
            "expected_intent": "analyze_document",
            "description": "Document analysis"
        }
    ]
    
    print("Testing API connectivity...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print(f"❌ API server error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return
    
    print(f"\nTesting {len(test_queries)} realistic user queries...")
    print("-" * 50)
    
    successful_tests = 0
    
    for i, test in enumerate(test_queries, 1):
        try:
            print(f"\n{i}. {test['description']}")
            print(f"   Query: '{test['message']}'")
            
            # Send request to chat endpoint
            payload = {
                "message": test['message'],
                "user_id": f"test_user_{i}"
            }
            
            response = requests.post(
                f"{base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                intent = data.get('intent', 'unknown')
                response_text = data.get('response', 'No response')
                
                print(f"   ✅ Status: 200 OK")
                print(f"   🎯 Intent: {intent}")
                print(f"   💬 Response: {response_text[:100]}...")
                
                if intent == test['expected_intent']:
                    print(f"   ✅ Intent matches expected: {intent}")
                    successful_tests += 1
                else:
                    print(f"   ⚠️ Intent mismatch: expected {test['expected_intent']}, got {intent}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
    
    print(f"\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    print(f"Successful tests: {successful_tests}/{len(test_queries)}")
    print(f"Success rate: {(successful_tests/len(test_queries))*100:.1f}%")
    
    if successful_tests == len(test_queries):
        print("🎉 ALL TESTS PASSED - Frontend-Backend integration working!")
    elif successful_tests >= len(test_queries) * 0.8:
        print("✅ MOSTLY WORKING - Minor improvements needed")
    else:
        print("⚠️ ISSUES DETECTED - Check orchestrator configuration")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Open frontend: http://localhost:5173")
    print(f"   2. Test these exact queries in the UI")
    print(f"   3. Verify responses match the API test results")

if __name__ == "__main__":
    asyncio.run(test_frontend_backend_integration())
