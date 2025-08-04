"""
Database Architecture Tests
Tests for enhanced database functionality
"""

import asyncio
import os
import sys

# Add modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(os.path.dirname(current_dir), 'modules')
sys.path.insert(0, modules_dir)

async def test_database_manager():
    """Test core database manager functionality"""
    try:
        from database.manager import DatabaseManager
        
        db = DatabaseManager("test_db_manager.db")
        await db.initialize()
        
        # Test user profile
        await db.update_user_profile("test_user", {"mutuelle": "test"})
        profile = await db.get_user_profile("test_user")
        profile_ok = profile["mutuelle"] == "test"
        
        # Test caching
        await db.cache_response("test_api", {"q": "test"}, {"data": "test"})
        cached = await db.get_cached_response("test_api", {"q": "test"})
        cache_ok = cached["data"] == "test"
        
        # Cleanup
        if os.path.exists("test_db_manager.db"):
            os.remove("test_db_manager.db")
        
        return profile_ok and cache_ok
        
    except Exception:
        return False

async def test_json_support():
    """Test complex JSON data handling"""
    try:
        from database.manager import DatabaseManager
        
        db = DatabaseManager("test_json_support.db")
        await db.initialize()
        
        # Complex JSON structure
        complex_data = {
            "mutuelle": {"provider": "MGEN", "coverage": {"consultation": 0.7}},
            "history": [{"condition": "diabetes", "date": "2020-01-01"}]
        }
        
        await db.update_user_profile("json_user", complex_data)
        retrieved = await db.get_user_profile("json_user")
        
        json_ok = (retrieved["mutuelle"]["provider"] == "MGEN" and 
                  len(retrieved["history"]) == 1)
        
        # Cleanup
        if os.path.exists("test_json_support.db"):
            os.remove("test_json_support.db")
        
        return json_ok
        
    except Exception:
        return False
