"""
Test script to verify practitioner search intent routing fix
"""

import asyncio
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

async def test_practitioner_response():
    """Test the complete practitioner search response"""
    
    print("🏥 Testing Practitioner Search Fix")
    print("=" * 50)
    
    try:
        from orchestrator import MedifluxOrchestrator
        
        orchestrator = MedifluxOrchestrator()
        
        # Test queries that should now work correctly
        test_queries = [
            "Je cherche un médecin généraliste à Paris",
            "Où trouver un cardiologue à Lyon?",
            "Besoin d'un dentiste près de chez moi"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            print("-" * 40)
            
            response = await orchestrator.process_query(query, {})
            
            print(f"✅ Success: {response['success']}")
            print(f"📋 Intent: {response.get('debug_info', {}).get('intent', 'unknown')}")
            print(f"🎯 Confidence: {response.get('debug_info', {}).get('confidence', 'unknown')}")
            
            # Check response content
            resp_content = response.get('response', '')
            if isinstance(resp_content, str):
                if len(resp_content) > 200:
                    print(f"📝 Response preview: {resp_content[:200]}...")
                else:
                    print(f"📝 Response: {resp_content}")
                    
                # Check if it contains real data indicators
                real_data_indicators = ['médecin', 'docteur', 'praticien', 'cabinet', 'consultation']
                placeholder_indicators = ['placeholder', 'TODO', 'mock', 'fake']
                
                has_real_data = any(indicator in resp_content.lower() for indicator in real_data_indicators)
                has_placeholder = any(indicator in resp_content.lower() for indicator in placeholder_indicators)
                
                print(f"🔍 Contains healthcare terms: {has_real_data}")
                print(f"⚠️  Contains placeholders: {has_placeholder}")
            
            print()
        
        print("🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_practitioner_response())
