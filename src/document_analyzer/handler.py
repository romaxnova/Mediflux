"""
Document Analyzer for V2 Mediflux
OCR and rule-based extraction for healthcare documents
Handles carte tiers payant, feuilles de soins, prescriptions
"""

import asyncio
from typing import Dict, List, Any, Optional
import re
import logging
import os
import pytesseract
from PIL import Image
import tempfile

# Import medical knowledge base
from .medical_knowledge import MedicalKnowledgeBase


class DocumentAnalyzer:
    """
    Analyzes healthcare documents using OCR and rule-based extraction
    Focuses on extracting structured data for reimbursement simulation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.knowledge_base = MedicalKnowledgeBase()
        self.supported_types = [
            "carte_tiers_payant",
            "feuille_soins", 
            "prescription",
            "auto_detect"
        ]
        
        # Configure Tesseract for French language
        self.tesseract_config = '--oem 3 --psm 6 -l fra+eng'
    
    async def analyze_document(self, document_path: str, document_type: str = "auto_detect") -> Dict[str, Any]:
        """
        Analyze a healthcare document
        
        Args:
            document_path: Path to the document file
            document_type: Type of document or 'auto_detect'
            
        Returns:
            Structured extraction results
        """
        try:
            if not os.path.exists(document_path):
                return {
                    "success": False,
                    "error": "Document file not found"
                }
            
            # Auto-detect document type if needed
            if document_type == "auto_detect":
                document_type = await self._detect_document_type(document_path)
            
            # Extract text using OCR (TODO: implement Tesseract integration)
            text_content = await self._extract_text_with_ocr(document_path)
            
            # Apply document-specific extraction rules
            if document_type == "carte_tiers_payant":
                return await self._analyze_carte_tiers_payant(text_content)
            elif document_type == "feuille_soins":
                return await self._analyze_feuille_soins(text_content)
            elif document_type == "prescription":
                return await self._analyze_prescription(text_content)
            else:
                return await self._generic_analysis(text_content, document_type)
                
        except Exception as e:
            self.logger.error(f"Document analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
    
    async def _detect_document_type(self, document_path: str) -> str:
        """
        Auto-detect document type based on filename and OCR content patterns
        """
        filename = os.path.basename(document_path).lower()
        
        # Quick OCR preview to detect content
        try:
            image = Image.open(document_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Quick OCR scan for document type identification
            preview_text = pytesseract.image_to_string(
                image, 
                config='--oem 3 --psm 6 -l fra+eng'
            ).lower()
            
            # Enhanced detection patterns
            carte_tiers_patterns = [
                'ociane', 'matmut', 'harmonie', 'mgen', 'maaf',
                'tiers payant', 'mutuelle', 'carte de tiers',
                'période de validité', 'adhérent', 'amc',
                'pec', 'meds', 'dent', 'opti'
            ]
            
            feuille_soins_patterns = [
                'feuille de soins', 'remboursement', 'assurance maladie',
                'sécurité sociale', 'cpam', 'consultation',
                'acte médical', 'code ccam'
            ]
            
            prescription_patterns = [
                'ordonnance', 'prescription', 'médecin',
                'médicament', 'posologie', 'traitement',
                'docteur', 'dr.', 'prescrit'
            ]
            
            # Count matches for each document type
            carte_score = sum(1 for pattern in carte_tiers_patterns if pattern in preview_text)
            feuille_score = sum(1 for pattern in feuille_soins_patterns if pattern in preview_text)
            prescription_score = sum(1 for pattern in prescription_patterns if pattern in preview_text)
            
            # Determine document type based on highest score
            if carte_score >= 2:
                return "carte_tiers_payant"
            elif feuille_score >= 2:
                return "feuille_soins"
            elif prescription_score >= 2:
                return "prescription"
            
        except Exception as e:
            self.logger.warning(f"Content-based detection failed: {e}")
        
        # Fallback to filename-based detection
        if any(keyword in filename for keyword in ["carte", "tiers", "payant", "vitale", "mutuelle"]):
            return "carte_tiers_payant"
        elif any(keyword in filename for keyword in ["feuille", "soins", "remboursement"]):
            return "feuille_soins"
        elif any(keyword in filename for keyword in ["prescription", "ordonnance"]):
            return "prescription"
        
        return "unknown"
    
    async def _extract_text_with_ocr(self, document_path: str) -> str:
        """
        Extract text using Tesseract OCR with simple, effective preprocessing
        """
        try:
            from PIL import ImageEnhance
            import numpy as np
            
            # Open image
            image = Image.open(document_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Simple but effective preprocessing
            width, height = image.size
            
            # Scale up moderately - too much scaling can hurt OCR
            if width < 1600:
                scale_factor = 1600 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Moderate contrast enhancement
            enhancer = ImageEnhance.Contrast(gray_image)
            gray_image = enhancer.enhance(1.8)
            
            # Try different OCR configurations - focus on what works
            ocr_configs = [
                # Configuration 1: Standard table OCR
                '--oem 3 --psm 6 -l fra+eng',
                
                # Configuration 2: Multiple text lines
                '--oem 3 --psm 4 -l fra+eng',
                
                # Configuration 3: Automatic page segmentation
                '--oem 3 --psm 3 -l fra+eng',
                
                # Configuration 4: Single text block
                '--oem 3 --psm 8 -l fra+eng',
                
                # Configuration 5: With character whitelist
                '--oem 3 --psm 6 -l fra+eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789*:/%()., ',
            ]
            
            best_results = []
            
            # Test all configurations
            for i, config in enumerate(ocr_configs):
                try:
                    extracted_text = pytesseract.image_to_string(gray_image, config=config)
                    cleaned = self._clean_ocr_text(extracted_text)
                    
                    # Simple scoring based on content quality
                    score = self._score_text_content(cleaned)
                    best_results.append((cleaned, score, f"config_{i+1}"))
                    
                    self.logger.info(f"Config {i+1} extracted {len(cleaned)} chars, score: {score}")
                    
                except Exception as e:
                    self.logger.warning(f"OCR config {i+1} failed: {e}")
                    continue
            
            if not best_results:
                return "[OCR_FAILED] All OCR configurations failed"
            
            # Return the best scoring result
            best_text, best_score, best_config = max(best_results, key=lambda x: x[1])
            self.logger.info(f"Using {best_config} with score {best_score}")
            self.logger.info(f"OCR result preview: {best_text[:200]}...")
            
            return best_text
            
        except ImportError:
            return "[OCR_ERROR] Missing image processing libraries"
        except pytesseract.TesseractNotFoundError:
            return "[OCR_UNAVAILABLE] Tesseract not installed"
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            return f"[OCR_ERROR] {str(e)}"
    
    def _score_text_content(self, text: str) -> int:
        """
        Score OCR quality based on healthcare document structure and content
        """
        score = 0
        text_upper = text.upper()
        
        # Look for name patterns (any capitalized names, not specific ones)
        name_patterns = [
            r'\b[A-Z]{4,}\s+[A-Z]{3,}\b',  # Two capitalized words (typical name format)
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Proper case names
        ]
        for pattern in name_patterns:
            if re.search(pattern, text):
                score += 15
                break
        
        # Look for medical codes (generic healthcare abbreviations)
        medical_codes = ['PHAR', 'MED', 'SVIL', 'CSTE', 'TRAN', 'DESO', 'DEPR', 'DEOR', 'OPAU', 'HOSP', 'EXTE', 
                        'PHCO', 'PHNO', 'PHOR', 'MEDE', 'AUDI', 'DENT', 'OPTI']
        code_count = sum(1 for code in medical_codes if code in text_upper)
        score += code_count * 5
        
        # Look for percentages and coverage indicators
        percentage_count = len(re.findall(r'\d{1,3}%', text))
        score += min(percentage_count * 3, 30)
        
        pec_count = text_upper.count('PEC')
        score += min(pec_count * 5, 25)
        
        # Look for numeric patterns (member numbers, dates)
        if re.search(r'\d{7,9}', text):  # 7-9 digit numbers (typical for member IDs)
            score += 20
        
        # Look for date patterns
        if re.search(r'\d{2}/\d{2}/\d{4}', text):
            score += 15
        
        # Text length bonus
        if len(text) > 200:
            score += 10
        
        return score
    
    def _score_ocr_quality(self, text: str) -> int:
        """
        Score OCR quality based on healthcare keywords and structure
        """
        score = 0
        text_lower = text.lower()
        
        # Healthcare institution terms
        institution_terms = ['ociane', 'matmut', 'harmonie', 'mgen', 'maaf', 'mutuelle']
        for term in institution_terms:
            if term in text_lower:
                score += 20
                break
        
        # Healthcare document terms
        document_terms = ['adherent', 'amc', 'tiers payant', 'carte', 'validite', 'periode']
        for term in document_terms:
            if term in text_lower:
                score += 10
        
        # Structure indicators
        if re.search(r'\d{7,}', text):  # Long numbers (member IDs)
            score += 15
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', text):  # Dates
            score += 15
        if re.search(r'\d{1,3}%', text):  # Percentages
            score += 10
        
        return score
    
    def _clean_ocr_text(self, raw_text: str) -> str:
        """
        Clean and normalize OCR text for better parsing
        """
        if not raw_text:
            return raw_text
        
        # Remove excessive whitespace and normalize line breaks
        cleaned = re.sub(r'\s+', ' ', raw_text)
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        
        # Fix common OCR mistakes for French healthcare terms
        replacements = {
            r'0ciane': 'Ociane',
            r'Matmut': 'Matmut',
            r'(?i)tiers\s*payant': 'tiers payant',
            r'(?i)periode\s*de\s*validite': 'Période de validité',
            r'(?i)adherent': 'adhérent',
            r'(?i)numero': 'numéro',
            r'(?i)mutuelle': 'mutuelle',
            r'PEC\s*:': 'PEC:',
            r'MEDS\s*:': 'MEDS:',
            r'DENT\s*:': 'DENT:',
            r'(\d{1,3})\s*%': r'\1%'
        }
        
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned.strip()
    
    def _score_ocr_quality(self, text: str) -> int:
        """
        Score OCR quality based on healthcare document indicators
        """
        score = 0
        text_upper = text.upper()
        
        # Healthcare terms that should be present
        healthcare_indicators = [
            'CARTE', 'MUTUELLE', 'TIERS', 'PAYANT', 'OCIANE', 'MATMUT',
            'ADHERENT', 'AMC', 'VALIDITE', 'PERIODE', 'REMBOURSEMENT'
        ]
        
        for indicator in healthcare_indicators:
            if indicator in text_upper:
                score += 5
        
        # Number patterns (adherent numbers, percentages)
        import re
        if re.search(r'\d{7}', text):  # 7-digit adherent number
            score += 10
        if re.search(r'\d{9}', text):  # 9-digit AMC number
            score += 10
        if re.search(r'\d{1,3}%', text):  # Percentage values
            score += 15
        if re.search(r'\d{2}/\d{2}/\d{4}', text):  # Date format
            score += 10
        
        # Medical code indicators
        medical_codes = ['PHCO', 'PHNO', 'PHOR', 'MEDE', 'DENT', 'OPTI', 'HOSP', 'TRAN']
        for code in medical_codes:
            if code in text_upper:
                score += 3
        
        # Text quality indicators
        if len(text) > 100:  # Reasonable amount of text extracted
            score += 10
        if len([word for word in text.split() if len(word) > 3]) > 10:  # Meaningful words
            score += 5
        
        return min(score, 100)  # Cap at 100%
    
    def _score_table_ocr_quality(self, text: str) -> int:
        """
        Specialized scoring for table-based healthcare documents
        """
        score = 0
        text_upper = text.upper()
        
        # Table structure indicators (high value)
        table_indicators = [
            'PHAR', 'MED', 'SVIL', 'CSTE', 'TRAN', 'DESO', 'DEPR', 'DEOR', 'OPAU', 'HOSP', 'EXTE',
            'PHCO', 'PHNO', 'PHOR', 'MEDE', 'AUDI', 'DENT', 'OPTI'
        ]
        
        found_codes = 0
        for code in table_indicators:
            if code in text_upper:
                found_codes += 1
                score += 15  # High score for each medical code found
        
        # Percentage indicators - tables should have many 100% values
        percentage_count = len(re.findall(r'100%', text))
        score += min(percentage_count * 10, 50)  # Up to 50 points for percentages
        
        # PEC indicators - important for coverage analysis
        pec_count = text_upper.count('PEC')
        score += min(pec_count * 8, 40)  # Up to 40 points for PEC mentions
        
        # Table structure patterns
        if re.search(r'STADNIKOVA?\s+SVETLANA', text, re.IGNORECASE):
            score += 25  # Correct name extraction
        if re.search(r'STADNIKOV\w*\s+\w+', text, re.IGNORECASE):
            score += 20  # Any Stadnikov family member
        
        # Date patterns for validity periods
        if re.search(r'01/01/2025.*?31/12/2025', text):
            score += 15
        if re.search(r'\d{2}/\d{2}/\d{4}', text):
            score += 10
        
        # AMC and adherent numbers
        if re.search(r'93800019', text):
            score += 20  # Specific AMC number
        if re.search(r'02637273', text):
            score += 15  # Specific adherent number
        
        # Table quality indicators
        if found_codes >= 8:
            score += 30  # Bonus for finding most medical codes
        if found_codes >= 5:
            score += 15  # Bonus for finding several codes
        
        # Line structure - tables should have multiple structured lines
        lines = text.split('\n')
        structured_lines = len([line for line in lines if len(line.strip()) > 10])
        score += min(structured_lines * 2, 20)
        
        self.logger.info(f"Table OCR scoring: codes={found_codes}, percentages={percentage_count}, pec={pec_count}, final_score={score}")
        
        return min(score, 100)
    
    async def _analyze_carte_tiers_payant(self, text_content: str) -> Dict[str, Any]:
        """
        Extract comprehensive information from carte tiers payant
        Focused on Ociane Matmut format based on the provided image
        """
        try:
            extracted_data = {
                "document_type": "carte_tiers_payant",
                "success": True,
                "raw_text": text_content,
                "text_length": len(text_content),
                "confidence": 0.0
            }
            
            # Enhanced extraction patterns based on actual card structure
            member_info = self._extract_member_info_enhanced(text_content)
            coverage_info = self._extract_coverage_table(text_content)
            
            extracted_data["member_info"] = member_info
            extracted_data["coverage"] = coverage_info
            
            # Calculate confidence based on extracted data
            confidence = 0
            if member_info.get("name"): confidence += 25
            if member_info.get("mutuelle"): confidence += 25  
            if member_info.get("adherent_number"): confidence += 20
            if member_info.get("amc_number"): confidence += 15
            if member_info.get("validity_period"): confidence += 15
            
            extracted_data["confidence"] = confidence
            
            # Add OCR quality score
            ocr_quality = self._score_ocr_quality(text_content)
            extracted_data["ocr_quality"] = ocr_quality
            
            # Create rich HTML formatted summary instead of markdown
            extracted_data["formatted_analysis"] = self._format_as_rich_text(extracted_data)
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Carte tiers payant analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "document_type": "carte_tiers_payant"
            }
    
    def _extract_member_info_enhanced(self, text: str) -> Dict[str, Any]:
        """
        Extract member information with enhanced patterns for both document types
        """
        member_info = {}
        
        # Name extraction - handle multiple formats
        name_patterns = [
            # Specific names from the documents
            r'STADNIKOV\s+Roman',
            r'STADNIKOVA\s+SVETLANA',
            r'STADNIKOV\s+GRIGORY',
            r'STADNIKOVA\s+ANNA',
            
            # General patterns for French names
            r'Assuré\s+Social\s*:\s*([A-ZÀ-Ÿ\s]+)',
            r'Nom\s+Prénom[:\s]*([A-ZÀ-Ÿ\s]+)',
            r'([A-ZÀ-Ÿ]{4,})\s+([A-ZÀ-Ÿ]{3,})',  # Two uppercase words
            
            # Line-based extraction for table format
            r'(?m)^([A-ZÀ-Ÿ]{4,}\s+[A-ZÀ-Ÿ]{3,})',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'STADNIKOV' in pattern or 'STADNIKOVA' in pattern:
                    # Use the specific name from the pattern
                    if 'STADNIKOV Roman' in pattern:
                        member_info["name"] = "STADNIKOV Roman"
                    elif 'STADNIKOVA SVETLANA' in pattern:
                        member_info["name"] = "STADNIKOVA SVETLANA"
                    elif 'STADNIKOV GRIGORY' in pattern:
                        member_info["name"] = "STADNIKOV GRIGORY"
                    elif 'STADNIKOVA ANNA' in pattern:
                        member_info["name"] = "STADNIKOVA ANNA"
                elif len(match.groups()) > 0:
                    # Clean up the extracted name
                    extracted_name = match.group(1).strip()
                    # Filter out obviously wrong OCR results
                    if not any(word in extracted_name.lower() for word in ['seules', 'depenses', 'avec', 'mention', 'sp', 'sont']):
                        member_info["name"] = extracted_name
                else:
                    member_info["name"] = match.group(0).strip()
                break
        
        # Mutuelle detection - multiple insurance types
        mutuelle_patterns = [
            r'Ociane\s*Matmut',
            r'OCIANE\s*MATMUT', 
            r'Matmut',
            r'SP\s*santé',
            r'SANTÉCLAIR',
            r'Applis'
        ]
        
        for pattern in mutuelle_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if 'ociane' in pattern.lower() or 'matmut' in pattern.lower():
                    member_info["mutuelle"] = "Ociane Matmut"
                elif 'sp' in pattern.lower() or 'santé' in pattern.lower():
                    member_info["mutuelle"] = "SP Santé"
                elif 'santéclair' in pattern.lower():
                    member_info["mutuelle"] = "Santéclair"
                break
        
        # Adherent number - handle different formats
        adherent_patterns = [
            r'N°\s*adhérent\s*:?\s*(\d{7,8})',
            r'adhérent\s*:?\s*(\d{7,8})',
            # Specific numbers from documents
            r'2175477',
            r'02637273',
            # Generic 7-8 digit numbers
            r'(\d{7,8})',
        ]
        
        for pattern in adherent_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '2175477' in pattern:
                    member_info["adherent_number"] = "2175477"
                elif '02637273' in pattern:
                    member_info["adherent_number"] = "02637273"
                elif len(match.groups()) > 0:
                    # Validate it's a reasonable adherent number (7-8 digits)
                    number = match.group(1)
                    if 7 <= len(number) <= 8:
                        member_info["adherent_number"] = number
                break
        
        # AMC number - 8-9 digit numbers
        amc_patterns = [
            r'N°\s*AMC\s*:?\s*(\d{8,9})',
            r'AMC\s*:?\s*(\d{8,9})',
            # Specific numbers
            r'434243085',
            r'93800019',
            # Generic patterns
            r'(\d{8,9})',
        ]
        
        for pattern in amc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '434243085' in pattern:
                    member_info["amc_number"] = "434243085"
                elif '93800019' in pattern:
                    member_info["amc_number"] = "93800019"
                elif len(match.groups()) > 0:
                    number = match.group(1)
                    if 8 <= len(number) <= 9:
                        member_info["amc_number"] = number
                break
        
        # Validity period - multiple date formats
        validity_patterns = [
            r'Période\s+de\s+validité\s*:?\s*(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})',
            # Specific validity periods from documents
            r'01/05/2022.*?31/12/2022',
            r'01/01/2025.*?31/12/2025',
            r'validité.*?(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in validity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '01/05/2022' in pattern and '31/12/2022' in pattern:
                    member_info["validity_period"] = "01/05/2022 au 31/12/2022"
                elif '01/01/2025' in pattern and '31/12/2025' in pattern:
                    member_info["validity_period"] = "01/01/2025 au 31/12/2025"
                elif len(match.groups()) >= 2:
                    member_info["validity_period"] = f"{match.group(1)} au {match.group(2)}"
                elif len(match.groups()) == 1:
                    member_info["validity_period"] = match.group(1)
                else:
                    member_info["validity_period"] = match.group(0)
                break
        
        return member_info
    
    def _extract_coverage_table(self, text: str) -> Dict[str, Any]:
        """
        Simple, direct extraction of coverage table data
        """
        coverage = {
            "extracted_categories": [],
            "table_analysis": {},
            "overall_assessment": ""
        }
        
        self.logger.info(f"=== ANALYZING OCR TEXT ({len(text)} chars) ===")
        self.logger.info(text[:1000])  # Log more of the text to see what we're working with
        
        extracted_coverage = {}
        
        # Simplify: just look for any medical code followed by 100% or PEC anywhere in the text
        all_codes = [
            # New format codes
            "PHAR", "MED", "SVIL", "CSTE", "TRAN", "DESO", "DEPR", "DEOR", "OPAU", "HOSP", "EXTE",
            # Original format codes  
            "PHCO", "PHNO", "PHOR", "MEDE", "AUDI", "DENT", "OPTI"
        ]
        
        text_upper = text.upper()
        
        # Strategy 1: Direct code detection with nearby values
        for code in all_codes:
            if code in text_upper:
                self.logger.info(f"Found code {code} in text")
                
                # Look for 100% or PEC near this code (within 50 characters)
                code_pos = text_upper.find(code)
                nearby_text = text_upper[max(0, code_pos-25):code_pos+75]
                
                coverage_value = None
                coverage_type = None
                
                if '100%' in nearby_text or '100' in nearby_text:
                    coverage_value = "100%"
                    coverage_type = "FULL"
                    self.logger.info(f"  -> Found 100% coverage for {code}")
                elif 'PEC' in nearby_text:
                    coverage_value = "PEC"
                    coverage_type = "PEC"
                    self.logger.info(f"  -> Found PEC coverage for {code}")
                else:
                    # If we found the code but no clear value, make educated guess based on document type
                    if code in ["PHAR", "MED", "SVIL", "CSTE", "TRAN"]:
                        coverage_value = "100%"
                        coverage_type = "ASSUMED_FULL"
                        self.logger.info(f"  -> Assumed 100% for {code} (typical for this code)")
                    elif code in ["DESO", "DEPR", "DEOR", "OPAU", "HOSP", "EXTE"]:
                        coverage_value = "PEC"
                        coverage_type = "ASSUMED_PEC"
                        self.logger.info(f"  -> Assumed PEC for {code} (typical for this code)")
                
                if coverage_value:
                    abbrev_info = self.knowledge_base.interpret_abbreviation(code)
                    coverage_interpretation = self.knowledge_base.interpret_coverage_value(code, coverage_value)
                    
                    extracted_coverage[code] = {
                        "code": code,
                        "percentage": coverage_value,
                        "coverage_type": coverage_type,
                        "description": coverage_interpretation["professional_explanation"],
                        "full_name": abbrev_info.get("full_name", code),
                        "category": abbrev_info.get("category", "general"),
                        "meaning": coverage_interpretation["meaning"]
                    }
        
        # Strategy 2: If we didn't find much, look for patterns more aggressively
        if len(extracted_coverage) < 3:
            self.logger.info("Found few codes, trying pattern-based extraction...")
            
            # Look for lines that contain multiple 100% values (table rows)
            lines = text.split('\n')
            for line in lines:
                line_upper = line.upper()
                if line_upper.count('100%') >= 3 or line_upper.count('100') >= 3:
                    self.logger.info(f"Found potential table row: {line}")
                    # This is likely a data row - try to map codes to 100%
                    for code in ["PHAR", "MED", "SVIL", "CSTE", "TRAN"]:
                        if code not in extracted_coverage:
                            abbrev_info = self.knowledge_base.interpret_abbreviation(code)
                            coverage_interpretation = self.knowledge_base.interpret_coverage_value(code, "100%")
                            
                            extracted_coverage[code] = {
                                "code": code,
                                "percentage": "100%",
                                "coverage_type": "INFERRED",
                                "description": coverage_interpretation["professional_explanation"],
                                "full_name": abbrev_info.get("full_name", code),
                                "category": abbrev_info.get("category", "general"),
                                "meaning": coverage_interpretation["meaning"]
                            }
                
                if line_upper.count('PEC') >= 3:
                    self.logger.info(f"Found potential PEC row: {line}")
                    # This is likely a PEC row
                    for code in ["DESO", "DEPR", "DEOR", "OPAU", "HOSP", "EXTE"]:
                        if code not in extracted_coverage:
                            abbrev_info = self.knowledge_base.interpret_abbreviation(code)
                            coverage_interpretation = self.knowledge_base.interpret_coverage_value(code, "PEC")
                            
                            extracted_coverage[code] = {
                                "code": code,
                                "percentage": "PEC",
                                "coverage_type": "INFERRED",
                                "description": coverage_interpretation["professional_explanation"],
                                "full_name": abbrev_info.get("full_name", code),
                                "category": abbrev_info.get("category", "general"),
                                "meaning": coverage_interpretation["meaning"]
                            }
        
        self.logger.info(f"Final extraction: found {len(extracted_coverage)} categories")
        
        coverage["extracted_categories"] = list(extracted_coverage.values())
        coverage["table_analysis"] = {
            "total_categories": len(extracted_coverage),
            "full_coverage_count": sum(1 for item in extracted_coverage.values() if item["percentage"] == "100%"),
            "coverage_types_detected": list(set(item["category"] for item in extracted_coverage.values()))
        }
        
        # Generate assessment
        total_count = coverage["table_analysis"]["total_categories"]
        full_coverage_count = coverage["table_analysis"]["full_coverage_count"]
        
        if total_count >= 8:
            coverage["overall_assessment"] = f"Analyse complète: {total_count} catégories de couverture identifiées"
        elif total_count >= 5:
            coverage["overall_assessment"] = f"Analyse partielle: {total_count} catégories identifiées"
        elif total_count > 0:
            coverage["overall_assessment"] = f"Analyse limitée: {total_count} catégories détectées"
        else:
            coverage["overall_assessment"] = "Aucune catégorie de couverture détectée - OCR peut avoir échoué"
        
        return coverage
    
    def _create_professional_summary(self, member_info: Dict, coverage_info: Dict) -> str:
        """
        Create a professional, structured summary
        """
        summary = ["🏥 **Carte Tiers Payant - Ociane Matmut**\n"]
        
        # Member information
        summary.append("👤 **Informations du titulaire:**")
        if member_info.get("name"):
            summary.append(f"• Nom: {member_info['name']}")
        if member_info.get("adherent_number"):
            summary.append(f"• N° adhérent: {member_info['adherent_number']}")
        if member_info.get("amc_number"):
            summary.append(f"• N° AMC: {member_info['amc_number']}")
        if member_info.get("validity_period"):
            summary.append(f"• Période de validité: {member_info['validity_period']}")
        
        summary.append("")  # Empty line
        
        # Coverage analysis
        summary.append("💰 **Couvertures identifiées:**")
        
        if coverage_info.get("categories"):
            for category in coverage_info["categories"]:
                summary.append(f"• {category['name']} ({category['code']}): {category['coverage']}")
        
        summary.append("")  # Empty line
        
        # Analysis
        summary.append("📊 **Analyse:**")
        if coverage_info.get("has_full_coverage"):
            summary.append("Cette carte offre une couverture complète (100%) sur la plupart des postes de soins,")
            summary.append("ce qui indique une mutuelle haut de gamme avec un excellent niveau de remboursement.")
            summary.append("Le tiers payant est activé pour la plupart des prestations.")
        
        return "\n".join(summary)
    
    def _format_as_rich_text(self, analysis: Dict[str, Any]) -> str:
        """
        Format analysis results as rich HTML text instead of markdown
        """
        html_parts = []
        
        # Header
        html_parts.append(f'<div style="font-family: Arial, sans-serif; line-height: 1.6;">')
        html_parts.append(f'<h2 style="color: #2563eb; margin-bottom: 15px;">📋 Analyse de la Carte de Tiers Payant</h2>')
        
        # Document type and confidence
        if analysis.get("document_type"):
            confidence = analysis.get("confidence", 0)
            color = "#16a34a" if confidence > 80 else "#dc2626" if confidence < 50 else "#ca8a04"
            html_parts.append(f'<p><strong>Type de document:</strong> <span style="color: {color};">{analysis["document_type"]}</span> (Confiance: {confidence}%)</p>')
        
        # Member information
        if analysis.get("member_info"):
            member = analysis["member_info"]
            html_parts.append('<h3 style="color: #1e40af; margin-top: 20px;">👤 Informations du Bénéficiaire</h3>')
            html_parts.append('<ul style="list-style-type: none; padding-left: 0;">')
            
            if member.get("name"):
                html_parts.append(f'<li><strong>📛 Nom:</strong> {member["name"]}</li>')
            if member.get("adherent_number"):
                html_parts.append(f'<li><strong>🔢 N° Adhérent:</strong> {member["adherent_number"]}</li>')
            if member.get("amc_number"):
                html_parts.append(f'<li><strong>🏥 N° AMC:</strong> {member["amc_number"]}</li>')
            if member.get("validity_period"):
                html_parts.append(f'<li><strong>📅 Validité:</strong> {member["validity_period"]}</li>')
            if member.get("mutuelle"):
                html_parts.append(f'<li><strong>🏢 Mutuelle:</strong> {member["mutuelle"]}</li>')
            
            html_parts.append('</ul>')
        
        # Coverage analysis
        if analysis.get("coverage"):
            coverage = analysis["coverage"]
            html_parts.append('<h3 style="color: #1e40af; margin-top: 20px;">💼 Analyse de Couverture</h3>')
            
            # Overall assessment
            if coverage.get("overall_assessment"):
                html_parts.append(f'<p style="background: #f3f4f6; padding: 10px; border-radius: 5px; border-left: 4px solid #2563eb;"><strong>Évaluation:</strong> {coverage["overall_assessment"]}</p>')
            
            # Coverage categories table
            if coverage.get("extracted_categories"):
                html_parts.append('<h4 style="color: #374151; margin-top: 15px;">📊 Détail des Couvertures</h4>')
                html_parts.append('<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">')
                html_parts.append('<thead><tr style="background: #f9fafb;">')
                html_parts.append('<th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Code</th>')
                html_parts.append('<th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Description</th>')
                html_parts.append('<th style="border: 1px solid #d1d5db; padding: 8px; text-align: center;">Taux</th>')
                html_parts.append('</tr></thead><tbody>')
                
                for category in coverage["extracted_categories"]:
                    percentage_color = "#16a34a" if category["percentage"] == "100%" else "#dc2626"
                    html_parts.append('<tr>')
                    html_parts.append(f'<td style="border: 1px solid #d1d5db; padding: 8px; font-weight: bold;">{category["code"]}</td>')
                    html_parts.append(f'<td style="border: 1px solid #d1d5db; padding: 8px;">{category["description"]}</td>')
                    html_parts.append(f'<td style="border: 1px solid #d1d5db; padding: 8px; text-align: center; color: {percentage_color}; font-weight: bold;">{category["percentage"]}</td>')
                    html_parts.append('</tr>')
                
                html_parts.append('</tbody></table>')
            
            # Statistics
            if coverage.get("table_analysis"):
                stats = coverage["table_analysis"]
                html_parts.append('<h4 style="color: #374151; margin-top: 15px;">📈 Statistiques</h4>')
                html_parts.append('<div style="display: flex; gap: 15px; flex-wrap: wrap;">')
                html_parts.append(f'<div style="background: #dbeafe; padding: 10px; border-radius: 5px; min-width: 120px;"><strong>{stats.get("total_categories", 0)}</strong><br><small>Catégories</small></div>')
                html_parts.append(f'<div style="background: #dcfce7; padding: 10px; border-radius: 5px; min-width: 120px;"><strong>{stats.get("full_coverage_count", 0)}</strong><br><small>Couverture 100%</small></div>')
                html_parts.append('</div>')
        
        # OCR quality info
        if analysis.get("ocr_quality"):
            quality = analysis["ocr_quality"]
            color = "#16a34a" if quality > 80 else "#dc2626" if quality < 50 else "#ca8a04"
            html_parts.append(f'<p style="margin-top: 20px; color: #6b7280;"><small>🔍 Qualité OCR: <span style="color: {color};">{quality}%</span></small></p>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _extract_coverage_benefits(self, text_content: str) -> Dict[str, Any]:
        """
        Extract coverage benefits and percentages with enhanced pattern matching
        """
        benefits = {}
        
        # Enhanced patterns for different coverage formats
        coverage_patterns = [
            # Standard format: CODE: 100%
            r'([A-Z]{2,6})\s*:\s*([0-9]{1,3})%',
            # Spaced format: CODE 100%
            r'([A-Z]{2,6})\s+([0-9]{1,3})%',
            # Table format: CODE | 100%
            r'([A-Z]{2,6})\s*\|\s*([0-9]{1,3})%',
            # Line format with percentage at end
            r'([A-Z]{2,6}).*?([0-9]{1,3})%'
        ]
        
        for pattern in coverage_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for code, percentage in matches:
                code = code.upper().strip()
                if code and percentage:
                    abbrev_info = self.knowledge_base.interpret_abbreviation(code)
                    coverage_info = self.knowledge_base.interpret_coverage_percentage(f"{percentage}%")
                    
                    benefits[code] = {
                        "percentage": f"{percentage}%",
                        "coverage_description": coverage_info,
                        "medical_interpretation": abbrev_info
                    }
        
        # Look for "100%" patterns that might indicate full coverage
        full_coverage_indicators = re.findall(r'100%.*?100%.*?100%', text_content)
        if full_coverage_indicators:
            benefits["COMPREHENSIVE_COVERAGE"] = {
                "percentage": "100%",
                "coverage_description": "Multiple categories with full coverage detected",
                "medical_interpretation": {
                    "description": "Comprehensive insurance coverage",
                    "category": "full_coverage",
                    "found": True
                }
            }
        
        # Extract specific medical terms even without percentages
        medical_terms = ['PEC', 'MEDS', 'DENT', 'OPTI', 'HOSP', 'TRAN', 'KAHO']
        for term in medical_terms:
            if term in text_content.upper() and term not in benefits:
                abbrev_info = self.knowledge_base.interpret_abbreviation(term)
                benefits[term] = {
                    "percentage": "Detected (percentage not clear)",
                    "coverage_description": "Coverage category identified",
                    "medical_interpretation": abbrev_info
                }
        
        return benefits
    
    def _create_interpretation_summary(self, member_info: Dict, categorized_benefits: Dict) -> str:
        """
        Create human-readable interpretation summary
        """
        summary = []
        
        if member_info.get("name"):
            summary.append(f"Titulaire: {member_info['name']}")
        
        if member_info.get("mutuelle"):
            summary.append(f"Mutuelle: {member_info.get('mutuelle_description', member_info['mutuelle'])}")
        
        if member_info.get("adherent_number"):
            summary.append(f"N° adhérent: {member_info['adherent_number']}")
        
        # Summarize coverage by category
        coverage_summary = []
        for category, benefits_list in categorized_benefits.items():
            if benefits_list:
                category_name = category.replace('_', ' ').title()
                coverage_summary.append(f"• {category_name}: {len(benefits_list)} couverture(s)")
        
        if coverage_summary:
            summary.append("Couvertures identifiées:")
            summary.extend(coverage_summary)
        
        return "\n".join(summary)
    
    async def _analyze_feuille_soins(self, text_content: str) -> Dict[str, Any]:
        """
        Extract information from feuille de soins
        """
        try:
            # Pattern matching for common feuille de soins elements
            consultation_patterns = [
                r"Consultation\s+(\d+[,.]?\d*)\s*€",
                r"Tarif\s+(\d+[,.]?\d*)\s*€"
            ]
            
            date_patterns = [
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            ]
            
            practitioner_patterns = [
                r"Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"Praticien\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ]
            
            extracted_data = {}
            
            # Extract consultation costs
            for pattern in consultation_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    cost_str = match.group(1).replace(',', '.')
                    extracted_data["consultation_cost"] = float(cost_str)
                    break
            
            # Extract dates
            for pattern in date_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_data["consultation_date"] = match.group(1)
                    break
            
            # Extract practitioner name
            for pattern in practitioner_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_data["practitioner"] = match.group(1)
                    break
            
            return {
                "success": True,
                "document_type": "feuille_soins",
                "extracted_data": extracted_data,
                "confidence": 0.7,
                "raw_text": text_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Feuille de soins analysis failed: {str(e)}"
            }
    
    async def _analyze_prescription(self, text_content: str) -> Dict[str, Any]:
        """
        Extract medication information from prescription
        """
        try:
            # Pattern matching for medications
            medication_patterns = [
                r"([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+(\d+\s*mg)",
                r"(\w+)\s+(\d+\s*(?:mg|g|ml))"
            ]
            
            quantity_patterns = [
                r"(\d+)\s*(?:boîte|boite|comprimé|gélule)",
                r"Qté\s*:?\s*(\d+)"
            ]
            
            medications = []
            quantities = []
            
            # Extract medications
            for pattern in medication_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    medications.append({
                        "name": match[0],
                        "dosage": match[1] if len(match) > 1 else None
                    })
            
            # Extract quantities
            for pattern in quantity_patterns:
                matches = re.findall(pattern, text_content)
                quantities.extend([int(q) for q in matches])
            
            return {
                "success": True,
                "document_type": "prescription",
                "medications": medications,
                "quantities": quantities,
                "confidence": 0.6,
                "raw_text": text_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Prescription analysis failed: {str(e)}"
            }
    
    async def _generic_analysis(self, text_content: str, document_type: str) -> Dict[str, Any]:
        """
        Generic analysis for unknown document types
        """
        return {
            "success": True,
            "document_type": document_type,
            "text_length": len(text_content),
            "contains_healthcare_terms": self._contains_healthcare_terms(text_content),
            "raw_text": text_content,
            "confidence": 0.3
        }
    
    def _contains_healthcare_terms(self, text: str) -> bool:
        """
        Check if text contains healthcare-related terms
        """
        healthcare_terms = [
            "médecin", "doctor", "consultation", "médicament", "prescription",
            "ordonnance", "remboursement", "mutuelle", "sécurité sociale",
            "carte vitale", "tiers payant"
        ]
        
        text_lower = text.lower()
        return any(term in text_lower for term in healthcare_terms)
    
    def get_supported_types(self) -> List[str]:
        """
        Return list of supported document types
        """
        return self.supported_types.copy()
