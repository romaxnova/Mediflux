"""
Production Database Configuration for Mediflux V2
Handles environment-specific database settings and optimizations
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Environment-aware database configuration"""
    
    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or os.getenv('MEDIFLUX_ENV', 'development')
        self.setup_config()
    
    def setup_config(self):
        """Setup configuration based on environment"""
        configs = {
            'development': {
                'db_path': 'data/mediflux.db',
                'keep_raw_files': True,
                'enable_wal': False,
                'cache_size': 2000,
                'log_level': 'DEBUG'
            },
            'staging': {
                'db_path': 'mediflux_staging.db', 
                'keep_raw_files': False,
                'enable_wal': True,
                'cache_size': 5000,
                'log_level': 'INFO'
            },
            'production': {
                'db_path': 'prod/mediflux_production.db',
                'keep_raw_files': False,
                'enable_wal': True,
                'cache_size': 10000,
                'log_level': 'WARNING'
            }
        }
        
        config = configs.get(self.environment, configs['development'])
        
        for key, value in config.items():
            setattr(self, key, value)
        
        # Override with environment variables if present
        self.db_path = os.getenv('DATABASE_PATH', self.db_path)
        self.keep_raw_files = os.getenv('KEEP_RAW_FILES', str(self.keep_raw_files)).lower() == 'true'
    
    def get_connection(self) -> sqlite3.Connection:
        """Get optimized database connection"""
        conn = sqlite3.connect(self.db_path)
        
        # Apply performance optimizations
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA cache_size = {self.cache_size}")
        conn.execute("PRAGMA temp_store = MEMORY")
        
        if self.enable_wal:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
        
        return conn
    
    def get_db_info(self):
        """Get database information and statistics"""
        if not os.path.exists(self.db_path):
            return {"status": "not_found", "path": self.db_path}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get table counts
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_info = {}
            
            for (table_name,) in tables:
                count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                table_info[table_name] = count
            
            # Get database size
            db_size = os.path.getsize(self.db_path)
            
            # Get metadata if available
            try:
                metadata = cursor.execute("SELECT key, value FROM app_metadata").fetchall()
                metadata_dict = dict(metadata)
            except sqlite3.OperationalError:
                metadata_dict = {}
            
            info = {
                "status": "ready",
                "path": self.db_path,
                "environment": self.environment,
                "size_kb": round(db_size / 1024, 1),
                "tables": table_info,
                "metadata": metadata_dict
            }
            
            conn.close()
            return info
            
        except Exception as e:
            conn.close()
            return {"status": "error", "error": str(e), "path": self.db_path}

class ProductionDatabaseClient:
    """Production-optimized database client for Mediflux"""
    
    def __init__(self, environment: str = None):
        self.config = DatabaseConfig(environment)
        self.db_path = self.config.db_path
    
    async def get_hospital_recommendations(self, department: str = None, max_results: int = 10) -> list:
        """Get hospital recommendations optimized for production"""
        conn = self.config.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT finess_id, name, city, department, postal_code,
                   mco_beds, occupancy_rate, availability_score,
                   emergency_capacity, activity_level
            FROM hospitals 
            WHERE mco_beds IS NOT NULL 
            AND occupancy_rate IS NOT NULL
            AND occupancy_rate < 0.9
        """
        params = []
        
        if department:
            query += " AND department = ?"
            params.append(department)
        
        query += " ORDER BY availability_score DESC, mco_beds DESC LIMIT ?"
        params.append(max_results)
        
        results = cursor.execute(query, params).fetchall()
        conn.close()
        
        recommendations = []
        for row in results:
            rec = {
                'finess_id': row[0],
                'name': row[1],
                'city': row[2], 
                'department': row[3],
                'postal_code': row[4],
                'beds': row[5],
                'occupancy_rate': row[6],
                'availability_score': row[7],
                'emergency_capacity': row[8],
                'activity_level': row[9],
                'recommendation_reason': f"Low occupancy ({row[6]:.1%}) - faster access likely",
                'estimated_available_beds': int(row[5] * (1 - row[6])) if row[5] and row[6] else None
            }
            recommendations.append(rec)
        
        return recommendations
    
    async def get_regional_analysis(self, department: str) -> dict:
        """Get regional hospital analysis"""
        conn = self.config.get_connection()
        cursor = conn.cursor()
        
        # Regional metrics
        regional_query = """
            SELECT department, region_name, total_hospitals, total_beds, 
                   emergency_services, emergency_density
            FROM regional_metrics WHERE department = ?
        """
        regional_data = cursor.execute(regional_query, (department,)).fetchone()
        
        # Hospital breakdown
        hospital_query = """
            SELECT activity_level, COUNT(*) as count, 
                   AVG(occupancy_rate) as avg_occupancy,
                   AVG(availability_score) as avg_availability
            FROM hospitals 
            WHERE department = ? AND activity_level IS NOT NULL
            GROUP BY activity_level
        """
        hospital_breakdown = cursor.execute(hospital_query, (department,)).fetchall()
        
        conn.close()
        
        analysis = {
            'department': department,
            'regional_metrics': {
                'total_hospitals': regional_data[2] if regional_data else 0,
                'total_beds': regional_data[3] if regional_data else 0, 
                'emergency_services': regional_data[4] if regional_data else 0,
                'emergency_density': regional_data[5] if regional_data else 'UNKNOWN'
            } if regional_data else {},
            'hospital_breakdown': [
                {
                    'activity_level': row[0],
                    'count': row[1],
                    'avg_occupancy': round(row[2], 3) if row[2] else None,
                    'avg_availability': round(row[3], 1) if row[3] else None
                }
                for row in hospital_breakdown
            ]
        }
        
        return analysis
    
    def health_check(self) -> dict:
        """Production health check endpoint"""
        db_info = self.config.get_db_info()
        
        if db_info['status'] != 'ready':
            return {
                'status': 'unhealthy',
                'database': db_info,
                'timestamp': None
            }
        
        # Check query performance
        import time
        start_time = time.time()
        
        conn = self.config.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hospitals WHERE occupancy_rate < 0.8")
        available_hospitals = cursor.fetchone()[0]
        conn.close()
        
        query_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'status': 'healthy',
            'database': {
                'path': db_info['path'],
                'size_kb': db_info['size_kb'],
                'environment': self.config.environment,
                'hospitals_available': available_hospitals
            },
            'performance': {
                'query_time_ms': query_time
            },
            'timestamp': time.time()
        }

# Global instance for production use
production_db = ProductionDatabaseClient('production')

# Environment detection helper
def get_database_client(environment: str = None) -> ProductionDatabaseClient:
    """Get database client for specified environment"""
    env = environment or os.getenv('MEDIFLUX_ENV', 'development')
    return ProductionDatabaseClient(env)
