#!/usr/bin/env python3
"""
V2 Mediflux Demo
Quick demonstration of the new modular architecture
"""

import sys
import os
import json

# Add the modules directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, modules_dir)

def demo_intent_router():
    """Demonstrate intent routing capabilities"""
    print("🎯 Intent Router Demo")
    print("-" * 30)
    
    try:
        from interpreter.intent_router import IntentRouter
        router = IntentRouter()
        
        test_queries = [
            "Combien coûte le Doliprane?",
            "Je cherche un cardiologue à Paris",
            "Analyser ma carte tiers payant",
            "Parcours de soins pour diabète",
            "Trouver un médecin généraliste"
        ]
        
        print("Testing query interpretation...")
        for query in test_queries:
            # Note: Using sync version since we're in a simple demo
            print(f"\nQuery: '{query}'")
            
            # For demo, we'll show pattern matching without async
            patterns = router.intent_patterns
            matched_intents = []
            
            for intent, pattern_list in patterns.items():
                for pattern in pattern_list:
                    import re
                    if re.search(pattern, query.lower(), re.IGNORECASE):
                        matched_intents.append(intent)
                        break
            
            if matched_intents:
                print(f"  → Detected intent: {matched_intents[0]}")
            else:
                print(f"  → Would use AI fallback")
        
        print(f"\n✅ Intent Router working! Supports {len(router.intent_patterns)} intent types")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def demo_memory_store():
    """Demonstrate memory store capabilities"""
    print("\n💾 Memory Store Demo")
    print("-" * 30)
    
    try:
        from memory.store import MemoryStore
        
        # Initialize memory store
        memory = MemoryStore()
        print("✅ Memory store initialized")
        print(f"   Database location: {memory.db_path}")
        
        # Show supported operations
        print("\nSupported operations:")
        print("  - User profile management")
        print("  - Session history tracking")
        print("  - Automatic data compression")
        print("  - GDPR compliance features")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def demo_data_clients():
    """Demonstrate data hub clients"""
    print("\n🌐 Data Hub Clients Demo")
    print("-" * 30)
    
    clients_status = {}
    
    # BDPM Client
    try:
        from data_hub.bdpm import BDPMClient
        bdpm = BDPMClient()
        print("✅ BDPM Client - French medication database")
        print("   Features: Name/substance/CIS search, reimbursement info, generics")
        clients_status['bdpm'] = True
    except Exception as e:
        print(f"❌ BDPM Client error: {e}")
        clients_status['bdpm'] = False
    
    # Annuaire Client  
    try:
        from data_hub.annuaire import AnnuaireClient
        annuaire = AnnuaireClient()
        print("✅ Annuaire Santé Client - French healthcare directory")
        print("   Features: Practitioner search, tariff analysis, aggregated data")
        clients_status['annuaire'] = True
    except Exception as e:
        print(f"❌ Annuaire Client error: {e}")
        clients_status['annuaire'] = False
    
    # Odissé Client
    try:
        from data_hub.odisse import OdisseClient
        odisse = OdisseClient()
        print("✅ Odissé Client - Regional healthcare metrics")
        print("   Features: Professional density, wait times, access indicators")
        clients_status['odisse'] = True
    except Exception as e:
        print(f"❌ Odissé Client error: {e}")
        clients_status['odisse'] = False
    
    # Open Medic Client
    try:
        from data_hub.open_medic import OpenMedicClient
        open_medic = OpenMedicClient()
        print("✅ Open Medic Client - Medication reimbursement trends")
        print("   Features: CSV processing, historical trends, regional statistics")
        clients_status['open_medic'] = True
    except Exception as e:
        print(f"❌ Open Medic Client error: {e}")
        clients_status['open_medic'] = False
    
    working_clients = sum(clients_status.values())
    total_clients = len(clients_status)
    print(f"\n📊 Data clients status: {working_clients}/{total_clients} working")
    
    return working_clients > 0

def demo_analysis_modules():
    """Demonstrate analysis modules"""
    print("\n🔬 Analysis Modules Demo")
    print("-" * 30)
    
    modules_status = {}
    
    # Reimbursement Simulator
    try:
        from reimbursement.simulator import ReimbursementSimulator
        simulator = ReimbursementSimulator()
        print("✅ Reimbursement Simulator")
        print("   Features: Cost breakdown, mutuelle comparison, savings tips")
        
        # Show example calculation
        print("   Example: GP consultation = €25 → Patient remainder ≈ €7.50")
        modules_status['reimbursement'] = True
    except Exception as e:
        print(f"❌ Reimbursement Simulator error: {e}")
        modules_status['reimbursement'] = False
    
    # Document Analyzer
    try:
        from document_analyzer.handler import DocumentAnalyzer
        analyzer = DocumentAnalyzer()
        supported_types = analyzer.get_supported_types()
        print("✅ Document Analyzer")
        print(f"   Supported types: {', '.join(supported_types)}")
        modules_status['document'] = True
    except Exception as e:
        print(f"❌ Document Analyzer error: {e}")
        modules_status['document'] = False
    
    # Care Pathway Advisor
    try:
        from care_pathway.advisor import CarePathwayAdvisor
        advisor = CarePathwayAdvisor()
        print("✅ Care Pathway Advisor")
        print("   Features: Optimized care sequences, cost estimates, timelines")
        modules_status['pathway'] = True
    except Exception as e:
        print(f"❌ Care Pathway Advisor error: {e}")
        modules_status['pathway'] = False
    
    working_modules = sum(modules_status.values())
    total_modules = len(modules_status)
    print(f"\n📊 Analysis modules status: {working_modules}/{total_modules} working")
    
    return working_modules > 0

def show_architecture_overview():
    """Show the V2 architecture overview"""
    print("\n🏗️  V2 Architecture Overview")
    print("=" * 50)
    
    architecture = {
        "Orchestrator": "Main coordinator with intent-based routing",
        "Intent Router": "Rule-based query interpretation + AI fallback",
        "Memory Store": "SQLite-based user profiles & session history",
        "Data Hub": {
            "BDPM": "French medication database client",
            "Annuaire Santé": "Healthcare directory with aggregation",
            "Odissé": "Regional healthcare metrics",
            "Open Medic": "Medication reimbursement trends"
        },
        "Analysis Modules": {
            "Reimbursement Simulator": "Cost breakdown calculator",
            "Document Analyzer": "OCR + rule-based extraction",
            "Care Pathway Advisor": "Intelligent care sequencing"
        }
    }
    
    def print_dict(d, indent=0):
        for key, value in d.items():
            if isinstance(value, dict):
                print("  " * indent + f"📁 {key}:")
                print_dict(value, indent + 1)
            else:
                print("  " * indent + f"📄 {key}: {value}")
    
    print_dict(architecture)

def main():
    """Run the V2 demo"""
    print("🚀 Mediflux V2 Architecture Demo")
    print("=" * 50)
    
    # Show architecture
    show_architecture_overview()
    
    # Test components
    results = []
    results.append(demo_intent_router())
    results.append(demo_memory_store())
    results.append(demo_data_clients())
    results.append(demo_analysis_modules())
    
    # Summary
    print("\n📋 Demo Summary")
    print("=" * 30)
    working_components = sum(results)
    total_components = len(results)
    
    component_names = ["Intent Router", "Memory Store", "Data Clients", "Analysis Modules"]
    
    for i, (name, status) in enumerate(zip(component_names, results)):
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
    
    print(f"\n🎯 Overall Status: {working_components}/{total_components} component groups working")
    
    if working_components == total_components:
        print("🎉 All V2 components are ready!")
        print("\nNext steps:")
        print("- Test async functionality with real API calls")
        print("- Implement OCR integration")
        print("- Add local AI (Mixtral) support")
        print("- Create web interface")
    else:
        print("⚠️  Some components need attention - check import paths and dependencies")
    
    print(f"\n📁 V2 Project location: {current_dir}")

if __name__ == "__main__":
    main()
