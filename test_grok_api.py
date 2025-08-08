"""
Separate Grok API test to validate LLM integration
Tests both XAI (Grok) and OpenAI APIs independently
"""

import asyncio
import aiohttp
import os
from typing import Optional
from dotenv import load_dotenv

class GrokAPITester:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        self.xai_api_key = os.getenv("XAI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # XAI (Grok) API endpoint
        self.xai_base_url = "https://api.x.ai/v1"
        # OpenAI API endpoint  
        self.openai_base_url = "https://api.openai.com/v1"
    
    def check_api_keys(self):
        """Check which API keys are available"""
        print("🔑 API KEY STATUS:")
        print("-" * 30)
        print(f"XAI_API_KEY: {'✅ Set' if self.xai_api_key else '❌ Not found'}")
        print(f"OPENAI_API_KEY: {'✅ Set' if self.openai_api_key else '❌ Not found'}")
        
        if not self.xai_api_key and not self.openai_api_key:
            print("\n⚠️  NO API KEYS CONFIGURED!")
            print("To test LLM integration, set either:")
            print("export XAI_API_KEY='your-grok-api-key'")
            print("or")
            print("export OPENAI_API_KEY='your-openai-api-key'")
            return False
        return True
    
    async def test_grok_api(self, query: str = "What is the capital of France?") -> Optional[str]:
        """Test XAI (Grok) API directly"""
        if not self.xai_api_key:
            print("❌ XAI_API_KEY not set, skipping Grok test")
            return None
            
        print(f"\n🤖 TESTING GROK API")
        print(f"Query: {query}")
        print("-" * 40)
        
        headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-2",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant specialized in French healthcare. Respond in French."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.xai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"Raw response: {data}")  # Debug: see full response
                        choice = data["choices"][0]["message"]
                        # grok-3-mini-fast should have direct content (not reasoning)
                        grok_response = choice.get("content", "")
                        print(f"✅ Grok Response: {grok_response}")
                        return grok_response
                    elif response.status == 429:
                        error_text = await response.text()
                        print(f"⚠️  Rate Limited (429): {error_text}")
                        print("💡 Tip: Wait a few seconds between requests")
                        return None
                    else:
                        error_text = await response.text()
                        print(f"❌ Error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None
    
    async def test_openai_api(self, query: str = "What is the capital of France?") -> Optional[str]:
        """Test OpenAI API directly"""
        if not self.openai_api_key:
            print("❌ OPENAI_API_KEY not set, skipping OpenAI test")
            return None
            
        print(f"\n🧠 TESTING OPENAI API")
        print(f"Query: {query}")
        print("-" * 40)
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant specialized in French healthcare. Respond in French."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        openai_response = data["choices"][0]["message"]["content"]
                        print(f"✅ OpenAI Response: {openai_response}")
                        return openai_response
                    else:
                        error_text = await response.text()
                        print(f"❌ Error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None
    
    async def test_healthcare_queries(self):
        """Test with healthcare-specific queries"""
        healthcare_queries = [
            "Je cherche un cardiologue à Lyon, pouvez-vous m'aider?"
        ]  # Reduced to 1 query to avoid rate limits
        
        print("\n🏥 TESTING HEALTHCARE QUERIES")
        print("=" * 50)
        
        for i, query in enumerate(healthcare_queries, 1):
            print(f"\n--- Query {i} ---")
            
            # Test with Grok first (avoid OpenAI due to quota issues)
            grok_result = await self.test_grok_api(query)
            
            # Add delay to respect rate limits
            print("⏳ Waiting 3 seconds to respect rate limits...")
            await asyncio.sleep(3)
            
            print(f"\nComparison for: {query}")
            print(f"Grok: {'✅ Success' if grok_result else '❌ Failed'}")
            
            return grok_result  # Return early to avoid hitting more rate limits
    
    async def test_api_integration_flow(self):
        """Test the exact same flow as AIResponseGenerator"""
        print("\n🔄 TESTING INTEGRATION FLOW")
        print("=" * 50)
        
        # Simulate the exact context our orchestrator sends
        test_context = {
            "user_query": "Je cherche un cardiologue à Lyon",
            "intent": "practitioner_search",
            "orchestrator_results": {
                "success": True,
                "search_results": {
                    "specialty": "cardiologue",
                    "location": "Lyon", 
                    "total_found": 50,
                    "practitioners": [
                        {"name": "Dr. Martin Dupont", "address": "123 Rue de la République, Lyon"}
                    ]
                }
            },
            "user_context": {
                "profile": {"mutuelle_type": "MGEN", "chronic_conditions": ["hypertension"]}
            }
        }
        
        # Create a prompt like AIResponseGenerator would
        system_prompt = """You are a French healthcare assistant. Generate a helpful, personalized response based on the user query and available data. Respond in French."""
        
        user_prompt = f"""
Query: {test_context['user_query']}
Intent: {test_context['intent']}
Results: {test_context['orchestrator_results']}
User Profile: {test_context['user_context']['profile']}

Please provide a helpful response that incorporates the search results and user context.
"""
        
        print("System Prompt:", system_prompt[:100] + "...")
        print("User Prompt:", user_prompt[:200] + "...")
        
        grok_result = await self.test_grok_api(user_prompt)
        openai_result = await self.test_openai_api(user_prompt)
        
        return grok_result or openai_result

async def main():
    tester = GrokAPITester()
    
    print("🧪 GROK/LLM API TESTING")
    print("=" * 60)
    
    # Check API key status
    has_keys = tester.check_api_keys()
    
    if has_keys:
        # Test basic functionality
        await tester.test_grok_api()
        await tester.test_openai_api()
        
        # Test healthcare queries
        await tester.test_healthcare_queries()
        
        # Test integration flow
        result = await tester.test_api_integration_flow()
        
        print(f"\n🎯 FINAL RESULT:")
        if result:
            print("✅ LLM API integration working!")
            print("The orchestrator should be able to generate unique responses.")
        else:
            print("❌ LLM API integration failed")
            print("Check API keys and network connectivity.")
    else:
        print("\n🔧 TO FIX THE ORCHESTRATOR:")
        print("1. Get a Grok API key from https://console.x.ai")
        print("2. Set it: export XAI_API_KEY='your-api-key'")
        print("3. Or use OpenAI: export OPENAI_API_KEY='your-openai-key'")
        print("4. Restart the orchestrator")
        
        # Test fallback behavior
        print("\n🎭 TESTING FALLBACK BEHAVIOR (without API keys):")
        print("This is what your orchestrator is currently doing...")

if __name__ == "__main__":
    asyncio.run(main())
