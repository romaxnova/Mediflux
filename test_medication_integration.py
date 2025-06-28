#!/usr/bin/env python3
"""
Test the complete medication integration with AI interpreter and smart orchestrator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_orchestration.smart_orchestrator import SmartHealthcareOrchestrator

def test_medication_integration():
    """Test complete medication integration"""
    print("=== Testing Complete Medication Integration ===\n")
    
    orchestrator = SmartHealthcareOrchestrator()
    
    test_queries = [
        "find Doliprane",
        "what is Aspirin",
        "médicament paracétamol",
        "prix Doliprane",
        "medications with paracetamol",
        "substance paracétamol"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Testing query: '{query}'")
        try:
            result = orchestrator.process_query(query)
            
            print(f"   ✅ Success: {result.get('success', False)}")
            print(f"   ✅ Search Type: {result.get('search_type', 'unknown')}")
            print(f"   ✅ Results Count: {result.get('count', 0)}")
            
            if result.get('results') and len(result['results']) > 0:
                first_result = result['results'][0]
                if first_result.get('resource_type') == 'medication':
                    print(f"   ✅ First medication: {first_result.get('name', 'Unknown')}")
                    print(f"   ✅ CIS Code: {first_result.get('id', 'Unknown')}")
                    print(f"   ✅ Form: {first_result.get('pharmaceutical_form', 'Unknown')}")
            
            # Show AI interpretation
            ai_interp = result.get('ai_interpretation', {})
            print(f"   🤖 AI Intent: {ai_interp.get('intent', 'unknown')}")
            print(f"   🤖 AI Confidence: {ai_interp.get('confidence', 0)}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()

if __name__ == "__main__":
    test_medication_integration()
