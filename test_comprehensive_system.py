"""
Test the comprehensive healthcare search system with diverse queries
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'core_orchestration'))

from core_orchestration.comprehensive_orchestrator import ComprehensiveHealthcareOrchestrator

def test_comprehensive_system():
    """Test the comprehensive system with various query types"""
    
    orchestrator = ComprehensiveHealthcareOrchestrator()
    
    # Test queries covering all 5 FHIR resources
    test_queries = [
        # Organization searches
        "je cherche un hôpital à Paris",
        "find pharmacies in Lyon",
        "cliniques à Marseille",
        
        # Practitioner by specialty searches
        "je cherche un cardiologue",
        "find a dentist in Nice",
        "kinésithérapeute à Toulouse",
        
        # Practitioner by name searches  
        "Dr. Martin",
        "cherche Jean Dupont médecin",
        "find Dr. Sophie Prach",
        
        # Healthcare service searches
        "service d'urgences",
        "radiologie à Lyon", 
        "laboratoire médical",
        
        # Device searches
        "IRM à Paris",
        "scanner médical",
        "équipement radiologique"
    ]
    
    print("🏥 TESTING COMPREHENSIVE HEALTHCARE SEARCH SYSTEM")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[TEST {i}] Query: {query}")
        print("-" * 40)
        
        try:
            result = orchestrator.process_query(query)
            
            if result.get("success"):
                print(f"✅ SUCCESS: {result.get('count', 0)} results")
                print(f"   Search type: {result.get('search_type', 'unknown')}")
                print(f"   Message: {result.get('message', 'No message')}")
                
                # Show AI interpretation
                ai_interp = result.get("ai_interpretation", {})
                print(f"   AI Intent: {ai_interp.get('intent', 'unknown')}")
                print(f"   AI Confidence: {ai_interp.get('confidence', 0):.2f}")
                
                # Show first few results
                results = result.get("results", [])
                for j, res in enumerate(results[:2]):  # Show first 2 results
                    if res.get("resource_type") == "organization":
                        print(f"   Result {j+1}: {res.get('name', 'Unknown')} ({res.get('type', 'Unknown type')})")
                        if res.get("address", {}).get("city"):
                            print(f"              📍 {res['address']['city']}")
                    
                    elif res.get("resource_type") == "practitioner":
                        print(f"   Result {j+1}: {res.get('name', 'Unknown')} - {res.get('specialty', 'Unknown specialty')}")
                        if res.get("address", {}).get("organization"):
                            print(f"              🏢 {res['address']['organization']}")
                    
                    elif res.get("resource_type") == "healthcare_service":
                        print(f"   Result {j+1}: {res.get('name', 'Unknown service')} - {res.get('category', 'Unknown category')}")
                    
                    elif res.get("resource_type") == "device":
                        print(f"   Result {j+1}: {res.get('name', 'Unknown device')} ({res.get('type', 'Unknown type')})")
                
                if len(results) > 2:
                    print(f"   ... and {len(results) - 2} more results")
                
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"💥 EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE TESTING COMPLETED")

if __name__ == "__main__":
    test_comprehensive_system()
