#!/usr/bin/env python3
"""
Complete Medication Integration Test
Tests the full medication search workflow through the smart orchestrator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_orchestration.smart_orchestrator import SmartHealthcareOrchestrator
from core_orchestration.ai_query_interpreter import AIQueryInterpreter
from core_orchestration.medication_toolkit import MedicationToolkit

def test_medication_integration():
    """Test complete medication search integration"""
    print("=== Testing Complete Medication Integration ===\n")
    
    # Test 1: Direct medication toolkit
    print("1. Testing Medication Toolkit directly...")
    toolkit = MedicationToolkit()
    
    result = toolkit.search_by_name("Doliprane", limit=3)
    print(f"   ✅ Toolkit Success: {result['success']}")
    print(f"   ✅ Count: {result.get('count', 0)}")
    if result['success'] and result['results']:
        print(f"   ✅ First medication: {result['results'][0]['name']}")
    print()
    
    # Test 2: AI Query Interpreter (fallback)
    print("2. Testing AI Query Interpreter (fallback mode)...")
    interpreter = AIQueryInterpreter()
    
    # Test medication queries
    test_queries = [
        "find Doliprane",
        "search for paracetamol",
        "médicament Aspirin",
        "what is Ibuprofen"
    ]
    
    for query in test_queries:
        print(f"   Testing: '{query}'")
        try:
            interpretation = interpreter.synchronous_interpret_query(query)
            intent = interpretation.get("intent", "unknown")
            confidence = interpretation.get("confidence", 0)
            
            print(f"   ✅ Intent: {intent}")
            print(f"   ✅ Confidence: {confidence}")
            
            if intent == "medication":
                med_params = interpretation.get("fhir_params", {}).get("medication", {})
                print(f"   ✅ Search type: {med_params.get('search_type', 'unknown')}")
                print(f"   ✅ Query: {med_params.get('query', 'unknown')}")
                print(f"   ✅ Limit: {med_params.get('limit', 'unknown')}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # Test 3: Smart Orchestrator End-to-End
    print("3. Testing Smart Orchestrator End-to-End...")
    orchestrator = SmartHealthcareOrchestrator()
    
    test_queries = [
        "find Doliprane",
        "search for medications with paracetamol",
        "what is CIS 60009011"
    ]
    
    for query in test_queries:
        print(f"   Testing: '{query}'")
        try:
            result = orchestrator.process_query(query)
            
            print(f"   ✅ Success: {result.get('success', False)}")
            print(f"   ✅ Count: {result.get('count', 0)}")
            print(f"   ✅ Search type: {result.get('search_type', 'unknown')}")
            print(f"   ✅ Message: {result.get('message', 'No message')}")
            
            if result.get('success') and result.get('results'):
                first_result = result['results'][0]
                print(f"   ✅ First result: {first_result.get('name', 'Unknown')}")
                print(f"   ✅ Resource type: {first_result.get('resource_type', 'unknown')}")
            
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=== Integration Test Complete ===")

if __name__ == "__main__":
    test_medication_integration()
