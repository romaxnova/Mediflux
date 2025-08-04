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


class DocumentAnalyzer:
    """
    Analyzes healthcare documents using OCR and rule-based extraction
    Focuses on extracting structured data for reimbursement simulation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_types = [
            "carte_tiers_payant",
            "feuille_soins",
            "prescription",
            "auto_detect"
        ]
    
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
        Auto-detect document type based on filename and content patterns
        TODO: Implement with actual OCR and pattern matching
        """
        filename = os.path.basename(document_path).lower()
        
        if any(keyword in filename for keyword in ["carte", "tiers", "payant", "vitale"]):
            return "carte_tiers_payant"
        elif any(keyword in filename for keyword in ["feuille", "soins", "remboursement"]):
            return "feuille_soins"
        elif any(keyword in filename for keyword in ["prescription", "ordonnance"]):
            return "prescription"
        else:
            return "unknown"
    
    async def _extract_text_with_ocr(self, document_path: str) -> str:
        """
        Extract text using Tesseract OCR
        TODO: Implement actual Tesseract integration
        """
        # Placeholder - would use pytesseract or similar
        return f"[OCR_PLACEHOLDER] Text content from {document_path}"
    
    async def _analyze_carte_tiers_payant(self, text_content: str) -> Dict[str, Any]:
        """
        Extract information from carte tiers payant
        """
        try:
            # Example extraction patterns (would be refined with real OCR text)
            mutuelle_patterns = [
                r"Mutuelle\s+([A-Za-z\s]+)",
                r"Organisme\s+([A-Za-z\s]+)",
                r"([A-Z]{2,}\s+[A-Z]{2,})"  # Insurance company names in caps
            ]
            
            numero_patterns = [
                r"N°\s*(\d+)",
                r"Numéro\s*:?\s*(\d+)",
                r"(\d{13,})"  # Long identification numbers
            ]
            
            # Extract mutuelle information
            mutuelle_info = {}
            for pattern in mutuelle_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    mutuelle_info["name"] = match.group(1).strip()
                    break
            
            # Extract identification numbers
            for pattern in numero_patterns:
                match = re.search(pattern, text_content)
                if match:
                    mutuelle_info["numero"] = match.group(1)
                    break
            
            # Determine mutuelle type (basic heuristics)
            mutuelle_type = "basic"
            if mutuelle_info.get("name"):
                name_lower = mutuelle_info["name"].lower()
                if any(premium in name_lower for premium in ["premium", "plus", "confort", "excellence"]):
                    mutuelle_type = "premium"
            
            return {
                "success": True,
                "document_type": "carte_tiers_payant",
                "mutuelle_info": {
                    **mutuelle_info,
                    "type": mutuelle_type,
                    "tiers_payant_enabled": True  # Assume true for carte tiers payant
                },
                "confidence": 0.8,  # Placeholder confidence score
                "raw_text": text_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Carte tiers payant analysis failed: {str(e)}"
            }
    
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
