#!/usr/bin/env python3

"""
Test the corrected practitioner name search using the proper /Practitioner endpoint
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_orchestration.smart_orchestrator import SmartHealthcareOrchestrator

def test_name_searches():
    """Test various name search patterns"""
    orchestrator = SmartHealthcareOrchestrator()
    
    # Test cases for name searches
    test_queries = [
        "Find Dr Sophie Prach",
        "Search for Jean Dupont doctor", 
        "Find practitioner Martin",
        "Look for Dr. Pierre Bernard",
        "Search for Marie Dubois médecin"
    ]
    
    print("🧪 Testing Corrected Name Search (using /Practitioner endpoint)")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        print("-" * 50)
        
        try:
            result = orchestrator.process_query(query)
            
            if result.get("success"):
                count = result.get("count", 0)
                print(f"✅ SUCCESS: Found {count} practitioners")
                
                # Show first few results
                for j, practitioner in enumerate(result.get("results", [])[:3], 1):
                    print(f"   {j}. {practitioner.get('name', 'Unknown')} - {practitioner.get('specialty', 'N/A')}")
                    if practitioner.get("rpps_id"):
                        print(f"      RPPS: {practitioner['rpps_id']}")
                    print(f"      ID: {practitioner.get('id', 'N/A')}")
                
                if count > 3:
                    print(f"   ... and {count - 3} more")
                    
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"💥 EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_name_searches()
