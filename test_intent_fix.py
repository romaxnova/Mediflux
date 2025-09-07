#!/usr/bin/env python3
"""
Test script to verify that intent routing now properly handles symptom queries
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.interpreter.intent_router import IntentRouter

async def test_intent_routing():
    """Test that symptom queries now trigger care_pathway intent"""
    router = IntentRouter()
    
    test_queries = [
        "Je me sens fatigué depuis 3 semaines",
        "J'ai mal à la tête depuis plusieurs jours", 
        "Je souffre de troubles du sommeil",
        "J'ai des douleurs dans le dos",
        "Feeling tired for weeks",
        "I have pain in my stomach",
        "parcours de soins pour diabète"  # This should still work
    ]
    
    print("🔍 Testing Intent Routing Fix")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            result = await router.route_intent(query)
            intent = result["intent"]
            confidence = result.get("confidence", 0)
            method = result.get("method", "unknown")
            
            if intent == "care_pathway":
                print(f"✅ Intent: {intent} (confidence: {confidence:.2f}, method: {method})")
            elif intent == "general_query":
                print(f"❌ Intent: {intent} (still falling back to general_query)")
            else:
                print(f"⚠️  Intent: {intent} (unexpected intent)")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Expected: All symptom queries should trigger 'care_pathway' intent")

if __name__ == "__main__":
    asyncio.run(test_intent_routing())
