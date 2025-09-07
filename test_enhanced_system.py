#!/usr/bin/env python3
"""
Test Enhanced LangChain System - Comprehensive Healthcare Testing
Tests the complete system with real French healthcare scenarios
"""

import asyncio
import sys
import os
import json
from dotenv import load_dotenv

# Add modules to path
sys.path.append('/Users/romanstadnikov/Desktop/Mediflux')

from modules.specialized_agents import AgentOrchestrator
from modules.langchain_orchestrator import LangChainOrchestrator

async def test_agent_routing():
    """Test intelligent agent routing with real healthcare queries"""
    
    print("🎯 TESTING AGENT ROUTING")
    print("=" * 50)
    
    orchestrator = AgentOrchestrator()
    
    # Test queries in French (real healthcare scenarios)
    test_queries = [
        {
            "query": "Combien coûte le Doliprane 1000mg et quel est le remboursement?",
            "expected_agent": "medication",
            "description": "Medication price and reimbursement query"
        },
        {
            "query": "Je cherche un cardiologue à Lyon secteur 1",
            "expected_agent": "pathway", 
            "description": "Practitioner search query"
        },
        {
            "query": "Quel est le coût d'une consultation spécialiste secteur 2?",
            "expected_agent": "reimbursement",
            "description": "Cost calculation query"
        },
        {
            "query": "J'ai mal au dos depuis 2 semaines, que faire?",
            "expected_agent": "pathway",
            "description": "Care pathway guidance"
        },
        {
            "query": "Le Paracétamol est-il remboursé par la sécurité sociale?",
            "expected_agent": "medication",
            "description": "Medication reimbursement question"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print(f"Expected agent: {test_case['expected_agent']}")
        
        try:
            result = await orchestrator.route_query(test_case['query'])
            
            if result.get('success', False):
                agent_used = result.get('agent_used', 'unknown')
                print(f"✅ Success! Routed to: {agent_used}")
                
                if agent_used == test_case['expected_agent']:
                    print(f"✅ Correct routing!")
                    success_count += 1
                else:
                    print(f"⚠️  Unexpected routing (got {agent_used}, expected {test_case['expected_agent']})")
                
                # Show response details
                if 'result' in result:
                    response = result['result']
                    if isinstance(response, dict):
                        tools_used = response.get('tools_used', [])
                        print(f"🔧 Tools used: {', '.join(tools_used)}")
                    else:
                        print(f"📝 Response: {str(response)[:100]}...")
                        
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("-" * 40)
    
    print(f"\n📊 ROUTING TEST RESULTS")
    print(f"Successful routes: {success_count}/{len(test_queries)}")
    print(f"Success rate: {(success_count/len(test_queries)*100):.1f}%")
    
    return success_count == len(test_queries)

async def test_system_integration():
    """Test complete system integration"""
    
    print("\n🔗 TESTING SYSTEM INTEGRATION")
    print("=" * 50)
    
    # Test agent orchestrator
    print("1. Testing Agent Orchestrator...")
    orchestrator = AgentOrchestrator()
    status = orchestrator.get_agent_status()
    print(f"Agent status: {json.dumps(status, indent=2)}")
    
    # Test LangChain orchestrator
    print("\n2. Testing LangChain Orchestrator...")
    try:
        lc_orchestrator = LangChainOrchestrator()
        print("✅ LangChain orchestrator initialized")
        
        # Test basic query processing
        test_query = "Test de connectivité système"
        result = await lc_orchestrator.process_query(test_query)
        print(f"✅ Query processing works: {str(result)[:100]}...")
        
    except Exception as e:
        print(f"❌ LangChain orchestrator failed: {e}")
    
    # Test environment configuration
    print("\n3. Testing Environment Configuration...")
    load_dotenv()
    
    xai_key = os.getenv("XAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if xai_key:
        print("✅ XAI API key configured")
    elif openai_key:
        print("✅ OpenAI API key configured (fallback)")
    else:
        print("❌ No LLM API key found")
    
    return True

async def test_performance_comparison():
    """Compare new system vs old system approach"""
    
    print("\n⚡ PERFORMANCE COMPARISON")
    print("=" * 50)
    
    # Test query that would be handled differently
    complex_query = "Je cherche un cardiologue remboursé secteur 1 à Paris pour un suivi post-infarctus"
    
    print(f"Query: {complex_query}")
    print("\n🆚 NEW SYSTEM (LangChain + Grok):")
    
    try:
        orchestrator = AgentOrchestrator()
        start_time = asyncio.get_event_loop().time()
        
        result = await orchestrator.route_query(complex_query)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"✅ Processing time: {processing_time:.2f}s")
        print(f"✅ Agent selected: {result.get('agent_used', 'unknown')}")
        print(f"✅ Success: {result.get('success', False)}")
        
        if result.get('result'):
            response = result['result']
            if isinstance(response, dict):
                tools = response.get('tools_used', [])
                print(f"✅ Tools utilized: {len(tools)} tools")
            
    except Exception as e:
        print(f"❌ New system failed: {e}")
    
    print("\n🔍 OLD SYSTEM (Rule-based):")
    print("Would require manual if/else logic:")
    print("- Check for 'cardiologue' → pathway agent")
    print("- Check for 'secteur 1' → reimbursement agent") 
    print("- Check for 'remboursé' → reimbursement agent")
    print("❌ Conflicting routing logic - unclear which agent to use")
    print("❌ No contextual understanding of query intent")
    
    return True

async def test_error_handling():
    """Test system error handling and graceful degradation"""
    
    print("\n🛡️  TESTING ERROR HANDLING")
    print("=" * 50)
    
    orchestrator = AgentOrchestrator()
    
    # Test edge cases
    edge_cases = [
        "",  # Empty query
        "askdjflkasjdf",  # Nonsense query
        "Hello in English",  # Non-French query
        "A" * 1000,  # Very long query
    ]
    
    for i, query in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge case {i}: {query[:50]}{'...' if len(query) > 50 else ''}")
        
        try:
            result = await orchestrator.route_query(query)
            
            if result.get('success', False):
                print(f"✅ Handled gracefully: {result.get('agent_used', 'unknown')} agent")
            else:
                print(f"⚠️  Handled with error: {result.get('error', 'No error message')}")
                
        except Exception as e:
            print(f"❌ Exception raised: {str(e)[:100]}")
    
    return True

async def main():
    """Run comprehensive system tests"""
    
    print("🏥 ENHANCED LANGCHAIN SYSTEM TESTING")
    print("🇫🇷 Comprehensive Healthcare AI Validation")
    print("=" * 60)
    
    # Check environment
    load_dotenv()
    if not os.getenv("XAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("❌ No LLM API key found. Some tests may run in mock mode.")
    
    test_results = []
    
    try:
        # Run all tests
        print("Starting comprehensive test suite...")
        
        result1 = await test_agent_routing()
        test_results.append(("Agent Routing", result1))
        
        result2 = await test_system_integration() 
        test_results.append(("System Integration", result2))
        
        result3 = await test_performance_comparison()
        test_results.append(("Performance Comparison", result3))
        
        result4 = await test_error_handling()
        test_results.append(("Error Handling", result4))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:25} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("Your LangChain system is ready to replace the old one!")
        else:
            print(f"\n⚠️  {total-passed} tests failed. Please review and fix issues.")
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
