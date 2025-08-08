"""
Comprehensive test of the orchestrator response system
Tests unique responses for different queries and identifies issues
"""

import asyncio
import sys
import os

# Add modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, current_dir)
sys.path.insert(0, modules_dir)

from modules.orchestrator import MedifluxOrchestrator

class OrchrestratorResponseTester:
    def __init__(self):
        self.orchestrator = MedifluxOrchestrator()
        self.test_queries = [
            "Je cherche un cardiologue à Lyon",
            "Combien coûte le Doliprane?",
            "Comment optimiser mon parcours pour le diabète?",
            "Analyser ma carte tiers payant",
            "Trouve-moi un générique pour l'ibuprofène",
            "Simulation remboursement consultation spécialiste",
            "Bonjour, je suis nouveau",
            "Aide-moi",
            "What is the weather today?",
            "Comment ça marche le système de santé français?"
        ]
    
    async def test_unique_responses(self):
        """Test that different queries get different responses"""
        print("🧪 TESTING UNIQUE RESPONSES")
        print("=" * 60)
        
        responses = {}
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n{i}. Query: {query}")
            print("-" * 40)
            
            try:
                result = await self.orchestrator.process_query(query, f"test_user_{i}")
                
                intent = result.get("intent", "unknown")
                ai_response = result.get("response", "NO AI RESPONSE")
                success = result.get("success", False)
                
                print(f"Intent: {intent}")
                print(f"Success: {success}")
                print(f"AI Response: {ai_response[:100]}...")
                
                # Check for uniqueness
                if ai_response in responses:
                    print(f"❌ DUPLICATE RESPONSE! Same as query: {responses[ai_response]}")
                else:
                    responses[ai_response] = query
                    print(f"✅ Unique response")
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
        
        print(f"\n📊 SUMMARY:")
        print(f"Total queries: {len(self.test_queries)}")
        print(f"Unique responses: {len(responses)}")
        print(f"Duplicate rate: {(len(self.test_queries) - len(responses)) / len(self.test_queries) * 100:.1f}%")
    
    async def test_ai_response_generator_directly(self):
        """Test the AI response generator in isolation"""
        print("\n\n🤖 TESTING AI RESPONSE GENERATOR DIRECTLY")
        print("=" * 60)
        
        # Test the AI response generator directly
        ai_gen = self.orchestrator.ai_response_generator
        
        test_cases = [
            {
                "query": "Je cherche un cardiologue à Lyon",
                "intent": "practitioner_search",
                "results": {
                    "success": True,
                    "search_results": {
                        "success": True,
                        "specialty": "cardiologue",
                        "location": "Lyon",
                        "total_found": 50
                    }
                },
                "user_context": {"profile": {}}
            },
            {
                "query": "Combien coûte le Doliprane?",
                "intent": "medication_info",
                "results": {
                    "success": True,
                    "medication_data": {
                        "success": True,
                        "results": [
                            {
                                "denomination": "DOLIPRANE 1000 mg",
                                "public_price": "2.50",
                                "commercialization_status": "Commercialisé"
                            }
                        ]
                    }
                },
                "user_context": {"profile": {"mutuelle_type": "MGEN"}}
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test['query']}")
            print("-" * 40)
            
            try:
                response = await ai_gen.generate_response(
                    user_query=test["query"],
                    intent=test["intent"], 
                    orchestrator_results=test["results"],
                    user_context=test["user_context"]
                )
                
                print(f"Response: {response}")
                print(f"Length: {len(response)} characters")
                print(f"Contains query terms: {'cardiologue' in response.lower() if 'cardiologue' in test['query'] else 'doliprane' in response.lower()}")
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
    
    async def test_api_endpoint_responses(self):
        """Test what the API endpoint actually returns"""
        print("\n\n🌐 TESTING API ENDPOINT RESPONSES")
        print("=" * 60)
        
        import requests
        
        api_queries = [
            "Je cherche un cardiologue à Lyon",
            "Combien coûte le Doliprane?",  
            "Bonjour",
            "Comment simuler un remboursement?"
        ]
        
        for i, query in enumerate(api_queries, 1):
            print(f"\n{i}. API Test: {query}")
            print("-" * 40)
            
            try:
                response = requests.post(
                    "http://localhost:8000/chat",
                    json={"message": query, "user_id": f"api_test_{i}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Status: {response.status_code}")
                    print(f"Intent: {data.get('intent', 'none')}")
                    print(f"Response: {data.get('response', 'NO RESPONSE')[:150]}...")
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")

async def main():
    tester = OrchrestratorResponseTester()
    
    print("🚀 COMPREHENSIVE ORCHESTRATOR TESTING")
    print("=" * 80)
    
    await tester.test_unique_responses()
    await tester.test_ai_response_generator_directly()
    await tester.test_api_endpoint_responses()
    
    print("\n\n🎯 DIAGNOSIS:")
    print("If you see:")
    print("- Same responses for different queries → AI generator not working properly")
    print("- 'NO AI RESPONSE' → Integration issue between orchestrator and AI generator")
    print("- API errors → Server/connection issues")
    print("- Fallback responses only → No LLM API key configured (expected)")

if __name__ == "__main__":
    asyncio.run(main())
