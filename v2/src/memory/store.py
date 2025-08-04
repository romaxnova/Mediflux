"""
V2 Memory Store - Enhanced Database Integration
Manages user profiles, session history, and context using enhanced SQLite
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import os
import sys

# Add database module to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.dirname(current_dir)
sys.path.insert(0, modules_dir)

from database.manager import DatabaseManager


class MemoryStore:
    """
    Enhanced memory store using DatabaseManager
    Handles user profiles, session history, and caching
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to v2 directory
            base_dir = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(base_dir, "mediflux_v2.db")
        
        self.db = DatabaseManager(db_path)
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            await self.db.initialize()
            self._initialized = True
            self.logger.info("Memory store initialized with enhanced database")
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get complete user context (profile + recent history)"""
        await self._ensure_initialized()
        
        profile = await self.db.get_user_profile(user_id) or {}
        recent_history = await self.db.get_user_sessions(user_id, limit=5)
        
        return {
            "user_id": user_id,
            "profile": profile,
            "recent_history": recent_history
        }
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update user profile with new data"""
        await self._ensure_initialized()
        
        # Get existing profile and merge updates
        existing_profile = await self.db.get_user_profile(user_id) or {}
        existing_profile.update(updates)
        
        await self.db.update_user_profile(user_id, existing_profile)
        self.logger.debug(f"Updated profile for user {user_id}: {list(updates.keys())}")
    
    async def update_session_history(self, user_id: str, query: str, result: Dict[str, Any]):
        """Add entry to session history"""
        await self._ensure_initialized()
        
        intent = result.get("intent", "unknown")
        await self.db.add_session_entry(user_id, query, intent, result)
        
        self.logger.debug(f"Added session entry for user {user_id}: {intent}")
    
    async def cache_api_response(self, endpoint: str, params: Dict[str, Any], response: Dict[str, Any], ttl_hours: int = 24):
        """Cache API response for reuse"""
        await self._ensure_initialized()
        await self.db.cache_response(endpoint, params, response, ttl_hours)
    
    async def get_cached_response(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached API response if available"""
        await self._ensure_initialized()
        return await self.db.get_cached_response(endpoint, params)
    
    async def store_document_analysis(self, user_id: str, filename: str, content_type: str, analysis: Dict[str, Any]):
        """Store document analysis results"""
        await self._ensure_initialized()
        await self.db.store_document_analysis(user_id, filename, content_type, analysis)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for monitoring"""
        await self._ensure_initialized()
        return await self.db.get_database_stats()
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        await self._ensure_initialized()
        return await self.db.cleanup_expired_cache()
