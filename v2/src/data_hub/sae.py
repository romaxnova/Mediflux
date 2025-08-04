"""
SAE (Statistique Annuelle des Établissements) Data Integration
Processes French hospital statistics for capacity and activity analysis
"""

import pandas as pd
import sqlite3
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv

logger = logging.getLogger(__name__)

class SAEClient:
    """Client for processing SAE hospital statistics data"""
    
    def __init__(self, db_path: str = "data/mediflux.db"):
        self.db_path = db_path
        self.data_dir = Path("data/sae")
        self.csv_dir = self.data_dir / "SAE 2023 Bases statistiques - formats SAS-CSV/Bases statistiques/Bases CSV"
        
    async def initialize_database(self):
        """Initialize SAE tables in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hospital identity and location
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sae_hospitals (
                fi TEXT PRIMARY KEY,  -- FINESS identifier
                rs TEXT,             -- Hospital name
                dep TEXT,            -- Department code
                reg TEXT,            -- Region code
                cominsee TEXT,       -- INSEE commune code
                nomcom TEXT,         -- Commune name
                cat TEXT,            -- Category
                stj TEXT,            -- Legal status
                typvoi TEXT,         -- Street type
                nomvoi TEXT,         -- Street name
                cpo TEXT,            -- Postal code
                libcom TEXT,         -- City name
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # MCO activity data (Medicine-Surgery-Obstetrics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sae_mco_activity (
                fi TEXT,
                rs TEXT,
                lit_mco INTEGER,     -- Total MCO beds
                jli_mco INTEGER,     -- MCO bed-days
                sejhc_mco INTEGER,   -- Complete stays
                sej0_mco INTEGER,    -- Same-day stays
                jou_mco INTEGER,     -- Patient days
                capacity_ratio REAL, -- Occupancy rate
                activity_level TEXT, -- HIGH/MEDIUM/LOW based on stays
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fi) REFERENCES sae_hospitals (fi)
            )
        """)
        
        # Emergency department data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sae_urgences (
                fi TEXT,
                rs TEXT,
                autsu INTEGER,       -- General emergency authorization
                autgen INTEGER,      -- General emergency service
                autsais INTEGER,     -- Emergency service SAMU/SMUR
                autped INTEGER,      -- Pediatric emergency
                emg INTEGER,         -- Emergency availability
                emergency_capacity TEXT, -- FULL/PARTIAL/LIMITED
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fi) REFERENCES sae_hospitals (fi)
            )
        """)
        
        # Regional hospital density metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sae_regional_metrics (
                dep TEXT PRIMARY KEY,
                nomcom_main TEXT,
                total_hospitals INTEGER,
                total_mco_beds INTEGER,
                total_emergency_services INTEGER,
                hospitals_per_100k REAL,  -- Will need population data
                beds_per_100k REAL,
                emergency_density TEXT,   -- HIGH/MEDIUM/LOW
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("SAE database tables initialized")
    
    def _parse_csv_with_semicolon(self, file_path: Path) -> pd.DataFrame:
        """Parse CSV files with semicolon separators (French format)"""
        try:
            # Read with semicolon separator, handle encoding
            df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)
            return df
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding
            df = pd.read_csv(file_path, sep=';', encoding='latin-1', low_memory=False)
            return df
    
    async def process_hospital_identity(self) -> int:
        """Process hospital identity data"""
        id_file = self.csv_dir / "ID_2023r.csv"
        if not id_file.exists():
            logger.error(f"ID file not found: {id_file}")
            return 0
            
        df = self._parse_csv_with_semicolon(id_file)
        
        # Select relevant columns and clean data
        hospitals = []
        for _, row in df.iterrows():
            if pd.isna(row.get('fi')) or pd.isna(row.get('rs')):
                continue
                
            hospital = {
                'fi': str(row['fi']).strip(),
                'rs': str(row['rs']).strip(),
                'dep': str(row.get('dep', '')).strip(),
                'reg': str(row.get('reg', '')).strip(), 
                'cominsee': str(row.get('COMINSEE', '')).strip(),
                'nomcom': str(row.get('NOMCOM', '')).strip(),
                'cat': str(row.get('cat', '')).strip(),
                'stj': str(row.get('stj', '')).strip(),
                'typvoi': str(row.get('TYPVOI', '')).strip(),
                'nomvoi': str(row.get('NOMVOI', '')).strip(),
                'cpo': str(row.get('CPO', '')).strip(),
                'libcom': str(row.get('LIBCOM', '')).strip()
            }
            hospitals.append(hospital)
        
        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM sae_hospitals")
        
        # Insert new data
        for hospital in hospitals:
            cursor.execute("""
                INSERT OR REPLACE INTO sae_hospitals 
                (fi, rs, dep, reg, cominsee, nomcom, cat, stj, typvoi, nomvoi, cpo, libcom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hospital['fi'], hospital['rs'], hospital['dep'], hospital['reg'],
                hospital['cominsee'], hospital['nomcom'], hospital['cat'], hospital['stj'],
                hospital['typvoi'], hospital['nomvoi'], hospital['cpo'], hospital['libcom']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Processed {len(hospitals)} hospitals")
        return len(hospitals)
    
    async def process_mco_activity(self) -> int:
        """Process MCO (Medicine-Surgery-Obstetrics) activity data"""
        mco_file = self.csv_dir / "MCO_2023r.csv"
        if not mco_file.exists():
            logger.error(f"MCO file not found: {mco_file}")
            return 0
            
        df = self._parse_csv_with_semicolon(mco_file)
        
        activities = []
        for _, row in df.iterrows():
            if pd.isna(row.get('FI')) or pd.isna(row.get('RS')):
                continue
                
            # Convert numeric fields, handle missing values
            lit_mco = self._safe_int(row.get('LIT_MCO'))
            jli_mco = self._safe_int(row.get('JLI_MCO'))
            sejhc_mco = self._safe_int(row.get('SEJHC_MCO'))
            sej0_mco = self._safe_int(row.get('SEJ0_MCO'))
            jou_mco = self._safe_int(row.get('JOU_MCO'))
            
            # Calculate occupancy rate
            capacity_ratio = None
            if lit_mco and lit_mco > 0 and jli_mco:
                capacity_ratio = round(jli_mco / (lit_mco * 365), 3)
            
            # Classify activity level
            activity_level = "LOW"
            if sejhc_mco:
                if sejhc_mco > 10000:
                    activity_level = "HIGH"
                elif sejhc_mco > 3000:
                    activity_level = "MEDIUM"
            
            activity = {
                'fi': str(row['FI']).strip(),
                'rs': str(row['RS']).strip(),
                'lit_mco': lit_mco,
                'jli_mco': jli_mco,
                'sejhc_mco': sejhc_mco,
                'sej0_mco': sej0_mco,
                'jou_mco': jou_mco,
                'capacity_ratio': capacity_ratio,
                'activity_level': activity_level
            }
            activities.append(activity)
        
        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM sae_mco_activity")
        
        # Insert new data
        for activity in activities:
            cursor.execute("""
                INSERT INTO sae_mco_activity 
                (fi, rs, lit_mco, jli_mco, sejhc_mco, sej0_mco, jou_mco, capacity_ratio, activity_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity['fi'], activity['rs'], activity['lit_mco'], activity['jli_mco'],
                activity['sejhc_mco'], activity['sej0_mco'], activity['jou_mco'],
                activity['capacity_ratio'], activity['activity_level']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Processed MCO activity for {len(activities)} hospitals")
        return len(activities)
    
    async def process_emergency_services(self) -> int:
        """Process emergency department data"""
        urgences_file = self.csv_dir / "URGENCES_2023r.csv"
        if not urgences_file.exists():
            logger.error(f"Urgences file not found: {urgences_file}")
            return 0
            
        df = self._parse_csv_with_semicolon(urgences_file)
        
        emergency_services = []
        for _, row in df.iterrows():
            if pd.isna(row.get('FI')) or pd.isna(row.get('RS')):
                continue
            
            autsu = self._safe_int(row.get('AUTSU'))
            autgen = self._safe_int(row.get('AUTGEN')) 
            autsais = self._safe_int(row.get('AUTSAIS'))
            autped = self._safe_int(row.get('AUTPED'))
            emg = self._safe_int(row.get('EMG'))
            
            # Classify emergency capacity
            services_count = sum([autsu or 0, autgen or 0, autsais or 0, autped or 0])
            if services_count >= 3:
                emergency_capacity = "FULL"
            elif services_count >= 2:
                emergency_capacity = "PARTIAL"
            else:
                emergency_capacity = "LIMITED"
            
            emergency = {
                'fi': str(row['FI']).strip(),
                'rs': str(row['RS']).strip(),
                'autsu': autsu,
                'autgen': autgen,
                'autsais': autsais,
                'autped': autped,
                'emg': emg,
                'emergency_capacity': emergency_capacity
            }
            emergency_services.append(emergency)
        
        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM sae_urgences")
        
        # Insert new data
        for emergency in emergency_services:
            cursor.execute("""
                INSERT INTO sae_urgences 
                (fi, rs, autsu, autgen, autsais, autped, emg, emergency_capacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emergency['fi'], emergency['rs'], emergency['autsu'], emergency['autgen'],
                emergency['autsais'], emergency['autped'], emergency['emg'], emergency['emergency_capacity']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Processed emergency services for {len(emergency_services)} hospitals")
        return len(emergency_services)
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int, return None if invalid"""
        if pd.isna(value):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    async def calculate_regional_metrics(self) -> int:
        """Calculate regional hospital density metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get regional aggregations
        cursor.execute("""
            SELECT 
                h.dep,
                h.nomcom,
                COUNT(DISTINCT h.fi) as total_hospitals,
                COALESCE(SUM(m.lit_mco), 0) as total_mco_beds,
                COUNT(DISTINCT u.fi) as total_emergency_services
            FROM sae_hospitals h
            LEFT JOIN sae_mco_activity m ON h.fi = m.fi
            LEFT JOIN sae_urgences u ON h.fi = u.fi AND u.autsu = 1
            WHERE h.dep IS NOT NULL AND h.dep != ''
            GROUP BY h.dep
            HAVING COUNT(DISTINCT h.fi) > 0
            ORDER BY total_hospitals DESC
        """)
        
        regional_data = cursor.fetchall()
        
        # Clear existing metrics
        cursor.execute("DELETE FROM sae_regional_metrics")
        
        # Insert regional metrics
        for row in regional_data:
            dep, nomcom_main, total_hospitals, total_mco_beds, total_emergency_services = row
            
            # Classify emergency density (relative to hospital count)
            emergency_ratio = total_emergency_services / total_hospitals if total_hospitals > 0 else 0
            if emergency_ratio >= 0.7:
                emergency_density = "HIGH"
            elif emergency_ratio >= 0.4:
                emergency_density = "MEDIUM"
            else:
                emergency_density = "LOW"
            
            cursor.execute("""
                INSERT INTO sae_regional_metrics 
                (dep, nomcom_main, total_hospitals, total_mco_beds, total_emergency_services, emergency_density)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dep, nomcom_main, total_hospitals, total_mco_beds, total_emergency_services, emergency_density))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Calculated metrics for {len(regional_data)} departments")
        return len(regional_data)
    
    async def get_hospital_capacity_by_region(self, department: str = None, activity_level: str = None) -> List[Dict]:
        """Get hospital capacity information by region"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                h.fi, h.rs, h.dep, h.nomcom, h.cpo,
                m.lit_mco, m.capacity_ratio, m.activity_level,
                u.emergency_capacity,
                r.emergency_density
            FROM sae_hospitals h
            LEFT JOIN sae_mco_activity m ON h.fi = m.fi
            LEFT JOIN sae_urgences u ON h.fi = u.fi
            LEFT JOIN sae_regional_metrics r ON h.dep = r.dep
            WHERE 1=1
        """
        params = []
        
        if department:
            query += " AND h.dep = ?"
            params.append(department)
            
        if activity_level:
            query += " AND m.activity_level = ?"
            params.append(activity_level)
        
        query += " ORDER BY m.lit_mco DESC NULLS LAST"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        hospitals = []
        for row in results:
            hospital = {
                'finess_id': row[0],
                'name': row[1],
                'department': row[2],
                'city': row[3],
                'postal_code': row[4],
                'mco_beds': row[5],
                'occupancy_rate': row[6],
                'activity_level': row[7],
                'emergency_capacity': row[8],
                'regional_emergency_density': row[9]
            }
            hospitals.append(hospital)
        
        return hospitals
    
    async def get_low_capacity_hospitals(self, max_occupancy: float = 0.8) -> List[Dict]:
        """Find hospitals with lower occupancy rates for routing recommendations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                h.fi, h.rs, h.dep, h.nomcom, h.cpo,
                m.lit_mco, m.capacity_ratio, m.activity_level,
                u.emergency_capacity
            FROM sae_hospitals h
            INNER JOIN sae_mco_activity m ON h.fi = m.fi
            LEFT JOIN sae_urgences u ON h.fi = u.fi
            WHERE m.capacity_ratio IS NOT NULL 
            AND m.capacity_ratio < ?
            AND m.lit_mco > 10
            ORDER BY m.capacity_ratio ASC, m.lit_mco DESC
        """, (max_occupancy,))
        
        results = cursor.fetchall()
        conn.close()
        
        hospitals = []
        for row in results:
            hospital = {
                'finess_id': row[0],
                'name': row[1], 
                'department': row[2],
                'city': row[3],
                'postal_code': row[4],
                'beds': row[5],
                'occupancy_rate': row[6],
                'activity_level': row[7],
                'emergency_capacity': row[8],
                'availability_score': round((1 - row[6]) * 100, 1) if row[6] else None
            }
            hospitals.append(hospital)
        
        return hospitals
    
    async def process_all_sae_data(self) -> Dict[str, int]:
        """Process all SAE data sources"""
        await self.initialize_database()
        
        results = {
            'hospitals': await self.process_hospital_identity(),
            'mco_activity': await self.process_mco_activity(), 
            'emergency_services': await self.process_emergency_services(),
            'regional_metrics': await self.calculate_regional_metrics()
        }
        
        logger.info(f"SAE processing complete: {results}")
        return results

# Example usage functions for Mediflux integration
async def get_hospital_recommendations(user_location: str, specialty: str = None) -> List[Dict]:
    """Get hospital recommendations based on capacity and location"""
    client = SAEClient()
    
    # For French cities, extract department code (first 2 digits of postal code)
    dept_code = None
    if len(user_location) >= 2 and user_location[:2].isdigit():
        dept_code = user_location[:2]
    
    # Get hospitals with lower occupancy rates
    available_hospitals = await client.get_low_capacity_hospitals(max_occupancy=0.85)
    
    if dept_code:
        # Filter by department
        available_hospitals = [h for h in available_hospitals if h['department'] == dept_code]
    
    # Add routing recommendations
    for hospital in available_hospitals[:10]:  # Top 10 recommendations
        hospital['recommendation_reason'] = f"Lower occupancy ({hospital['occupancy_rate']:.1%}) - faster access likely"
        hospital['beds_available_estimate'] = int(hospital['beds'] * (1 - hospital['occupancy_rate'])) if hospital['occupancy_rate'] else "Unknown"
    
    return available_hospitals[:10]
