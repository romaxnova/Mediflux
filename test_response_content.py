"""
Detailed test of orchestrator responses to verify real data usage
"""

import asyncio
import sys
import os

# Add modules to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

async def test_orchestrator_responses():
    """Test actual content of orchestrator responses"""
    
    print("🔍 Testing Orchestrator Response Content")
    print("=" * 50)
    
    try:
        from orchestrator import MedifluxOrchestrator
        from ai.response_generator import AIResponseGenerator
        
        # Test medication query (should work with real BDPM data)
        print("1. Testing medication query...")
        orchestrator = MedifluxOrchestrator()
        
        med_response = await orchestrator.process_query("Combien coûte le paracétamol?", {})
        print(f"✅ Medication query success: {med_response['success']}")
        med_content = str(med_response.get('response', ''))
        print(f"📝 Response length: {len(med_content)} chars")
        print(f"🔍 Contains price data: {'€' in med_content or 'euro' in med_content}")
        print(f"🏥 Contains medication names: {'paracétamol' in med_content.lower() or 'doliprane' in med_content.lower()}")
        print(f"💊 Response preview: {med_content[:200]}...")
        
        print("\n" + "-"*50)
        
        # Test practitioner query (should work with real FHIR data)
        print("2. Testing practitioner query...")
        
        prac_response = await orchestrator.process_query("Je cherche un médecin généraliste à Paris", {})
        print(f"✅ Practitioner query success: {prac_response['success']}")
        prac_content = str(prac_response.get('response', ''))
        print(f"📝 Response length: {len(prac_content)} chars")
        print(f"🏥 Contains practitioner terms: {any(term in prac_content.lower() for term in ['médecin', 'docteur', 'praticien', 'cabinet'])}")
        print(f"📍 Contains location info: {'paris' in prac_content.lower()}")
        print(f"⚠️  Contains placeholders: {any(placeholder in prac_content.lower() for placeholder in ['placeholder', 'todo', 'mock'])}")
        print(f"🔍 Response preview: {prac_content[:300]}...")
        
        print("\n" + "-"*50)
        
        # Test AI Response Generator directly
        print("3. Testing AI Response Generator...")
        
        generator = AIResponseGenerator()
        
        # Create fake practitioner data to test AI response
        fake_practitioners = [
            {
                "display_name": "Dr. Jean Dupont",
                "formatted_address": "123 Rue de la Santé, 75014 Paris",
                "specialty": "Médecine générale",
                "phone": "01.23.45.67.89"
            }
        ]
        
        ai_response = await generator.generate_response(
            user_query="Je cherche un médecin généraliste à Paris",
            intent="practitioner_search",
            data={"practitioners": fake_practitioners},
            context={}
        )
        
        print(f"🤖 AI Response type: {type(ai_response)}")
        print(f"📝 AI Response length: {len(str(ai_response))} chars")
        print(f"🔍 AI Response preview: {str(ai_response)[:300]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator_responses())
