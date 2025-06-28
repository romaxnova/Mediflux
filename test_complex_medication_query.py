#!/usr/bin/env python3
"""
Test complex French medication queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_orchestration.ai_query_interpreter import AIQueryInterpreter
from core_orchestration.smart_orchestrator import SmartHealthcareOrchestrator

def test_complex_french_queries():
    """Test complex French medication queries"""
    
    print("=== Testing Complex French Medication Queries ===\n")
    
    # Initialize components
    interpreter = AIQueryInterpreter()
    orchestrator = SmartHealthcareOrchestrator()
    
    # Test queries
    test_queries = [
        "j'ai besoin d'un medicament pour mieux dormir sans ordonnance",
        "médicament contre les maux de tête sans prescription",
        "je cherche quelque chose pour la toux en vente libre",
        "anti-inflammatoire disponible en pharmacie sans ordonnance",
        "remède naturel pour le stress et l'anxiété",
        "médicament pour la digestion sans aller chez le médecin"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Testing query: '{query}'")
        
        # Test AI interpretation (fallback will work even with invalid API key)
        try:
            interpretation = interpreter.synchronous_interpret_query(query)
            print(f"   Intent: {interpretation.get('intent', 'unknown')}")
            print(f"   Confidence: {interpretation.get('confidence', 0)}")
            
            # Check if it detected medication intent
            if interpretation.get('intent') == 'medication':
                medication_params = interpretation.get('fhir_params', {}).get('medication', {})
                print(f"   ✅ Detected as medication query")
                print(f"   Search type: {medication_params.get('search_type', 'unknown')}")
                print(f"   Query: {medication_params.get('query', 'unknown')}")
            else:
                print(f"   ❌ Not detected as medication query")
                
            # Check extracted entities
            entities = interpretation.get('extracted_entities', {})
            if entities.get('medication_name'):
                print(f"   Medication name: {entities['medication_name']}")
            if entities.get('substance_name'):
                print(f"   Substance name: {entities['substance_name']}")
                
        except Exception as e:
            print(f"   ❌ Interpretation failed: {e}")
        
        # Test full orchestrator
        try:
            result = orchestrator.process_query(query)
            if result.get('success'):
                print(f"   ✅ Orchestrator success: {result.get('count', 0)} results")
                if result.get('results'):
                    first_result = result['results'][0]
                    print(f"   First result: {first_result.get('name', 'Unknown')}")
            else:
                print(f"   ❌ Orchestrator failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Orchestrator error: {e}")
            
        print()  # Empty line between queries
    
    print("=== Complex Query Test Complete ===")

if __name__ == "__main__":
    test_complex_french_queries()
