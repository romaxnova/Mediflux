#!/usr/bin/env python3
"""
End-to-end test to verify the complete intelligence pipeline
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.orchestrator import MedifluxOrchestrator

async def test_end_to_end_intelligence():
    """Test the complete pipeline from query to AI reasoning"""
    
    print("🧠 Testing End-to-End Intelligence Pipeline")
    print("=" * 60)
    
    orchestrator = MedifluxOrchestrator()
    
    # The query that previously failed to trigger AI reasoning
    test_query = "Je me sens fatigué depuis 3 semaines"
    
    print(f"Query: '{test_query}'")
    print("\n🔍 Processing...")
    
    try:
        result = await orchestrator.process_query(test_query)
        
        print(f"\n📋 Result Type: {result.get('type', 'unknown')}")
        print(f"📝 Message: {result.get('message', 'No message')}")
        
        # Check if it's using AI reasoning vs hardcoded response
        if result.get('type') == 'general_response':
            print("❌ FAILED: Still using hardcoded general response")
        elif result.get('type') == 'care_pathway':
            print("✅ SUCCESS: Using intelligent care pathway")
            
            # Check if it extracted the condition
            extracted_condition = result.get('extracted_condition')
            if extracted_condition:
                print(f"🎯 Condition Extracted: {extracted_condition['condition']} (confidence: {extracted_condition['confidence']:.2f})")
            else:
                print("🤖 AI Reasoning: No exact condition match - using AI pathway generation")
            
            # Check pathway recommendations
            pathway = result.get('pathway_recommendations')
            if pathway:
                print(f"📊 Pathway Steps: {len(pathway.get('steps', []))} steps")
                print(f"🔬 Reasoning Method: {pathway.get('reasoning_method', 'unknown')}")
        else:
            print(f"⚠️  Unexpected response type: {result.get('type')}")
            
        print(f"\n📄 Full Response:\n{result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_end_to_end_intelligence())
