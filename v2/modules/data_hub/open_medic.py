"""
Open Medic Data Client for V2 Mediflux
Processes CSV data for medication reimbursement trends and statistics
Provides historical reimbursement patterns for cost estimation
"""

import asyncio
import csv
import os
from typing import Dict, List, Any, Optional
import logging
import sqlite3
from datetime import datetime


class OpenMedicClient:
    """
    Client for Open Medic dataset (French medication reimbursement data)
    Processes CSV files and provides statistical analysis for cost estimation
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to v2/data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data")
        
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "open_medic.db")
        self.logger = logging.getLogger(__name__)
        self._ensure_data_directory()
        self._init_database()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database for Open Medic data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS medication_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    medication_name TEXT NOT NULL,
                    substance_name TEXT,
                    age_group TEXT,
                    region TEXT,
                    avg_reimbursement_rate REAL,
                    total_prescriptions INTEGER,
                    total_cost_euros REAL,
                    avg_cost_per_prescription REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS regional_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    region TEXT NOT NULL,
                    category TEXT NOT NULL,
                    avg_reimbursement_rate REAL,
                    total_prescriptions INTEGER,
                    cost_per_capita REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    async def load_csv_data(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Load and process Open Medic CSV data
        
        Args:
            csv_file_path: Path to the Open Medic CSV file
            
        Returns:
            Processing results and statistics
        """
        try:
            if not os.path.exists(csv_file_path):
                return {
                    "success": False,
                    "error": "CSV file not found"
                }
            
            # Process CSV in thread to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._process_csv_file, csv_file_path
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"CSV loading failed: {str(e)}")
            return {
                "success": False,
                "error": f"CSV processing failed: {str(e)}"
            }
    
    def _process_csv_file(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Process CSV file and store in database
        """
        processed_rows = 0
        skipped_rows = 0
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                # Detect CSV dialect
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                
                reader = csv.DictReader(csvfile, dialect=dialect)
                
                with sqlite3.connect(self.db_path) as conn:
                    for row in reader:
                        try:
                            # Process row based on expected Open Medic CSV structure
                            processed_row = self._process_csv_row(row)
                            if processed_row:
                                self._insert_medication_stat(conn, processed_row)
                                processed_rows += 1
                            else:
                                skipped_rows += 1
                        except Exception as e:
                            self.logger.warning(f"Skipped row due to error: {str(e)}")
                            skipped_rows += 1
                    
                    conn.commit()
            
            return {
                "success": True,
                "processed_rows": processed_rows,
                "skipped_rows": skipped_rows,
                "total_rows": processed_rows + skipped_rows
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSV processing error: {str(e)}"
            }
    
    def _process_csv_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Process a single CSV row into standardized format
        """
        try:
            # Expected Open Medic CSV columns (may vary by year)
            # This would need to be adapted based on actual CSV structure
            
            # Example mapping - adjust based on real Open Medic CSV format
            medication_name = row.get('nom_court', row.get('medication_name', ''))
            substance_name = row.get('substance', row.get('active_substance', ''))
            
            # Parse numeric values
            reimbursement_rate = self._safe_float(row.get('taux_remb', '0'))
            prescriptions = self._safe_int(row.get('nb_prescriptions', '0'))
            total_cost = self._safe_float(row.get('cout_total', '0'))
            
            if not medication_name or prescriptions == 0:
                return None
            
            return {
                "year": 2023,  # Would extract from filename or data
                "medication_name": medication_name,
                "substance_name": substance_name,
                "age_group": row.get('age_group', 'all'),
                "region": row.get('region', 'national'),
                "avg_reimbursement_rate": reimbursement_rate / 100 if reimbursement_rate > 1 else reimbursement_rate,
                "total_prescriptions": prescriptions,
                "total_cost_euros": total_cost,
                "avg_cost_per_prescription": total_cost / prescriptions if prescriptions > 0 else 0
            }
            
        except Exception as e:
            self.logger.warning(f"Row processing error: {str(e)}")
            return None
    
    def _safe_float(self, value: str) -> float:
        """Safely convert string to float"""
        try:
            return float(value.replace(',', '.').replace(' ', ''))
        except (ValueError, AttributeError):
            return 0.0
    
    def _safe_int(self, value: str) -> int:
        """Safely convert string to int"""
        try:
            return int(float(value.replace(',', '.').replace(' ', '')))
        except (ValueError, AttributeError):
            return 0
    
    def _insert_medication_stat(self, conn: sqlite3.Connection, data: Dict[str, Any]):
        """Insert medication statistics into database"""
        conn.execute("""
            INSERT INTO medication_stats 
            (year, medication_name, substance_name, age_group, region, 
             avg_reimbursement_rate, total_prescriptions, total_cost_euros, avg_cost_per_prescription)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["year"],
            data["medication_name"],
            data["substance_name"],
            data["age_group"],
            data["region"],
            data["avg_reimbursement_rate"],
            data["total_prescriptions"],
            data["total_cost_euros"],
            data["avg_cost_per_prescription"]
        ))
    
    async def get_medication_trends(self, medication_name: str) -> Dict[str, Any]:
        """
        Get historical reimbursement trends for a medication
        
        Args:
            medication_name: Name of the medication
            
        Returns:
            Historical trends and statistics
        """
        try:
            def _query_trends():
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # Get medication statistics
                    cursor = conn.execute("""
                        SELECT year, region, avg_reimbursement_rate, 
                               total_prescriptions, avg_cost_per_prescription
                        FROM medication_stats
                        WHERE medication_name LIKE ? OR substance_name LIKE ?
                        ORDER BY year DESC, total_prescriptions DESC
                    """, (f"%{medication_name}%", f"%{medication_name}%"))
                    
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            
            results = await asyncio.get_event_loop().run_in_executor(None, _query_trends)
            
            if not results:
                return {
                    "success": False,
                    "error": "No historical data found for this medication"
                }
            
            # Analyze trends
            analysis = self._analyze_medication_trends(results, medication_name)
            
            return {
                "success": True,
                "medication_name": medication_name,
                "historical_data": results[:10],  # Latest 10 entries
                "trend_analysis": analysis,
                "data_points": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Trend analysis failed: {str(e)}"
            }
    
    def _analyze_medication_trends(self, data: List[Dict], medication_name: str) -> Dict[str, Any]:
        """
        Analyze medication trends from historical data
        """
        if not data:
            return {"error": "No data to analyze"}
        
        # Calculate averages
        avg_reimbursement = sum(row["avg_reimbursement_rate"] for row in data if row["avg_reimbursement_rate"]) / len(data)
        avg_cost = sum(row["avg_cost_per_prescription"] for row in data if row["avg_cost_per_prescription"]) / len(data)
        
        # Regional variation
        regional_data = {}
        for row in data:
            region = row["region"]
            if region not in regional_data:
                regional_data[region] = []
            regional_data[region].append(row["avg_reimbursement_rate"])
        
        regional_averages = {
            region: sum(rates) / len(rates) 
            for region, rates in regional_data.items() 
            if rates
        }
        
        return {
            "average_reimbursement_rate": round(avg_reimbursement, 3),
            "average_cost_per_prescription": round(avg_cost, 2),
            "regional_variations": regional_averages,
            "best_reimbursement_regions": sorted(
                regional_averages.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3],
            "data_years": list(set(row["year"] for row in data)),
            "cost_trend": "stable"  # Would calculate actual trend
        }
    
    async def get_regional_statistics(self, region: str) -> Dict[str, Any]:
        """
        Get regional medication reimbursement statistics
        """
        try:
            def _query_regional():
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    cursor = conn.execute("""
                        SELECT medication_name, avg_reimbursement_rate, 
                               total_prescriptions, avg_cost_per_prescription
                        FROM medication_stats
                        WHERE region = ? OR region = 'national'
                        ORDER BY total_prescriptions DESC
                        LIMIT 50
                    """, (region,))
                    
                    return [dict(row) for row in cursor.fetchall()]
            
            results = await asyncio.get_event_loop().run_in_executor(None, _query_regional)
            
            if not results:
                return {
                    "success": False,
                    "error": f"No data found for region: {region}"
                }
            
            # Calculate regional statistics
            total_prescriptions = sum(row["total_prescriptions"] for row in results)
            avg_reimbursement = sum(row["avg_reimbursement_rate"] for row in results) / len(results)
            
            top_medications = sorted(
                results, 
                key=lambda x: x["total_prescriptions"], 
                reverse=True
            )[:10]
            
            return {
                "success": True,
                "region": region,
                "total_prescriptions": total_prescriptions,
                "average_reimbursement_rate": round(avg_reimbursement, 3),
                "top_medications": top_medications,
                "medication_count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Regional statistics query failed: {str(e)}"
            }
    
    async def search_similar_medications(self, medication_name: str, substance_name: str = None) -> Dict[str, Any]:
        """
        Find medications with similar reimbursement patterns
        """
        try:
            def _search_similar():
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    if substance_name:
                        # Search by substance
                        cursor = conn.execute("""
                            SELECT medication_name, substance_name, avg_reimbursement_rate, 
                                   avg_cost_per_prescription, total_prescriptions
                            FROM medication_stats
                            WHERE substance_name LIKE ?
                            ORDER BY total_prescriptions DESC
                            LIMIT 20
                        """, (f"%{substance_name}%",))
                    else:
                        # Search by similar names
                        cursor = conn.execute("""
                            SELECT medication_name, substance_name, avg_reimbursement_rate, 
                                   avg_cost_per_prescription, total_prescriptions
                            FROM medication_stats
                            WHERE medication_name LIKE ?
                            ORDER BY total_prescriptions DESC
                            LIMIT 20
                        """, (f"%{medication_name}%",))
                    
                    return [dict(row) for row in cursor.fetchall()]
            
            results = await asyncio.get_event_loop().run_in_executor(None, _search_similar)
            
            return {
                "success": True,
                "search_term": medication_name,
                "substance_filter": substance_name,
                "similar_medications": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Similar medication search failed: {str(e)}"
            }
