#!/usr/bin/env python3
"""
Prompt 2 Test: Database Architecture Validation
Test SQLite implementation with JSON support and caching
"""

import asyncio
import sys
import os

# Add modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, modules_dir)

async def test_database_manager():
    """Test enhanced database manager"""
    print("💾 Testing Database Manager...")
    
    try:
        from database.manager import DatabaseManager
        
        # Use test database
        db = DatabaseManager("test_prompt2.db")
        await db.initialize()
        
        # Test user profile operations
        test_user = "test_user_db"
        test_profile = {"mutuelle": "premium", "location": "Lyon", "pathology": "hypertension"}
        
        await db.update_user_profile(test_user, test_profile)
        retrieved_profile = await db.get_user_profile(test_user)
        
        if retrieved_profile == test_profile:
            print("  ✅ User profile storage/retrieval")
        else:
            print("  ❌ User profile issues")
            return False
        
        # Test session history
        await db.add_session_entry(test_user, "Test query", "test_intent", {"success": True})
        sessions = await db.get_user_sessions(test_user, 1)
        
        if len(sessions) == 1 and sessions[0]["query"] == "Test query":
            print("  ✅ Session history")
        else:
            print("  ❌ Session history issues")
            return False
        
        # Test API caching
        cache_endpoint = "test_api"
        cache_params = {"param1": "value1"}
        cache_response = {"data": "test_data"}
        
        await db.cache_response(cache_endpoint, cache_params, cache_response, 1)
        cached = await db.get_cached_response(cache_endpoint, cache_params)
        
        if cached == cache_response:
            print("  ✅ API response caching")
        else:
            print("  ❌ API caching issues")
            return False
        
        # Test database stats
        stats = await db.get_database_stats()
        if stats["users_count"] >= 1 and stats["sessions_count"] >= 1:
            print("  ✅ Database statistics")
        else:
            print("  ❌ Database statistics issues")
            return False
        
        # Cleanup test database
        os.remove("test_prompt2.db")
        return True
        
    except Exception as e:
        print(f"  ❌ Database manager failed: {e}")
        return False

async def test_enhanced_memory_store():
    """Test enhanced memory store integration"""
    print("\n🧠 Testing Enhanced Memory Store...")
    
    try:
        from memory.store import MemoryStore
        
        # Use test database
        memory = MemoryStore("test_memory.db")
        
        test_user = "test_user_memory"
        
        # Test profile management
        await memory.update_user_profile(test_user, {"mutuelle": "basic", "location": "Paris"})
        context = await memory.get_user_context(test_user)
        
        if context["profile"]["mutuelle"] == "basic":
            print("  ✅ Profile management")
        else:
            print("  ❌ Profile management issues")
            return False
        
        # Test session history
        await memory.update_session_history(test_user, "Test query", {"intent": "test", "success": True})
        updated_context = await memory.get_user_context(test_user)
        
        if len(updated_context["recent_history"]) > 0:
            print("  ✅ Session history integration")
        else:
            print("  ❌ Session history integration issues")
            return False
        
        # Test API caching
        cache_params = {"query": "test"}
        cache_response = {"results": ["data1", "data2"]}
        
        await memory.cache_api_response("test_endpoint", cache_params, cache_response)
        cached = await memory.get_cached_response("test_endpoint", cache_params)
        
        if cached == cache_response:
            print("  ✅ API caching integration")
        else:
            print("  ❌ API caching integration issues")
            return False
        
        # Test cleanup
        cleaned = await memory.cleanup_expired_cache()
        stats = await memory.get_database_stats()
        
        if "db_size_mb" in stats:
            print("  ✅ Database maintenance")
        else:
            print("  ❌ Database maintenance issues")
            return False
        
        # Cleanup test database
        os.remove("test_memory.db")
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced memory store failed: {e}")
        return False

async def test_json_support():
    """Test JSON storage and querying capabilities"""
    print("\n📄 Testing JSON Support...")
    
    try:
        from database.manager import DatabaseManager
        
        db = DatabaseManager("test_json.db")
        await db.initialize()
        
        # Test complex JSON data
        complex_profile = {
            "mutuelle": {
                "provider": "MGEN",
                "coverage": {"consultation": 0.7, "specialist": 0.6},
                "options": ["dental", "optical"]
            },
            "medical_history": [
                {"condition": "diabetes", "diagnosed": "2020-01-15"},
                {"condition": "hypertension", "diagnosed": "2021-03-10"}
            ],
            "preferences": {
                "language": "fr",
                "notifications": True,
                "distance_limit_km": 10
            }
        }
        
        await db.update_user_profile("json_test_user", complex_profile)
        retrieved = await db.get_user_profile("json_test_user")
        
        # Verify nested data integrity
        if (retrieved["mutuelle"]["provider"] == "MGEN" and 
            len(retrieved["medical_history"]) == 2 and
            retrieved["preferences"]["distance_limit_km"] == 10):
            print("  ✅ Complex JSON storage")
        else:
            print("  ❌ Complex JSON integrity issues")
            return False
        
        # Test document analysis storage
        analysis_data = {
            "extracted_text": "Patient: John Doe\nMutuelle: MGEN\nRemboursement: 70%",
            "entities": {
                "patient_name": "John Doe",
                "mutuelle": "MGEN",
                "reimbursement_rate": 0.7
            },
            "confidence_score": 0.95
        }
        
        await db.store_document_analysis("json_test_user", "test_doc.pdf", "application/pdf", analysis_data)
        docs = await db.get_user_documents("json_test_user", 1)
        
        if len(docs) == 1 and docs[0]["analysis"]["confidence_score"] == 0.95:
            print("  ✅ Document analysis JSON storage")
        else:
            print("  ❌ Document analysis storage issues")
            return False
        
        os.remove("test_json.db")
        return True
        
    except Exception as e:
        print(f"  ❌ JSON support failed: {e}")
        return False

async def main():
    """Run Prompt 2 database validation"""
    print("🚀 V2 PROMPT 2: DATABASE ARCHITECTURE VALIDATION")
    print("=" * 55)
    
    tests = [
        ("Database Manager", test_database_manager()),
        ("Enhanced Memory Store", test_enhanced_memory_store()),
        ("JSON Support", test_json_support())
    ]
    
    results = []
    for test_name, test_coro in tests:
        result = await test_coro
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 PROMPT 2 COMPLETION SUMMARY")
    print("=" * 55)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} database components validated")
    
    if passed == total:
        print("🎉 PROMPT 2 COMPLETED SUCCESSFULLY")
        print("✅ Enhanced SQLite database architecture implemented")
        print("✅ JSON support and complex data structures working")
        print("✅ API caching system functional")
        print("✅ User profile and session management enhanced")
        print("✅ Document analysis storage ready")
        return True
    else:
        print("⚠️  Some database components need attention")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
