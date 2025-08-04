"""
DREES Demographics Data Integration
Processes French healthcare professional density statistics for regional analysis
"""

import pandas as pd
import sqlite3
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class DREESClient:
    """Client for processing DREES healthcare professional demographics data"""
    
    def __init__(self, db_path: str = "data/mediflux.db"):
        self.db_path = db_path
        self.data_dir = Path("data/drees")
        self.base_url = "https://data.drees.solidarites-sante.gouv.fr/api/v2/catalog/datasets/la-demographie-des-professionnels-de-sante-depuis-2012/attachments/"
        
        # Key professional categories and their file mappings (from real API)
        self.professional_files = {
            'medecins': 'medecins_rpps_2012_2025_xlsx',
            'infirmieres_liberales': 'infirmieres_liberales_snds_2012_2023_xlsx', 
            'infirmieres_salariees': 'infirmieres_salariees_bts_2013_2021_xlsx',
            'kinesitherapeutes': 'kinesitherapeutes_rpps_2017_2024_xlsx',
            'chirurgiens_dentistes': 'chirurgiens_dentistes_rpps_2012_2025_xlsx',
            'pharmaciens': 'pharmaciens_rpps_2012_2025_xlsx',
            'sages_femmes': 'sages_femmes_rpps_2012_2025_xlsx'
        }
        
    async def initialize_database(self):
        """Initialize DREES demographics tables in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Professional density by territory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drees_professional_density (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profession TEXT,          -- e.g., 'medecins_generalistes'
                year INTEGER,            -- 2023, 2022, etc.
                territoire_code TEXT,    -- Department or region code
                territoire_nom TEXT,     -- Territory name  
                effectif INTEGER,        -- Number of professionals
                densite_100k REAL,       -- Density per 100k inhabitants
                population INTEGER,       -- Territory population
                density_category TEXT,   -- HIGH/MEDIUM/LOW relative density
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Regional professional availability index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drees_regional_availability (
                territoire_code TEXT PRIMARY KEY,
                territoire_nom TEXT,
                total_generalistes INTEGER,
                total_specialistes INTEGER, 
                total_infirmieres INTEGER,
                total_pharmaciens INTEGER,
                generaliste_density REAL,
                specialiste_density REAL,
                availability_score REAL,     -- Composite availability score
                shortage_risk TEXT,          -- HIGH/MEDIUM/LOW shortage risk
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Specialty-specific density for pathway optimization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drees_specialty_density (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                specialty TEXT,           -- e.g., 'cardiologie', 'pneumologie'
                territoire_code TEXT,
                territoire_nom TEXT,
                effectif INTEGER,
                densite_100k REAL,
                wait_time_estimate TEXT,  -- QUICK/MODERATE/LONG based on density
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("DREES demographics database tables initialized")
    
    async def download_professional_data(self, profession: str) -> Path:
        """Download specific professional demographics file"""
        if profession not in self.professional_files:
            raise ValueError(f"Unknown profession: {profession}")
            
        filename = self.professional_files[profession]
        file_path = self.data_dir / f"{profession}.xlsx"
        
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            return file_path
            
        # Download file
        url = urljoin(self.base_url, filename)
        logger.info(f"Downloading {profession} data from {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Downloaded {profession} data to {file_path}")
        return file_path
    
    def _process_excel_demographics(self, file_path: Path, profession: str) -> List[Dict]:
        """Process Excel file containing professional demographics by territory"""
        try:
            # Read Excel file - DREES files typically have data starting from row 2
            df = pd.read_excel(file_path, sheet_name=0, skiprows=1)
            
            # Standardize column names (DREES uses French column names)
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('é', 'e').str.replace('è', 'e')
            
            logger.info(f"Loaded {len(df)} records for {profession}")
            logger.info(f"Columns: {list(df.columns)[:10]}")  # Show first 10 columns
            
            records = []
            
            # Find the most recent year data (usually 2023 or 2022)
            year_columns = [col for col in df.columns if col.isdigit() and int(col) >= 2020]
            latest_year = max(year_columns) if year_columns else None
            
            if not latest_year:
                logger.warning(f"No recent year data found in {profession} file")
                return records
            
            for _, row in df.iterrows():
                # Territory identification - try different column name patterns
                territoire_code = None
                territoire_nom = None
                
                for col in ['code', 'dept', 'departement', 'territoire']:
                    if col in df.columns and pd.notna(row.get(col)):
                        territoire_code = str(row[col]).strip()
                        break
                        
                for col in ['nom', 'libelle', 'denomination', 'territoire_nom']:
                    if col in df.columns and pd.notna(row.get(col)):
                        territoire_nom = str(row[col]).strip()
                        break
                
                if not territoire_code or not territoire_nom:
                    continue
                
                # Get professional count for latest year
                effectif = None
                densite_100k = None
                
                if latest_year in df.columns:
                    effectif = self._safe_int(row.get(latest_year))
                
                # Look for density column (densité pour 100k habitants)
                density_col = f"densite_{latest_year}"
                for col in df.columns:
                    if 'densite' in col.lower() and latest_year in col:
                        densite_100k = self._safe_float(row.get(col))
                        break
                
                if effectif is None:
                    continue
                
                # Estimate population if we have density
                population = None
                if densite_100k and densite_100k > 0:
                    population = int((effectif * 100000) / densite_100k)
                
                # Categorize density
                density_category = self._categorize_density(densite_100k, profession)
                
                record = {
                    'profession': profession,
                    'year': int(latest_year),
                    'territoire_code': territoire_code,
                    'territoire_nom': territoire_nom,
                    'effectif': effectif,
                    'densite_100k': densite_100k,
                    'population': population,
                    'density_category': density_category
                }
                records.append(record)
            
            logger.info(f"Processed {len(records)} records for {profession}")
            return records
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def _categorize_density(self, density: Optional[float], profession: str) -> str:
        """Categorize professional density as HIGH/MEDIUM/LOW"""
        if density is None:
            return "UNKNOWN"
        
        # Density thresholds vary by profession (per 100k inhabitants)
        thresholds = {
            'medecins': {'high': 150, 'medium': 100},
            'infirmieres_liberales': {'high': 150, 'medium': 100},
            'infirmieres_salariees': {'high': 600, 'medium': 400},
            'pharmaciens': {'high': 35, 'medium': 25},
            'kinesitherapeutes': {'high': 120, 'medium': 80},
            'chirurgiens_dentistes': {'high': 70, 'medium': 50},
            'sages_femmes': {'high': 70, 'medium': 50}
        }
        
        prof_thresholds = thresholds.get(profession, {'high': 100, 'medium': 60})
        
        if density >= prof_thresholds['high']:
            return "HIGH"
        elif density >= prof_thresholds['medium']:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if pd.isna(value):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def process_professional_demographics(self, profession: str) -> int:
        """Process demographics data for a specific profession"""
        file_path = await self.download_professional_data(profession)
        records = self._process_excel_demographics(file_path, profession)
        
        if not records:
            return 0
        
        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data for this profession
        cursor.execute("DELETE FROM drees_professional_density WHERE profession = ?", (profession,))
        
        # Insert new records
        for record in records:
            cursor.execute("""
                INSERT INTO drees_professional_density 
                (profession, year, territoire_code, territoire_nom, effectif, densite_100k, population, density_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['profession'], record['year'], record['territoire_code'], record['territoire_nom'],
                record['effectif'], record['densite_100k'], record['population'], record['density_category']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Inserted {len(records)} records for {profession}")
        return len(records)
    
    async def calculate_regional_availability(self) -> int:
        """Calculate composite regional healthcare availability scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest data by territory
        cursor.execute("""
            SELECT 
                territoire_code,
                territoire_nom,
                SUM(CASE WHEN profession = 'medecins' THEN effectif ELSE 0 END) as generalistes,
                0 as specialistes,
                SUM(CASE WHEN profession = 'infirmieres_liberales' THEN effectif ELSE 0 END) as infirmieres,
                SUM(CASE WHEN profession = 'pharmaciens' THEN effectif ELSE 0 END) as pharmaciens,
                AVG(CASE WHEN profession = 'medecins' THEN densite_100k END) as gen_density,
                0 as spec_density,
                AVG(population) as avg_population
            FROM drees_professional_density
            WHERE year = (SELECT MAX(year) FROM drees_professional_density)
            GROUP BY territoire_code, territoire_nom
            HAVING generalistes > 0 OR infirmieres > 0
        """)
        
        regional_data = cursor.fetchall()
        
        # Clear existing availability data
        cursor.execute("DELETE FROM drees_regional_availability")
        
        # Calculate availability scores
        for row in regional_data:
            (territoire_code, territoire_nom, generalistes, specialistes, infirmieres, 
             pharmaciens, gen_density, spec_density, avg_population) = row
            
            # Calculate composite availability score (0-100)
            # Weight: 40% general practitioners, 35% specialists, 15% nurses, 10% pharmacists
            availability_score = 0
            
            if gen_density:
                availability_score += min(gen_density / 100, 1.0) * 40
            if spec_density:
                availability_score += min(spec_density / 60, 1.0) * 35
            if infirmieres and avg_population:
                nurse_density = (infirmieres * 100000) / avg_population
                availability_score += min(nurse_density / 700, 1.0) * 15
            if pharmaciens and avg_population:
                pharm_density = (pharmaciens * 100000) / avg_population
                availability_score += min(pharm_density / 30, 1.0) * 10
            
            # Determine shortage risk
            shortage_risk = "LOW"
            if availability_score < 30:
                shortage_risk = "HIGH"
            elif availability_score < 60:
                shortage_risk = "MEDIUM"
            
            cursor.execute("""
                INSERT INTO drees_regional_availability 
                (territoire_code, territoire_nom, total_generalistes, total_specialistes, 
                 total_infirmieres, total_pharmaciens, generaliste_density, specialiste_density,
                 availability_score, shortage_risk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                territoire_code, territoire_nom, generalistes, specialistes,
                infirmieres, pharmaciens, gen_density, spec_density,
                round(availability_score, 1), shortage_risk
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Calculated availability for {len(regional_data)} territories")
        return len(regional_data)
    
    async def get_professional_density_by_region(self, territoire_code: str = None, profession: str = None) -> List[Dict]:
        """Get professional density information by region"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT profession, territoire_code, territoire_nom, effectif, densite_100k, density_category
            FROM drees_professional_density
            WHERE year = (SELECT MAX(year) FROM drees_professional_density)
        """
        params = []
        
        if territoire_code:
            query += " AND territoire_code = ?"
            params.append(territoire_code)
            
        if profession:
            query += " AND profession = ?"
            params.append(profession)
        
        query += " ORDER BY densite_100k DESC NULLS LAST"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        densities = []
        for row in results:
            density = {
                'profession': row[0],
                'territory_code': row[1],
                'territory_name': row[2],
                'professional_count': row[3],
                'density_per_100k': row[4],
                'density_category': row[5]
            }
            densities.append(density)
        
        return densities
    
    async def get_low_density_areas(self, profession: str = 'medecins', max_density: float = None) -> List[Dict]:
        """Find areas with low professional density for shortage analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT territoire_code, territoire_nom, effectif, densite_100k, density_category
            FROM drees_professional_density
            WHERE profession = ?
            AND year = (SELECT MAX(year) FROM drees_professional_density WHERE profession = ?)
            AND density_category IN ('LOW', 'MEDIUM')
        """
        params = [profession, profession]
        
        if max_density:
            query += " AND densite_100k <= ?"
            params.append(max_density)
        
        query += " ORDER BY densite_100k ASC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        low_density_areas = []
        for row in results:
            area = {
                'territory_code': row[0],
                'territory_name': row[1],
                'professional_count': row[2],
                'density_per_100k': row[3],
                'density_category': row[4],
                'shortage_severity': 'HIGH' if row[3] and row[3] < 50 else 'MODERATE'
            }
            low_density_areas.append(area)
        
        return low_density_areas
    
    async def process_key_professions(self) -> Dict[str, int]:
        """Process the most important professions for Mediflux MVP"""
        key_professions = [
            'medecins',
            'infirmieres_liberales', 
            'pharmaciens'
        ]
        
        await self.initialize_database()
        results = {}
        
        for profession in key_professions:
            try:
                count = await self.process_professional_demographics(profession)
                results[profession] = count
            except Exception as e:
                logger.error(f"Failed to process {profession}: {e}")
                results[profession] = 0
        
        # Calculate regional availability after processing all professions
        availability_count = await self.calculate_regional_availability()
        results['regional_availability'] = availability_count
        
        logger.info(f"DREES processing complete: {results}")
        return results

# Example usage functions for Mediflux integration
async def get_specialist_availability(specialty: str, user_location: str) -> List[Dict]:
    """Get specialist availability based on location"""
    client = DREESClient()
    
    # Extract department code from location (first 2 digits)
    dept_code = user_location[:2] if len(user_location) >= 2 and user_location[:2].isdigit() else None
    
    if specialty.lower() in ['cardiology', 'cardiologue', 'general', 'generaliste']:
        profession = 'medecins'
    elif specialty.lower() in ['nurse', 'infirmiere']:
        profession = 'infirmieres_liberales'
    else:
        profession = 'medecins'  # Default to doctors
    
    # Get density data
    densities = await client.get_professional_density_by_region(
        territoire_code=dept_code, 
        profession=profession
    )
    
    # Add routing recommendations
    for density in densities:
        if density['density_category'] == 'HIGH':
            density['wait_estimate'] = 'Short wait expected (high density)'
            density['recommendation'] = 'Good availability in your area'
        elif density['density_category'] == 'MEDIUM':
            density['wait_estimate'] = 'Moderate wait expected'
            density['recommendation'] = 'Consider nearby areas for faster access'
        else:
            density['wait_estimate'] = 'Longer wait expected (low density)'
            density['recommendation'] = 'Consider telemedicine or travel to higher-density areas'
    
    return densities
