"""
Focused Tests for Orchestrator Issues
Fix the specific problems identified in comprehensive testing
"""

import asyncio
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

async def test_specific_issues():
    """Test and fix specific issues found in comprehensive testing"""
    print("🔍 FOCUSED TESTING FOR SPECIFIC ISSUES")
    print("=" * 50)
    
    from modules.orchestrator import MedifluxOrchestrator
    orchestrator = MedifluxOrchestrator()
    
    # Issue 1: Care pathway intent not being detected correctly
    print("\n🛤️ Testing Care Pathway Intent Detection")
    print("-" * 40)
    
    care_pathway_queries = [
        "Meilleur parcours pour mal de dos chronique à Paris",
        "Parcours de soins pour diabète",
        "Comment traiter l'hypertension",
        "Parcours optimal pour chirurgie",
        "Soins pour cancer du sein"
    ]
    
    for query in care_pathway_queries:
        try:
            result = await orchestrator.process_query(query, "pathway_test_user")
            intent = result.get('intent', 'unknown')
            success = result.get('success', False)
            
            print(f"Query: '{query}'")
            print(f"  Intent: {intent} | Success: {success}")
            
            if intent == 'care_pathway':
                print(f"  ✅ Correct intent detected")
            else:
                print(f"  ❌ Expected 'care_pathway', got '{intent}'")
                
            # Show results structure
            results = result.get('results', {})
            print(f"  Results type: {results.get('type', 'unknown')}")
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Issue 2: Fix BDPM client attribute name
    print("\n🔗 Testing Data Client Attributes")
    print("-" * 40)
    
    # Check correct attribute names
    print("Checking orchestrator attributes:")
    
    attrs_to_check = [
        ('bdpm_client', 'BDPM Client'),
        ('annuaire_client', 'Annuaire Client'), 
        ('odisse_client', 'Odisse Client'),
        ('memory_store', 'Memory Store'),
        ('intent_router', 'Intent Router')
    ]
    
    for attr, name in attrs_to_check:
        if hasattr(orchestrator, attr):
            obj = getattr(orchestrator, attr)
            print(f"  ✅ {name}: {type(obj).__name__}")
            
            # Check methods
            if hasattr(obj, 'search_medication'):
                print(f"    - has search_medication method")
            if hasattr(obj, 'search_practitioners'):
                print(f"    - has search_practitioners method")
            if hasattr(obj, 'get_regional_data'):
                print(f"    - has get_regional_data method")
        else:
            print(f"  ❌ {name}: Missing attribute '{attr}'")
    
    # Issue 3: Test error handling improvements
    print("\n⚠️ Testing Enhanced Error Handling")
    print("-" * 40)
    
    error_test_cases = [
        ("", "Empty query"),
        ("   ", "Whitespace only query"),
        ("askdjfkadsjfkadsfjkl", "Nonsense query"),
        ("!@#$%^&*()", "Special characters only")
    ]
    
    for query, description in error_test_cases:
        try:
            result = await orchestrator.process_query(query, "error_test_user")
            success = result.get('success', False)
            intent = result.get('intent', 'unknown')
            error = result.get('error', 'No error message')
            
            print(f"{description}: '{query}'")
            print(f"  Success: {success} | Intent: {intent}")
            if not success:
                print(f"  ✅ Properly handled error: {error}")
            else:
                print(f"  ⚠️ Did not fail as expected")
            print()
            
        except Exception as e:
            print(f"{description}: ✅ Exception handled gracefully: {str(e)}")
    
    # Issue 4: Test document handling with various inputs
    print("\n📄 Testing Document Upload Edge Cases")
    print("-" * 40)
    
    document_test_cases = [
        ("", "carte_tiers_payant", "Empty path"),
        ("nonexistent.pdf", "carte_tiers_payant", "Nonexistent file"),
        ("test.jpg", "", "Empty document type"),
        ("test.jpg", "invalid_type", "Invalid document type"),
    ]
    
    for file_path, doc_type, description in document_test_cases:
        try:
            result = await orchestrator.upload_document(file_path, doc_type, "doc_test_user")
            success = result.get('success', False)
            error = result.get('error', 'No error')
            
            print(f"{description}: path='{file_path}', type='{doc_type}'")
            print(f"  Success: {success}")
            if not success:
                print(f"  ✅ Error handled: {error}")
            else:
                print(f"  ⚠️ Unexpectedly succeeded")
            print()
            
        except Exception as e:
            print(f"{description}: ✅ Exception handled: {str(e)}")
    
    # Issue 5: Deep dive into user context and memory
    print("\n🧠 Testing Memory Store Deep Dive")
    print("-" * 40)
    
    try:
        # Test detailed memory operations
        test_user = "memory_deep_test"
        
        # Create complex user profile
        complex_profile = {
            "mutuelle": "MAIF Intégrale",
            "location": "Lyon 69002",
            "pathology": ["diabète type 2", "hypertension"],
            "preferences": {
                "cost_preference": "low",
                "wait_time_preference": "flexible",
                "sector_preference": "public"
            },
            "medical_history": {
                "allergies": ["pénicilline"],
                "medications": ["metformine", "lisinopril"]
            }
        }
        
        # Update profile
        result = await orchestrator.update_user_profile(test_user, complex_profile)
        print(f"Complex profile update: {result.get('success', False)}")
        
        # Retrieve and verify
        context = await orchestrator.memory_store.get_user_context(test_user)
        print(f"Context retrieval: {'✅' if context else '❌'}")
        
        if context and 'profile' in context:
            profile = context['profile']
            print(f"  Mutuelle: {profile.get('mutuelle', 'Missing')}")
            print(f"  Pathologies: {len(profile.get('pathology', []))}")
            print(f"  Preferences: {'✅' if 'preferences' in profile else '❌'}")
        
        # Test query with context
        print("\nTesting context-aware query:")
        result = await orchestrator.process_query(
            "Combien coûte mon traitement diabète?", 
            test_user
        )
        
        print(f"  Query success: {result.get('success', False)}")
        print(f"  Used context: {result.get('user_context', {}).get('profile', {}).get('mutuelle', 'None')}")
        
    except Exception as e:
        print(f"Memory deep dive error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_specific_issues())
