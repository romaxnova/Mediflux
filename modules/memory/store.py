"""
Memory Store for V2 Mediflux
Lightweight local storage for user profiles and session history
SQLite-based with automatic compression and privacy controls
"""

import sqlite3
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os


class MemoryStore:
    """
    Local memory store for user profiles and session history
    Uses SQLite for persistence with privacy-first design
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to v2/data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, "data", "user_memory.db")
        
        self.db_path = db_path
        self._ensure_directory_exists()
        self._init_database()
    
    def _ensure_directory_exists(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response JSON NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compressed_sessions (
                    user_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    session_count INTEGER NOT NULL,
                    last_compressed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id)
                )
            """)
            
            conn.commit()
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context including profile and recent history
        """
        def _get_context():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get user profile
                profile_row = conn.execute(
                    "SELECT profile FROM user_profiles WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                
                profile = json.loads(profile_row["profile"]) if profile_row else {}
                
                # Get recent session history (last 10 interactions)
                history_rows = conn.execute("""
                    SELECT query, response, timestamp 
                    FROM session_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """, (user_id,)).fetchall()
                
                recent_history = [
                    {
                        "query": row["query"],
                        "response": json.loads(row["response"]),
                        "timestamp": row["timestamp"]
                    }
                    for row in history_rows
                ]
                
                # Get compressed session summary if available
                summary_row = conn.execute(
                    "SELECT summary, session_count FROM compressed_sessions WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                
                session_summary = {
                    "summary": summary_row["summary"] if summary_row else "",
                    "total_sessions": summary_row["session_count"] if summary_row else 0
                }
                
                return {
                    "user_id": user_id,
                    "profile": profile,
                    "recent_history": recent_history,
                    "session_summary": session_summary
                }
        
        # Run in thread to avoid blocking
        return await asyncio.get_event_loop().run_in_executor(None, _get_context)
    
    async def update_user_profile(self, user_id: str, profile_updates: Dict[str, Any]) -> None:
        """
        Update user profile with new information
        """
        def _update_profile():
            with sqlite3.connect(self.db_path) as conn:
                # Get existing profile
                existing_row = conn.execute(
                    "SELECT profile FROM user_profiles WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                
                if existing_row:
                    existing_profile = json.loads(existing_row[0])
                    # Merge updates
                    existing_profile.update(profile_updates)
                    
                    conn.execute("""
                        UPDATE user_profiles 
                        SET profile = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ?
                    """, (json.dumps(existing_profile), user_id))
                else:
                    # Create new profile
                    conn.execute("""
                        INSERT INTO user_profiles (user_id, profile) 
                        VALUES (?, ?)
                    """, (user_id, json.dumps(profile_updates)))
                
                conn.commit()
        
        await asyncio.get_event_loop().run_in_executor(None, _update_profile)
    
    async def update_session_history(self, user_id: str, query: str, response: Dict[str, Any]) -> None:
        """
        Add new interaction to session history
        """
        def _update_history():
            with sqlite3.connect(self.db_path) as conn:
                # Add new session record
                conn.execute("""
                    INSERT INTO session_history (user_id, query, response) 
                    VALUES (?, ?, ?)
                """, (user_id, query, json.dumps(response)))
                
                # Check if we need to compress old sessions
                session_count = conn.execute(
                    "SELECT COUNT(*) FROM session_history WHERE user_id = ?",
                    (user_id,)
                ).fetchone()[0]
                
                # Compress if we have more than 50 sessions
                if session_count > 50:
                    self._compress_old_sessions(conn, user_id)
                
                conn.commit()
        
        await asyncio.get_event_loop().run_in_executor(None, _update_history)
    
    def _compress_old_sessions(self, conn: sqlite3.Connection, user_id: str) -> None:
        """
        Compress old session history to save space
        TODO: Implement LLM-based summarization when local AI is available
        """
        # Get old sessions (older than 30 days or beyond the last 20)
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        old_sessions = conn.execute("""
            SELECT query, response, timestamp 
            FROM session_history 
            WHERE user_id = ? AND (
                timestamp < ? OR 
                id NOT IN (
                    SELECT id FROM session_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 20
                )
            )
            ORDER BY timestamp
        """, (user_id, cutoff_date, user_id)).fetchall()
        
        if not old_sessions:
            return
        
        # Simple summarization for now (TODO: replace with LLM)
        query_types = {}
        for session in old_sessions:
            response_data = json.loads(session[1])
            intent = response_data.get("intent", "unknown")
            query_types[intent] = query_types.get(intent, 0) + 1
        
        summary = f"User had {len(old_sessions)} previous interactions: " + \
                 ", ".join([f"{count} {intent} queries" for intent, count in query_types.items()])
        
        # Update or insert compressed summary
        existing_summary = conn.execute(
            "SELECT summary, session_count FROM compressed_sessions WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if existing_summary:
            new_summary = f"{existing_summary[0]}; {summary}"
            new_count = existing_summary[1] + len(old_sessions)
            conn.execute("""
                UPDATE compressed_sessions 
                SET summary = ?, session_count = ?, last_compressed = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            """, (new_summary, new_count, user_id))
        else:
            conn.execute("""
                INSERT INTO compressed_sessions (user_id, summary, session_count) 
                VALUES (?, ?, ?)
            """, (user_id, summary, len(old_sessions)))
        
        # Delete compressed sessions
        session_ids = [str(session[0]) for session in old_sessions]
        if session_ids:
            placeholders = ",".join(["?" for _ in session_ids])
            conn.execute(f"""
                DELETE FROM session_history 
                WHERE user_id = ? AND id IN (
                    SELECT id FROM session_history 
                    WHERE user_id = ? AND (
                        timestamp < ? OR 
                        id NOT IN (
                            SELECT id FROM session_history 
                            WHERE user_id = ? 
                            ORDER BY timestamp DESC 
                            LIMIT 20
                        )
                    )
                )
            """, (user_id, user_id, cutoff_date, user_id))
    
    async def clear_user_data(self, user_id: str) -> None:
        """
        Clear all data for a user (GDPR compliance)
        """
        def _clear_data():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM session_history WHERE user_id = ?", (user_id,))
                conn.execute("DELETE FROM compressed_sessions WHERE user_id = ?", (user_id,))
                conn.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
                conn.commit()
        
        await asyncio.get_event_loop().run_in_executor(None, _clear_data)
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a user
        """
        def _get_stats():
            with sqlite3.connect(self.db_path) as conn:
                # Session count
                session_count = conn.execute(
                    "SELECT COUNT(*) FROM session_history WHERE user_id = ?",
                    (user_id,)
                ).fetchone()[0]
                
                # Compressed session count
                compressed_row = conn.execute(
                    "SELECT session_count FROM compressed_sessions WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                
                total_sessions = session_count + (compressed_row[0] if compressed_row else 0)
                
                # First interaction date
                first_interaction = conn.execute(
                    "SELECT MIN(timestamp) FROM session_history WHERE user_id = ?",
                    (user_id,)
                ).fetchone()[0]
                
                # Most common intents
                intent_counts = {}
                sessions = conn.execute(
                    "SELECT response FROM session_history WHERE user_id = ?",
                    (user_id,)
                ).fetchall()
                
                for session in sessions:
                    response_data = json.loads(session[0])
                    intent = response_data.get("intent", "unknown")
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
                
                return {
                    "total_sessions": total_sessions,
                    "recent_sessions": session_count,
                    "first_interaction": first_interaction,
                    "most_common_intents": dict(sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5])
                }
        
        return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data (GDPR compliance)
        """
        context = await self.get_user_context(user_id)
        stats = await self.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "profile": context["profile"],
            "session_history": context["recent_history"],
            "session_summary": context["session_summary"],
            "statistics": stats,
            "exported_at": datetime.now().isoformat()
        }
