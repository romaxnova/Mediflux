"""
Open Medic CSV Data Processor
Handles French medication reimbursement data from data.gouv.fr
Processes and stores medication expenditure statistics
"""

import asyncio
import aiohttp
import pandas as pd
import os
import hashlib
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import sqlite3


class OpenMedicProcessor:
    """
    Processor for Open Medic CSV data
    Downloads, processes, and stores French medication reimbursement data
    """
    
    def __init__(self, data_dir: str = "data/openmedic"):
        self.data_dir = data_dir
        self.base_url = "https://www.data.gouv.fr/api/1/datasets/r"
        self.logger = logging.getLogger(__name__)
        
        # Direct download URLs (discovered working URLs)
        self.download_urls = {
            "2024": "https://open-data-assurance-maladie.ameli.fr/medicaments/download_file.php?token=f11a2e714ddad5f93eea56de8410c181&file=Open_MEDIC_Base_Complete/OPEN_MEDIC_2024.zip"
        }
        
        # Fallback resource IDs from data.gouv.fr  
        self.csv_resources = {
            "2023": "58243d8c-2c83-49ee-b9e9-306c0096d1aa",  
            "2022": "3fa6410b-3a71-4bf0-84ef-61968f7cfe82",
            "2021": "288ab5f9-db9e-4597-afcd-840e043cc075"
        }
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize local database
        self.db_path = os.path.join(self.data_dir, "openmedic_data.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for processed data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS medication_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER,
                    atc1 TEXT,
                    l_atc1 TEXT,
                    atc5 TEXT,
                    l_atc5 TEXT,
                    cip13 TEXT,
                    l_cip13 TEXT,
                    age_group TEXT,
                    sexe TEXT,
                    ben_reg TEXT,
                    psp_spe TEXT,
                    boites INTEGER,
                    montant_rembourse REAL,
                    montant_base REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cip13 ON medication_data (cip13)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_atc1 ON medication_data (atc1)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_atc5 ON medication_data (atc5)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_product_name ON medication_data (l_cip13)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON medication_data (year)")
    
    async def download_openmedic_data(self, year: str = "2024") -> Dict[str, Any]:
        """Download OpenMedic data for specified year (ZIP or CSV)"""
        
        # Try direct download URL first
        if year in self.download_urls:
            download_url = self.download_urls[year]
            file_path = os.path.join(self.data_dir, f"OPEN_MEDIC_{year}.zip")
            is_zip = True
        elif year in self.csv_resources:
            resource_id = self.csv_resources[year]
            download_url = f"{self.base_url}/{resource_id}"
            file_path = os.path.join(self.data_dir, f"openmedic_{year}.csv")
            is_zip = False
        else:
            return {"success": False, "error": f"Year {year} not available"}
        
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for large CSV
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        file_size = os.path.getsize(file_path)
                        return {
                            "success": True,
                            "file_path": file_path,
                            "file_size_mb": round(file_size / (1024*1024), 2),
                            "year": year
                        }
                    else:
                        return {"success": False, "error": f"Download failed: HTTP {response.status}"}
                        
        except Exception as e:
            return {"success": False, "error": f"Download error: {str(e)}"}
    
    def process_csv_file(self, file_path: str, year: str, sample_size: int = 10000) -> Dict[str, Any]:
        """Process CSV file and extract key data"""
        try:
            # Read CSV with appropriate encoding and parsing
            df = pd.read_csv(file_path, 
                           encoding='utf-8', 
                           sep=';',  # French CSV format
                           low_memory=False,
                           nrows=sample_size if sample_size else None)
            
            # Basic data validation
            if df.empty:
                return {"success": False, "error": "Empty CSV file"}
            
            # Standardize column names (handle variations)
            column_mapping = self._get_column_mapping(df.columns.tolist())
            if not column_mapping:
                return {"success": False, "error": "Unable to identify required columns"}
            
            df = df.rename(columns=column_mapping)
            
            # Basic data processing
            processed_data = self._process_dataframe(df, year)
            
            return {
                "success": True,
                "year": year,
                "total_rows": len(df),
                "processed_records": len(processed_data),
                "sample_data": processed_data[:5],  # First 5 records
                "columns": list(df.columns),
                "file_path": file_path
            }
            
        except Exception as e:
            return {"success": False, "error": f"CSV processing error: {str(e)}"}
    
    def _get_column_mapping(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """Map CSV columns to standardized names"""
        # Real OpenMedic column structure (case-sensitive)
        expected_columns = [
            'ATC1', 'l_ATC1', 'ATC2', 'L_ATC2', 'ATC3', 'L_ATC3', 
            'ATC4', 'L_ATC4', 'ATC5', 'L_ATC5', 'CIP13', 'l_cip13',
            'TOP_GEN', 'GEN_NUM', 'age', 'sexe', 'BEN_REG', 'PSP_SPE',
            'BOITES', 'REM', 'BSE'
        ]
        
        # Check if we have the standard OpenMedic format
        if all(col in columns for col in ['ATC1', 'CIP13', 'l_cip13', 'BOITES', 'REM']):
            return {
                'ATC1': 'atc1',
                'l_ATC1': 'l_atc1', 
                'ATC5': 'atc5',
                'L_ATC5': 'l_atc5',
                'CIP13': 'cip13',
                'l_cip13': 'l_cip13',
                'age': 'age_group',
                'sexe': 'sexe',
                'BEN_REG': 'ben_reg',
                'PSP_SPE': 'psp_spe',
                'BOITES': 'boites',
                'REM': 'montant_rembourse',
                'BSE': 'montant_base'
            }
        
        # Fallback to pattern matching for other formats
        mapping_patterns = {
            'atc1': ['ATC1', 'code_atc', 'atc'],
            'l_cip13': ['l_cip13', 'l_medicament', 'medicament', 'denomination'],
            'boites': ['BOITES', 'nb_boites', 'nombre_boites', 'quantite'],
            'montant_rembourse': ['REM', 'mnt_remb_am', 'montant_rembourse'],
            'ben_reg': ['BEN_REG', 'reg', 'region'],
            'age_group': ['age', 'age_group', 'classe_age'],
            'sexe': ['sexe', 'genre', 'sex']
        }
        
        mapping = {}
        for standard_name, patterns in mapping_patterns.items():
            for pattern in patterns:
                for col in columns:
                    if pattern == col or pattern.lower() in col.lower():
                        mapping[col] = standard_name
                        break
                if standard_name in mapping.values():
                    break
        
        return mapping if len(mapping) >= 4 else None  # Need at least 4 key columns
    
    def _parse_french_float(self, value) -> float:
        """Parse French decimal format (comma as decimal separator)"""
        if pd.isna(value):
            return 0.0
        try:
            # Convert comma decimal separator to dot
            str_val = str(value).replace(',', '.')
            return float(str_val)
        except (ValueError, TypeError):
            return 0.0
    
    def _process_dataframe(self, df: pd.DataFrame, year: str) -> List[Dict[str, Any]]:
        """Process dataframe into standardized format"""
        processed = []
        
        for _, row in df.iterrows():
            try:
                record = {
                    "year": int(year),
                    "atc1": str(row['atc1']) if 'atc1' in row and pd.notna(row['atc1']) else '',
                    "l_atc1": str(row['l_atc1']) if 'l_atc1' in row and pd.notna(row['l_atc1']) else '',
                    "atc5": str(row['atc5']) if 'atc5' in row and pd.notna(row['atc5']) else '',
                    "l_atc5": str(row['l_atc5']) if 'l_atc5' in row and pd.notna(row['l_atc5']) else '',
                    "cip13": str(row['cip13']) if 'cip13' in row and pd.notna(row['cip13']) else '',
                    "l_cip13": str(row['l_cip13']) if 'l_cip13' in row and pd.notna(row['l_cip13']) else '',
                    "age_group": str(row['age_group']) if 'age_group' in row and pd.notna(row['age_group']) else '',
                    "sexe": str(row['sexe']) if 'sexe' in row and pd.notna(row['sexe']) else '',
                    "ben_reg": str(row['ben_reg']) if 'ben_reg' in row and pd.notna(row['ben_reg']) else '',
                    "psp_spe": str(row['psp_spe']) if 'psp_spe' in row and pd.notna(row['psp_spe']) else '',
                    "boites": int(row['boites']) if 'boites' in row and pd.notna(row['boites']) else 0,
                    "montant_rembourse": self._parse_french_float(row['montant_rembourse']) if 'montant_rembourse' in row else 0.0,
                    "montant_base": self._parse_french_float(row['montant_base']) if 'montant_base' in row else 0.0
                }
                
                # Only include records with essential data
                if record["l_cip13"] and record["boites"] > 0:
                    processed.append(record)
                    
            except (ValueError, TypeError) as e:
                continue  # Skip problematic rows
        
        return processed
    
    def store_processed_data(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store processed data in local database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for record in processed_data:
                    conn.execute("""
                        INSERT INTO medication_data 
                        (year, atc1, l_atc1, atc5, l_atc5, cip13, l_cip13, age_group, sexe, 
                         ben_reg, psp_spe, boites, montant_rembourse, montant_base)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record["year"], record["atc1"], record["l_atc1"], record["atc5"], record["l_atc5"],
                        record["cip13"], record["l_cip13"], record["age_group"], record["sexe"],
                        record["ben_reg"], record["psp_spe"], record["boites"], 
                        record["montant_rembourse"], record["montant_base"]
                    ))
                
                conn.commit()
                
            return {
                "success": True,
                "records_stored": len(processed_data),
                "database_path": self.db_path
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database storage error: {str(e)}"}
    
    def search_medication_costs(self, medication_name: str, limit: int = 10) -> Dict[str, Any]:
        """Search for medication cost data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT medicament, code_atc, nb_boites, montant_rembourse, region, year
                    FROM medication_data 
                    WHERE medicament LIKE ? 
                    ORDER BY montant_rembourse DESC
                    LIMIT ?
                """, (f"%{medication_name}%", limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "medicament": row[0],
                        "code_atc": row[1],
                        "nb_boites": row[2],
                        "montant_rembourse": row[3],
                        "region": row[4],
                        "year": row[5]
                    })
                
                return {
                    "success": True,
                    "query": medication_name,
                    "results": results,
                    "total_found": len(results)
                }
                
        except Exception as e:
            return {"success": False, "error": f"Search error: {str(e)}"}
    
    async def update_data(self, year: str = "2023", sample_size: int = 10000) -> Dict[str, Any]:
        """Complete data update workflow"""
        try:
            # Download latest CSV
            download_result = await self.download_csv_data(year)
            if not download_result["success"]:
                return download_result
            
            # Process CSV
            process_result = self.process_csv_file(
                download_result["file_path"], 
                year, 
                sample_size
            )
            if not process_result["success"]:
                return process_result
            
            # Store in database
            store_result = self.store_processed_data(process_result["sample_data"])
            if not store_result["success"]:
                return store_result
            
            return {
                "success": True,
                "year": year,
                "download_size_mb": download_result["file_size_mb"],
                "processed_records": process_result["processed_records"],
                "stored_records": store_result["records_stored"],
                "database_path": self.db_path
            }
            
        except Exception as e:
            return {"success": False, "error": f"Update workflow error: {str(e)}"}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM medication_data")
                total_records = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT DISTINCT year FROM medication_data ORDER BY year")
                years = [row[0] for row in cursor.fetchall()]
                
                cursor = conn.execute("SELECT COUNT(DISTINCT medicament) FROM medication_data")
                unique_medications = cursor.fetchone()[0]
                
                return {
                    "total_records": total_records,
                    "years_available": years,
                    "unique_medications": unique_medications,
                    "database_path": self.db_path
                }
                
        except Exception as e:
            return {"error": f"Stats error: {str(e)}"}
