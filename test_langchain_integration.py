#!/usr/bin/env python3
"""
Test script for LangChain integration in Mediflux
Tests both the main orchestrator and specialized agents
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Python environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'med/lib/python3.12/site-packages'))

async def test_langchain_orchestrator():
    """Test the main LangChain orchestrator"""
    
    print("🤖 Testing LangChain Healthcare Orchestrator")
    print("=" * 60)
    
    try:
        from modules.langchain_orchestrator import LangChainOrchestrator
        
        orchestrator = LangChainOrchestrator()
        
        # Test 1: Simple medication query
        print("\n📋 Test 1: Medication Information")
        print("-" * 30)
        query1 = "Quel est le prix du Doliprane et combien ça coûte avec la Sécurité Sociale ?"
        
        result1 = await orchestrator.process_query(query1)
        print(f"Query: {query1}")
        print(f"Success: {result1.get('success')}")
        print(f"Response: {result1.get('response', 'No response')}")
        if result1.get('tokens_used'):
            print(f"Tokens used: {result1['tokens_used']['total_tokens']}")
        print()
        
        # Test 2: Care pathway query
        print("\n🗺️ Test 2: Care Pathway")
        print("-" * 30)
        query2 = "J'ai mal au dos depuis plusieurs semaines, quel parcours de soins me conseillez-vous ?"
        
        result2 = await orchestrator.process_query(query2)
        print(f"Query: {query2}")
        print(f"Success: {result2.get('success')}")
        print(f"Response: {result2.get('response', 'No response')}")
        print()
        
        # Test 3: Complex orchestration query
        print("\n🔀 Test 3: Complex Orchestration")
        print("-" * 30)
        query3 = "Je cherche un cardiologue à Paris et je veux savoir combien ça va me coûter"
        
        result3 = await orchestrator.process_query(query3)
        print(f"Query: {query3}")
        print(f"Success: {result3.get('success')}")
        print(f"Response: {result3.get('response', 'No response')}")
        print()
        
        # Test 4: Health check
        print("\n🏥 Test 4: System Health Check")
        print("-" * 30)
        health = await orchestrator.health_check()
        print("Health Status:")
        for component, status in health.items():
            if isinstance(status, dict):
                print(f"  {component}:")
                for sub_comp, sub_status in status.items():
                    print(f"    {sub_comp}: {sub_status}")
            else:
                print(f"  {component}: {status}")
        
        # Test 5: Available tools
        print("\n🔧 Available Tools:")
        tools = orchestrator.get_available_tools()
        for tool in tools:
            print(f"  - {tool}")
        
        print("\n✅ LangChain Orchestrator tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure LangChain dependencies are installed:")
        print("pip install langchain langchain-openai langchain-community")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_specialized_agents():
    """Test specialized healthcare agents"""
    
    print("\n🎯 Testing Specialized Healthcare Agents")
    print("=" * 60)
    
    try:
        from modules.specialized_agents import AgentOrchestrator, MedicationAgent, PathwayAgent, ReimbursementAgent
        
        # Test individual agents
        print("\n💊 Testing Medication Agent")
        print("-" * 30)
        med_agent = MedicationAgent()
        med_result = await med_agent.process_medication_query("Informations sur l'amoxicilline")
        print(f"Medication Agent Result: {med_result.get('response', 'No response')}")
        
        print("\n🗺️ Testing Pathway Agent")
        print("-" * 30)
        path_agent = PathwayAgent()
        path_result = await path_agent.process_pathway_query("Parcours pour hypertension")
        print(f"Pathway Agent Result: {path_result.get('response', 'No response')}")
        
        print("\n💰 Testing Reimbursement Agent")
        print("-" * 30)
        reimb_agent = ReimbursementAgent()
        reimb_result = await reimb_agent.process_cost_query("Coût consultation cardiologue")
        print(f"Reimbursement Agent Result: {reimb_result.get('response', 'No response')}")
        
        # Test orchestrator routing
        print("\n🔀 Testing Agent Orchestrator")
        print("-" * 30)
        orchestrator = AgentOrchestrator()
        
        test_queries = [
            "Prix du Doliprane",
            "Parcours pour diabète",
            "Remboursement consultation spécialiste"
        ]
        
        for query in test_queries:
            result = await orchestrator.process_query(query)
            routed_to = result.get('routing_decision', 'unknown')
            print(f"Query: '{query}' → Routed to: {routed_to}")
            print(f"Response: {result.get('response', 'No response')[:100]}...")
            print()
        
        print("✅ Specialized agents tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error during specialized agents testing: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_integration_comparison():
    """Compare old vs new orchestration approaches"""
    
    print("\n⚖️ Integration Comparison: Old vs LangChain")
    print("=" * 60)
    
    test_query = "J'ai mal à la tête, que me conseillez-vous ?"
    
    # Test old orchestrator
    print("\n🔧 Old Rule-Based Orchestrator:")
    print("-" * 40)
    try:
        from modules.orchestrator import MedifluxOrchestrator
        old_orchestrator = MedifluxOrchestrator()
        old_result = await old_orchestrator.process_query(test_query)
        print(f"Old Result: {old_result.get('response', 'No response')}")
        print(f"Intent detected: {old_result.get('intent', 'unknown')}")
    except Exception as e:
        print(f"Old orchestrator error: {str(e)}")
    
    # Test new LangChain orchestrator
    print("\n🤖 New LangChain Orchestrator:")
    print("-" * 40)
    try:
        from modules.langchain_orchestrator import LangChainOrchestrator
        new_orchestrator = LangChainOrchestrator()
        new_result = await new_orchestrator.process_query(test_query)
        print(f"New Result: {new_result.get('response', 'No response')}")
        print(f"Agent type: {new_result.get('agent_type', 'unknown')}")
        if new_result.get('reasoning_steps'):
            print(f"Reasoning steps: {len(new_result['reasoning_steps'])}")
    except Exception as e:
        print(f"New orchestrator error: {str(e)}")


async def main():
    """Run all tests"""
    
    print("🚀 Mediflux LangChain Integration Test Suite")
    print("=" * 80)
    
    # Check environment setup
    print("\n🔍 Environment Check:")
    print("-" * 20)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OpenAI API Key found (ending in ...{api_key[-4:]})")
    else:
        print("❌ OpenAI API Key not found - set OPENAI_API_KEY environment variable")
        return
    
    try:
        import langchain
        print(f"✅ LangChain version: {langchain.__version__}")
    except ImportError:
        print("❌ LangChain not installed")
        return
    
    # Run tests
    await test_langchain_orchestrator()
    await test_specialized_agents()
    await test_integration_comparison()
    
    print("\n🎉 All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
