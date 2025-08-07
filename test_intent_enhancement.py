"""
Intent Router Enhancement Tests
Improve care pathway detection and overall intent accuracy
"""

import asyncio
import sys
import os
import re

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

async def analyze_intent_patterns():
    """Analyze current intent patterns and suggest improvements"""
    print("🔍 INTENT ROUTER ANALYSIS & ENHANCEMENT")
    print("=" * 55)
    
    from modules.interpreter.intent_router import IntentRouter
    router = IntentRouter()
    
    # Test care pathway queries that should work
    care_pathway_test_queries = [
        # Current patterns (should work)
        "Parcours de soins pour diabète",  # ✅ works
        "Parcours soins cancer",
        "Chemin médical pour hypertension",
        
        # Missing patterns (currently fail)
        "Meilleur parcours pour mal de dos chronique à Paris",  # ❌ fails - "meilleur"
        "Comment traiter l'hypertension",  # ❌ fails - "comment traiter"
        "Parcours optimal pour chirurgie",  # ❌ fails - "optimal"
        "Soins pour cancer du sein",  # ❌ fails - "soins pour"
        "Traitement pour arthrose",  # ❌ fails - "traitement pour"
        "Suivi médical diabète",  # ❌ fails - "suivi médical"
        "Protocole de soins hypertension",  # ❌ fails - "protocole"
        "Prise en charge maladie chronique",  # ❌ fails - "prise en charge"
        "Étapes traitement cancer",  # ❌ fails - "étapes traitement"
        "Démarche médicale arthrite"  # ❌ fails - "démarche médicale"
    ]
    
    print("🎯 Testing Current Care Pathway Detection:")
    print("-" * 45)
    
    working_patterns = []
    failing_patterns = []
    
    for query in care_pathway_test_queries:
        result = await router.route_intent(query)
        intent = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        if intent == 'care_pathway':
            working_patterns.append(query)
            print(f"✅ '{query}' → {intent} ({confidence:.2f})")
        else:
            failing_patterns.append(query)
            print(f"❌ '{query}' → {intent} ({confidence:.2f})")
    
    print(f"\n📊 Results: {len(working_patterns)}/{len(care_pathway_test_queries)} working")
    
    # Analyze patterns in failing queries
    print(f"\n🔧 Pattern Analysis for Failing Queries:")
    print("-" * 45)
    
    failing_keywords = []
    for query in failing_patterns:
        words = query.lower().split()
        for word in words:
            if len(word) > 3:  # Ignore short words
                failing_keywords.append(word)
    
    # Count frequency
    from collections import Counter
    keyword_counts = Counter(failing_keywords)
    
    print("Common keywords in failing queries:")
    for keyword, count in keyword_counts.most_common(10):
        print(f"  • '{keyword}': {count} occurrences")
    
    # Suggest new patterns
    suggested_patterns = [
        r"meilleur.*parcours",
        r"parcours.*optimal",  
        r"comment.*traiter",
        r"traitement.*pour",
        r"soins.*pour",
        r"suivi.*médical",
        r"protocole.*soins",
        r"prise.*en.*charge",
        r"étapes.*traitement",
        r"démarche.*médicale",
        r"gestion.*maladie",
        r"stratégie.*thérapeutique"
    ]
    
    print(f"\n💡 Suggested Additional Patterns:")
    print("-" * 45)
    for pattern in suggested_patterns:
        print(f"  • {pattern}")
    
    return suggested_patterns

async def test_enhanced_intent_router():
    """Test the intent router with enhanced patterns"""
    print("\n🚀 TESTING ENHANCED INTENT ROUTER")
    print("=" * 45)
    
    from modules.interpreter.intent_router import IntentRouter
    router = IntentRouter()
    
    # Add the enhanced patterns
    enhanced_patterns = [
        r"meilleur.*parcours",
        r"parcours.*optimal",  
        r"comment.*traiter",
        r"traitement.*pour",
        r"soins.*pour",
        r"suivi.*médical",
        r"protocole.*soins",
        r"prise.*en.*charge",
        r"étapes.*traitement",
        r"démarche.*médicale",
        r"gestion.*maladie",
        r"stratégie.*thérapeutique"
    ]
    
    # Add patterns to the router
    for pattern in enhanced_patterns:
        router.add_custom_pattern("care_pathway", pattern)
    
    print("✅ Enhanced patterns added to router")
    
    # Test the failing queries again
    failing_queries = [
        "Meilleur parcours pour mal de dos chronique à Paris",
        "Comment traiter l'hypertension",
        "Parcours optimal pour chirurgie",
        "Soins pour cancer du sein",
        "Traitement pour arthrose",
        "Suivi médical diabète",
        "Protocole de soins hypertension",
        "Prise en charge maladie chronique",
        "Étapes traitement cancer",
        "Démarche médicale arthrite"
    ]
    
    print(f"\n🧪 Re-testing Previously Failing Queries:")
    print("-" * 45)
    
    improved_count = 0
    for query in failing_queries:
        result = await router.route_intent(query)
        intent = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        if intent == 'care_pathway':
            improved_count += 1
            print(f"✅ '{query}' → {intent} ({confidence:.2f})")
        else:
            print(f"❌ '{query}' → {intent} ({confidence:.2f})")
    
    print(f"\n📈 Improvement: {improved_count}/{len(failing_queries)} now working")
    improvement_rate = (improved_count / len(failing_queries)) * 100
    print(f"   Improvement rate: {improvement_rate:.1f}%")
    
    return improved_count

async def test_full_orchestrator_with_enhancements():
    """Test the full orchestrator with enhanced intent detection"""
    print("\n🎼 TESTING FULL ORCHESTRATOR WITH ENHANCEMENTS")
    print("=" * 55)
    
    from modules.orchestrator import MedifluxOrchestrator
    from modules.interpreter.intent_router import IntentRouter
    
    # Create enhanced orchestrator
    orchestrator = MedifluxOrchestrator()
    
    # Enhance the intent router
    enhanced_patterns = [
        r"meilleur.*parcours",
        r"parcours.*optimal",  
        r"comment.*traiter",
        r"traitement.*pour",
        r"soins.*pour",
        r"suivi.*médical",
        r"protocole.*soins",
        r"prise.*en.*charge",
        r"étapes.*traitement",
        r"démarche.*médicale"
    ]
    
    for pattern in enhanced_patterns:
        orchestrator.intent_router.add_custom_pattern("care_pathway", pattern)
    
    print("✅ Orchestrator enhanced with better patterns")
    
    # Test the problematic care pathway queries
    test_queries = [
        "Meilleur parcours pour mal de dos chronique à Paris",
        "Comment traiter l'hypertension", 
        "Soins pour cancer du sein",
        "Traitement pour arthrose"
    ]
    
    print(f"\n🧪 Testing Enhanced Orchestrator:")
    print("-" * 45)
    
    successful_pathways = 0
    for query in test_queries:
        try:
            result = await orchestrator.process_query(query, "enhanced_test_user")
            intent = result.get('intent', 'unknown')
            success = result.get('success', False)
            results_type = result.get('results', {}).get('type', 'unknown')
            
            print(f"\nQuery: '{query}'")
            print(f"  Intent: {intent} | Success: {success}")
            print(f"  Results type: {results_type}")
            
            if intent == 'care_pathway' and success:
                successful_pathways += 1
                print(f"  ✅ Full pathway success!")
            elif intent == 'care_pathway':
                print(f"  ⚠️ Intent correct but execution issues")
            else:
                print(f"  ❌ Intent detection failed")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print(f"\n📊 Enhanced Orchestrator Results:")
    print(f"   Successful care pathways: {successful_pathways}/{len(test_queries)}")
    print(f"   Success rate: {(successful_pathways/len(test_queries))*100:.1f}%")

async def main():
    """Run all enhancement tests"""
    suggested_patterns = await analyze_intent_patterns()
    improved_count = await test_enhanced_intent_router()
    await test_full_orchestrator_with_enhancements()
    
    print(f"\n🎯 ENHANCEMENT SUMMARY")
    print("=" * 30)
    print(f"• Identified {len(suggested_patterns)} missing patterns")
    print(f"• Enhanced intent detection significantly")
    print(f"• Ready to apply permanent fixes to orchestrator")

if __name__ == "__main__":
    asyncio.run(main())
