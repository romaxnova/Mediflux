"""
V2 Enhanced Database Manager
Comprehensive SQLite implementation with JSON support, caching, and migrations
"""

import sqlite3
import json
import asyncio
import aiosqlite
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


class DatabaseManager:
    """
    Enhanced database manager for Mediflux V2
    Handles user profiles, sessions, API caching, and document storage
    """
    
    def __init__(self, db_path: str = "mediflux_v2.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize database with proper schema and extensions"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable JSON1 extension
            await db.execute("PRAGMA journal_mode=WAL")
            
            # Create tables
            await self._create_tables(db)
            await db.commit()
            
        self.logger.info(f"Database initialized: {self.db_path}")
    
    async def _create_tables(self, db):
        """Create all required tables"""
        
        # Users table - profiles and preferences
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                profile JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table - query history and results
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                intent TEXT,
                result JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # API cache table - external API responses
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                params_hash TEXT NOT NULL,
                response JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(endpoint, params_hash)
            )
        """)
        
        # Documents table - analysis results
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT,
                analysis JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users (user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON sessions (timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_endpoint ON api_cache (endpoint)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache (expires_at)")
    
    # User Profile Management
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT profile FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None
    
    async def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        """Update or create user profile"""
        profile_json = json.dumps(profile)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, profile, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, profile_json))
            await db.commit()
    
    # Session History Management
    async def add_session_entry(self, user_id: str, query: str, intent: str = None, result: Dict[str, Any] = None):
        """Add session history entry"""
        result_json = json.dumps(result) if result else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sessions (user_id, query, intent, result)
                VALUES (?, ?, ?, ?)
            """, (user_id, query, intent, result_json))
            await db.commit()
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent user sessions"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT query, intent, result, timestamp
                FROM sessions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = await cursor.fetchall()
            return [
                {
                    "query": row[0],
                    "intent": row[1],
                    "result": json.loads(row[2]) if row[2] else None,
                    "timestamp": row[3]
                }
                for row in rows
            ]
    
    # API Caching System
    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{endpoint}:{params_str}".encode()).hexdigest()
    
    async def get_cached_response(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached API response if not expired"""
        cache_key = self._generate_cache_key(endpoint, params)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT response FROM api_cache
                WHERE endpoint = ? AND params_hash = ? AND expires_at > CURRENT_TIMESTAMP
            """, (endpoint, cache_key))
            
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None
    
    async def cache_response(self, endpoint: str, params: Dict[str, Any], response: Dict[str, Any], ttl_hours: int = 24):
        """Cache API response with TTL"""
        cache_key = self._generate_cache_key(endpoint, params)
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        response_json = json.dumps(response)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO api_cache (endpoint, params_hash, response, expires_at)
                VALUES (?, ?, ?, ?)
            """, (endpoint, cache_key, response_json, expires_at))
            await db.commit()
    
    # Document Management
    async def store_document_analysis(self, user_id: str, filename: str, content_type: str, analysis: Dict[str, Any]):
        """Store document analysis results"""
        analysis_json = json.dumps(analysis)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO documents (user_id, filename, content_type, analysis)
                VALUES (?, ?, ?, ?)
            """, (user_id, filename, content_type, analysis_json))
            await db.commit()
    
    async def get_user_documents(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user document analysis history"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT filename, content_type, analysis, created_at
                FROM documents
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = await cursor.fetchall()
            return [
                {
                    "filename": row[0],
                    "content_type": row[1],
                    "analysis": json.loads(row[2]) if row[2] else None,
                    "timestamp": row[3]
                }
                for row in rows
            ]
    
    # Maintenance Operations
    async def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        async with aiosqlite.connect(self.db_path) as db:
            result = await db.execute("""
                DELETE FROM api_cache WHERE expires_at < CURRENT_TIMESTAMP
            """)
            await db.commit()
            return result.rowcount
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Count records in each table
            for table in ['users', 'sessions', 'api_cache', 'documents']:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = await cursor.fetchone()
                stats[f"{table}_count"] = count[0]
            
            # Database file size
            db_path = Path(self.db_path)
            stats["db_size_mb"] = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
            
            return stats


# Enhanced Memory Store with Database Integration
class EnhancedMemoryStore:
    """
    Enhanced memory store using DatabaseManager
    Replaces the basic SQLite implementation
    """
    
    def __init__(self, db_path: str = "mediflux_v2.db"):
        self.db = DatabaseManager(db_path)
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            await self.db.initialize()
            self._initialized = True
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get complete user context (profile + recent history)"""
        await self._ensure_initialized()
        
        profile = await self.db.get_user_profile(user_id) or {}
        recent_history = await self.db.get_user_sessions(user_id, limit=5)
        
        return {
            "profile": profile,
            "recent_history": recent_history
        }
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update user profile"""
        await self._ensure_initialized()
        
        # Get existing profile and merge updates
        existing_profile = await self.db.get_user_profile(user_id) or {}
        existing_profile.update(updates)
        
        await self.db.update_user_profile(user_id, existing_profile)
    
    async def update_session_history(self, user_id: str, query: str, result: Dict[str, Any]):
        """Add entry to session history"""
        await self._ensure_initialized()
        
        intent = result.get("intent")
        await self.db.add_session_entry(user_id, query, intent, result)
