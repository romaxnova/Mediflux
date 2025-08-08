"""
Simple single Grok API test to avoid rate limits
"""

import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

async def test_single_grok_request():
    """Test one single Grok request"""
    load_dotenv()
    api_key = os.getenv("XAI_API_KEY")
    
    if not api_key:
        print("❌ No XAI_API_KEY found")
        return
    
    print(f"🔑 API Key: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "grok-3-mini",
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant médical français. Réponds en français."
            },
            {
                "role": "user", 
                "content": "Je cherche un cardiologue à Lyon"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print("📤 Sending request...")
    print(f"Model: {payload['model']}")
    print(f"Query: {payload['messages'][1]['content']}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                
                print(f"📥 Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"📝 Raw Response:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]["message"]
                        content = choice.get("content", "") or choice.get("reasoning_content", "")
                        print(f"\n✅ SUCCESS!")
                        print(f"🤖 Grok says: {content}")
                        return content
                    else:
                        print("❌ No choices in response")
                        return None
                        
                elif response.status == 429:
                    error_text = await response.text()
                    print(f"⚠️  Rate Limited (429)")
                    print(f"Response: {error_text}")
                    return None
                else:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}")
                    print(f"Response: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_single_grok_request())
    
    if result:
        print(f"\n🎯 CONCLUSION: Grok API is working!")
        print(f"✅ The orchestrator should be able to generate AI responses")
    else:
        print(f"\n❌ CONCLUSION: Grok API failed")
        print(f"🔧 Need to fix API issues before orchestrator can work")
