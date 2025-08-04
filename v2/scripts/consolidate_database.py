#!/usr/bin/env python3
"""
Database Consolidation Script for Mediflux V2
Merges all scattered SQLite databases into a single production database
"""

import sqlite3
import shutil
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConsolidator:
    """Consolidates multiple SQLite databases into single production database"""
    
    def __init__(self):
        self.production_db = "mediflux_production.db"
        self.source_databases = [
            "data/mediflux.db",           # SAE data
            "data/open_medic.db",         # OpenMedic data  
            "data/user_memory.db",        # User sessions
            "mediflux_v2.db",            # Main app data
            "data/openmedic/openmedic_data.db"  # Additional OpenMedic
        ]
        
    def analyze_current_storage(self):
        """Analyze current database files and sizes"""
        logger.info("🔍 Analyzing current storage...")
        
        total_size = 0
        databases_found = []
        
        for db_path in self.source_databases:
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                total_size += size
                databases_found.append((db_path, size))
                logger.info(f"  Found: {db_path} ({size/1024:.1f}KB)")
        
        logger.info(f"📊 Total database size: {total_size/1024:.1f}KB")
        return databases_found, total_size
    
    def create_production_schema(self):
        """Create unified production database schema"""
        logger.info("🏗️  Creating production database schema...")
        
        # Remove existing production DB
        if os.path.exists(self.production_db):
            os.remove(self.production_db)
        
        conn = sqlite3.connect(self.production_db)
        cursor = conn.cursor()
        
        # Enable foreign keys and performance optimizations
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        # Core application tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User profiles and sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                profile_data TEXT,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API cache for external services
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                response_data TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # SAE Hospital Data (consolidated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                finess_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT,
                region TEXT,
                commune_insee TEXT,
                city TEXT,
                postal_code TEXT,
                category TEXT,
                legal_status TEXT,
                address TEXT,
                -- Activity metrics
                mco_beds INTEGER,
                occupancy_rate REAL,
                activity_level TEXT,
                -- Emergency services
                emergency_capacity TEXT,
                emergency_services INTEGER,
                -- Regional context
                regional_density TEXT,
                availability_score REAL,
                -- Metadata
                data_year INTEGER DEFAULT 2023,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Regional hospital metrics (aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regional_metrics (
                department TEXT PRIMARY KEY,
                region_name TEXT,
                total_hospitals INTEGER,
                total_beds INTEGER,
                emergency_services INTEGER,
                population INTEGER, -- Will be added later
                hospitals_per_100k REAL,
                beds_per_100k REAL,
                emergency_density TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # OpenMedic medication data (sampled/aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                cip13 TEXT PRIMARY KEY,
                denomination TEXT,
                atc_code TEXT,
                base_remb REAL,
                taux_remb REAL,
                nb_boites INTEGER,
                montant_remb REAL,
                region_code TEXT,
                data_year INTEGER DEFAULT 2024,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Professional demographics (DREES) - aggregated
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professional_demographics (
                profession TEXT,
                region_code TEXT,
                department TEXT,
                year INTEGER,
                count INTEGER,
                density_per_100k REAL,
                age_avg REAL,
                female_percentage REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (profession, region_code, year)
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_hospitals_dept ON hospitals(department)",
            "CREATE INDEX IF NOT EXISTS idx_hospitals_city ON hospitals(city)",
            "CREATE INDEX IF NOT EXISTS idx_hospitals_occupancy ON hospitals(occupancy_rate)",
            "CREATE INDEX IF NOT EXISTS idx_hospitals_availability ON hospitals(availability_score)",
            "CREATE INDEX IF NOT EXISTS idx_medications_atc ON medications(atc_code)",
            "CREATE INDEX IF NOT EXISTS idx_medications_region ON medications(region_code)",
            "CREATE INDEX IF NOT EXISTS idx_demographics_prof ON professional_demographics(profession)",
            "CREATE INDEX IF NOT EXISTS idx_demographics_dept ON professional_demographics(department)",
            "CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache(expires_at)"
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        # Insert metadata
        cursor.execute("""
            INSERT INTO app_metadata (key, value) VALUES 
            ('version', '2.0'),
            ('created', datetime('now')),
            ('data_sources', 'SAE2023,OpenMedic2024,DREES2024'),
            ('environment', 'production')
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Production database schema created")
    
    def migrate_sae_data(self):
        """Migrate SAE hospital data to production database"""
        logger.info("🏥 Migrating SAE hospital data...")
        
        sae_db = "data/mediflux.db"
        if not os.path.exists(sae_db):
            logger.warning(f"SAE database not found: {sae_db}")
            return
        
        source_conn = sqlite3.connect(sae_db)
        prod_conn = sqlite3.connect(self.production_db)
        
        # Get consolidated hospital data
        query = """
            SELECT 
                h.fi as finess_id,
                h.rs as name,
                h.dep as department,
                h.reg as region,
                h.cominsee as commune_insee,
                h.nomcom as city,
                h.cpo as postal_code,
                h.cat as category,
                h.stj as legal_status,
                (h.typvoi || ' ' || h.nomvoi || ', ' || h.libcom) as address,
                m.lit_mco as mco_beds,
                m.capacity_ratio as occupancy_rate,
                m.activity_level,
                u.emergency_capacity,
                (COALESCE(u.autsu, 0) + COALESCE(u.autgen, 0) + COALESCE(u.autsais, 0) + COALESCE(u.autped, 0)) as emergency_services,
                r.emergency_density as regional_density,
                CASE 
                    WHEN m.capacity_ratio IS NOT NULL THEN ROUND((1 - m.capacity_ratio) * 100, 1)
                    ELSE NULL 
                END as availability_score
            FROM sae_hospitals h
            LEFT JOIN sae_mco_activity m ON h.fi = m.fi
            LEFT JOIN sae_urgences u ON h.fi = u.fi  
            LEFT JOIN sae_regional_metrics r ON h.dep = r.dep
            WHERE h.fi IS NOT NULL AND h.rs IS NOT NULL
        """
        
        hospitals = source_conn.execute(query).fetchall()
        
        # Insert into production database
        prod_cursor = prod_conn.cursor()
        insert_query = """
            INSERT OR REPLACE INTO hospitals 
            (finess_id, name, department, region, commune_insee, city, postal_code, 
             category, legal_status, address, mco_beds, occupancy_rate, activity_level,
             emergency_capacity, emergency_services, regional_density, availability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        prod_cursor.executemany(insert_query, hospitals)
        
        # Migrate regional metrics
        regional_query = """
            SELECT dep, nomcom_main, total_hospitals, total_mco_beds, 
                   total_emergency_services, emergency_density
            FROM sae_regional_metrics
        """
        regional_data = source_conn.execute(regional_query).fetchall()
        
        regional_insert = """
            INSERT OR REPLACE INTO regional_metrics 
            (department, region_name, total_hospitals, total_beds, emergency_services, emergency_density)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        prod_cursor.executemany(regional_insert, regional_data)
        
        prod_conn.commit()
        source_conn.close()
        prod_conn.close()
        
        logger.info(f"✅ Migrated {len(hospitals)} hospitals and {len(regional_data)} regional metrics")
    
    def migrate_openmedic_sample(self, sample_size=10000):
        """Migrate a sample of OpenMedic data (full dataset too large for production)"""
        logger.info(f"💊 Migrating OpenMedic sample ({sample_size} records)...")
        
        # Find OpenMedic database
        openmedic_dbs = [
            "data/open_medic.db",
            "data/openmedic/openmedic_data.db"
        ]
        
        source_db = None
        for db in openmedic_dbs:
            if os.path.exists(db):
                source_db = db
                break
        
        if not source_db:
            logger.warning("OpenMedic database not found")
            return
        
        source_conn = sqlite3.connect(source_db)
        prod_conn = sqlite3.connect(self.production_db)
        
        # Get sample of medication data (highest reimbursement amounts)
        query = f"""
            SELECT cip13, denomination, atc_code, base_remb, taux_remb, 
                   nb_boites, montant_remb, region_code
            FROM openmedic_data 
            WHERE montant_remb > 0 
            ORDER BY montant_remb DESC 
            LIMIT {sample_size}
        """
        
        try:
            medications = source_conn.execute(query).fetchall()
            
            prod_cursor = prod_conn.cursor()
            insert_query = """
                INSERT OR REPLACE INTO medications 
                (cip13, denomination, atc_code, base_remb, taux_remb, nb_boites, montant_remb, region_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            prod_cursor.executemany(insert_query, medications)
            prod_conn.commit()
            
            logger.info(f"✅ Migrated {len(medications)} medication records")
            
        except sqlite3.OperationalError as e:
            logger.warning(f"OpenMedic migration failed: {e}")
        
        source_conn.close()
        prod_conn.close()
    
    def optimize_production_db(self):
        """Optimize production database for performance"""
        logger.info("⚡ Optimizing production database...")
        
        conn = sqlite3.connect(self.production_db)
        cursor = conn.cursor()
        
        # Vacuum and analyze
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        
        # Update statistics
        cursor.execute("""
            INSERT OR REPLACE INTO app_metadata (key, value) VALUES 
            ('last_optimized', datetime('now')),
            ('total_hospitals', (SELECT COUNT(*) FROM hospitals)),
            ('total_medications', (SELECT COUNT(*) FROM medications)),
            ('database_size_kb', ?)
        """, (os.path.getsize(self.production_db) // 1024,))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Database optimization complete")
    
    def consolidate(self, cleanup_sources=False):
        """Run full database consolidation"""
        logger.info("🚀 Starting database consolidation...")
        
        # Analysis
        databases_found, total_size = self.analyze_current_storage()
        
        # Create production database
        self.create_production_schema()
        
        # Migrate data
        self.migrate_sae_data()
        self.migrate_openmedic_sample()
        
        # Optimize
        self.optimize_production_db()
        
        # Final statistics
        prod_size = os.path.getsize(self.production_db)
        compression_ratio = (1 - prod_size / total_size) * 100 if total_size > 0 else 0
        
        logger.info(f"✅ Consolidation complete!")
        logger.info(f"📊 Before: {total_size/1024:.1f}KB across {len(databases_found)} files")
        logger.info(f"📊 After: {prod_size/1024:.1f}KB in single file")
        logger.info(f"📊 Compression: {compression_ratio:.1f}%")
        
        if cleanup_sources:
            logger.info("🧹 Cleaning up source databases...")
            for db_path, _ in databases_found:
                if db_path != self.production_db and os.path.exists(db_path):
                    os.remove(db_path)
                    logger.info(f"  Removed: {db_path}")
        
        logger.info(f"🎉 Production database ready: {self.production_db}")

def main():
    """Main consolidation process"""
    consolidator = DatabaseConsolidator()
    
    # Run consolidation (cleanup_sources=False for safety)
    consolidator.consolidate(cleanup_sources=False)
    
    print("\n" + "="*50)
    print("Database consolidation complete!")
    print(f"Production database: {consolidator.production_db}")
    print("Ready for deployment 🚀")

if __name__ == "__main__":
    main()
