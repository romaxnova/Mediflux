#!/usr/bin/env python3
"""
Simple test for medication query interpretation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core_orchestration.ai_query_interpreter import AIQueryInterpreter
    
    print("=== Testing AI Query Interpreter for Medications ===")
    
    interpreter = AIQueryInterpreter()
    
    # Test medication query
    query = "find Doliprane"
    print(f"Testing query: '{query}'")
    
    result = interpreter.synchronous_interpret_query(query)
    
    print(f"Intent: {result.get('intent')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Medication params: {result.get('fhir_params', {}).get('medication', {})}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
