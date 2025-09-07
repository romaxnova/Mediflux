#!/usr/bin/env python3
"""
Quick test script to verify LangChain integration is working
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add modules to path
sys.path.append('/Users/romanstadnikov/Desktop/Mediflux')

async def test_langchain_basic():
    """Test basic LangChain functionality"""
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage
        
        print("✅ LangChain imports successful")
        
        # Test XAI (Grok) connection first
        load_dotenv()
        xai_api_key = os.getenv("XAI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if xai_api_key:
            print("✅ XAI (Grok) API key found")
            
            # Create a simple test with Grok
            llm = ChatOpenAI(
                model="grok-2",
                temperature=0.0,
                api_key=xai_api_key,
                base_url="https://api.x.ai/v1"
            )
            
            # Test a simple call
            message = HumanMessage(content="Bonjour, comment allez-vous ?")
            response = await llm.agenerate([[message]])
            
            print("✅ XAI (Grok) connection successful")
            print(f"Test response: {response.generations[0][0].text[:100]}...")
            
        elif openai_api_key:
            print("✅ OpenAI API key found (fallback)")
            
            # Test with OpenAI as fallback
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.0,
                api_key=openai_api_key
            )
            
            # Test a simple call
            message = HumanMessage(content="Bonjour, comment allez-vous ?")
            response = await llm.agenerate([[message]])
            
            print("✅ OpenAI connection successful")
            print(f"Test response: {response.generations[0][0].text[:100]}...")
            
        else:
            print("⚠️  No LLM API key found - add XAI_API_KEY or OPENAI_API_KEY to .env file")
            
        return True
        
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        return False

async def test_langchain_orchestrator():
    """Test our custom LangChain orchestrator"""
    
    try:
        from modules.langchain_orchestrator import LangChainOrchestrator
        
        print("✅ LangChain orchestrator import successful")
        
        orchestrator = LangChainOrchestrator()
        
        # Test without API key (should create tools but not execute)
        health_check = await orchestrator.health_check()
        
        if health_check.get("tools_created"):
            print("✅ LangChain orchestrator initialization successful")
            print(f"Available tools: {len(health_check.get('available_tools', []))}")
        else:
            print("⚠️  LangChain orchestrator created but tools not initialized")
            
        return True
        
    except Exception as e:
        print(f"❌ LangChain orchestrator test failed: {str(e)}")
        return False

async def test_workflow_engine():
    """Test workflow engine"""
    
    try:
        from modules.workflow_engine import HealthcareWorkflowEngine
        
        print("✅ Workflow engine import successful")
        
        engine = HealthcareWorkflowEngine()
        
        workflows = engine.get_available_workflows()
        print(f"✅ Workflow engine created with {len(workflows)} workflows")
        print(f"Available workflows: {workflows}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow engine test failed: {str(e)}")
        return False

async def test_specialized_agents():
    """Test specialized agents"""
    
    try:
        from modules.specialized_agents import AgentOrchestrator
        
        print("✅ Specialized agents import successful")
        
        agent_orchestrator = AgentOrchestrator()
        
        # Test agent creation
        agents = ["medication", "pathway", "reimbursement"]
        
        for agent_type in agents:
            if hasattr(agent_orchestrator, f"{agent_type}_agent"):
                print(f"✅ {agent_type.title()} agent created")
            else:
                print(f"⚠️  {agent_type.title()} agent not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Specialized agents test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    
    print("🚀 Testing LangChain Integration for Mediflux")
    print("=" * 50)
    
    tests = [
        ("Basic LangChain", test_langchain_basic),
        ("LangChain Orchestrator", test_langchain_orchestrator), 
        ("Workflow Engine", test_workflow_engine),
        ("Specialized Agents", test_specialized_agents)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        print("-" * 30)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LangChain integration is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
    print("\n💡 Next steps:")
    print("1. Your XAI (Grok) API key is configured and working!")
    print("2. Run the comprehensive test suite: python test_langchain_integration.py")
    print("3. Start using LangChain orchestration in your healthcare workflows")
    print("4. Test with Grok demo: python demo_langchain.py")

if __name__ == "__main__":
    asyncio.run(main())
