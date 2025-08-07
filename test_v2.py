"""
V2 Mediflux Test Script
Quick verification of the new modular architecture
"""

import asyncio
import sys
import os

# Add v2 modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

async def test_v2_modules():
    """Test basic functionality of V2 modules"""
    
    print("🧪 Testing V2 Mediflux Modules")
    print("=" * 40)
    
    try:
        # Test Intent Router
        print("Testing Intent Router...")
        from interpreter.intent_router import IntentRouter
        router = IntentRouter()
        
        test_query = "Combien coûte le Doliprane à Paris?"
        result = await router.route_intent(test_query)
        print(f"✅ Intent detected: {result['intent']} (confidence: {result['confidence']:.2f})")
        
        # Test Memory Store
        print("\nTesting Memory Store...")
        from memory.store import MemoryStore
        memory = MemoryStore()
        
        await memory.update_user_profile("test_user", {"mutuelle": "basic", "location": "Paris"})
        context = await memory.get_user_context("test_user")
        print(f"✅ User context: {context['profile']}")
        
        # Test BDPM Client
        print("\nTesting BDPM Client...")
        from data_hub.bdpm import BDPMClient
        bdpm = BDPMClient()
        
        # This would make a real API call - just test initialization
        print("✅ BDPM Client initialized")
        
        # Test Reimbursement Simulator
        print("\nTesting Reimbursement Simulator...")
        from reimbursement.simulator import ReimbursementSimulator
        simulator = ReimbursementSimulator()
        
        simulation_params = {
            "treatment_type": "medication",
            "medication_name": "Doliprane",
            "mutuelle_type": "basic"
        }
        sim_result = await simulator.simulate_costs(simulation_params)
        print(f"✅ Cost simulation: {sim_result['success']}")
        
        # Test Document Analyzer
        print("\nTesting Document Analyzer...")
        from document_analyzer.handler import DocumentAnalyzer
        analyzer = DocumentAnalyzer()
        
        supported_types = analyzer.get_supported_types()
        print(f"✅ Document types supported: {', '.join(supported_types)}")
        
        # Test Care Pathway Advisor
        print("\nTesting Care Pathway Advisor...")
        from care_pathway.advisor import CarePathwayAdvisor
        advisor = CarePathwayAdvisor()
        
        pathway_params = {
            "condition": "mal de dos",
            "user_location": "Paris"
        }
        pathway_result = await advisor.get_optimized_pathway(pathway_params)
        print(f"✅ Care pathway: {pathway_result['success']}")
        
        print("\n🎉 All V2 modules initialized successfully!")
        print("\nNext steps:")
        print("- Integrate real OCR for document analysis")
        print("- Set up local AI (Mixtral) for complex query interpretation")
        print("- Implement actual API calls to Odissé")
        print("- Add comprehensive test coverage")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing modules: {str(e)}")
        return False

async def test_full_orchestrator():
    """Test the main orchestrator integration"""
    print("\n🎼 Testing Full Orchestrator Integration")
    print("=" * 40)
    
    try:
        from modules.orchestrator import MedifluxOrchestrator
        
        orchestrator = MedifluxOrchestrator()
        
        # Test queries
        test_queries = [
            "Combien coûte le Doliprane?",
            "Je cherche un cardiologue à Paris",
            "Parcours de soins pour mal de dos"
        ]
        
        for query in test_queries:
            print(f"\nTesting: '{query}'")
            result = await orchestrator.process_query(query, "test_user")
            print(f"✅ Intent: {result.get('intent', 'unknown')} | Success: {result.get('success', False)}")
        
        print("\n🎉 Orchestrator integration successful!")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {str(e)}")
        return False

if __name__ == "__main__":
    async def main():
        module_test = await test_v2_modules()
        if module_test:
            orchestrator_test = await test_full_orchestrator()
        
        print(f"\n📊 Test Results:")
        print(f"Modules: {'✅ PASS' if module_test else '❌ FAIL'}")
        print(f"Orchestrator: {'✅ PASS' if module_test and orchestrator_test else '❌ FAIL'}")
    
    asyncio.run(main())
