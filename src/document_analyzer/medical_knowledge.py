"""
Medical Knowledge Base for Document Analysis
Comprehensive mapping of French healthcare abbreviations and terms
"""

import re
from typing import Dict, List, Any

class MedicalKnowledgeBase:
    """
    Knowledge base for interpreting French healthcare documents
    Focuses on carte de tiers payant abbreviations and codes
    """
    
    def __init__(self):
        self.medical_abbreviations = {
            # Coverage types - Based on French healthcare mutual insurance standards
            "PHCO": {
                "full_name": "Pharmacie Conventionnée",
                "description": "Médicaments remboursables en pharmacie conventionnée",
                "category": "medication",
                "common_values": ["IS 100%", "100%"]
            },
            "PHNO": {
                "full_name": "Pharmacie Non Conventionnée", 
                "description": "Médicaments en pharmacie non conventionnée",
                "category": "medication",
                "common_values": ["IS 100%", "100%"]
            },
            "PHOR": {
                "full_name": "Pharmacie Hors Remboursement",
                "description": "Médicaments non remboursés par la Sécurité Sociale",
                "category": "medication",
                "common_values": ["IS 100%", "100%"]
            },
            "MEDE": {
                "full_name": "Médecine Générale et Spécialisée",
                "description": "Consultations médicales généralistes et spécialistes",
                "category": "general_care",
                "common_values": ["IS 100%", "KA/OC PEC"]
            },
            "AUDI": {
                "full_name": "Audiologie et Appareillage Auditif",
                "description": "Soins auditifs et prothèses auditives",
                "category": "hearing",
                "common_values": ["IS 100%", "PEC"]
            },
            "CSTE": {
                "full_name": "Consultations Spécialisées",
                "description": "Consultations chez des médecins spécialistes",
                "category": "general_care",
                "common_values": ["OC PEC", "PEC"]
            },
            "DENT": {
                "full_name": "Soins Dentaires",
                "description": "Soins dentaires et prothèses dentaires",
                "category": "dental",
                "common_values": ["IS 100%", "PEC"]
            },
            "EXTE": {
                "full_name": "Examens Externes",
                "description": "Examens médicaux externes (radiologie, analyses, etc.)",
                "category": "diagnostics",
                "common_values": ["IS 100%", "PEC"]
            },
            "HOSP": {
                "full_name": "Hospitalisation",  
                "description": "Frais d'hospitalisation et séjours cliniques",
                "category": "hospitalization",
                "common_values": ["IS 100%", "KA/OC PEC"]
            },
            "OPTI": {
                "full_name": "Optique",
                "description": "Lunettes, lentilles et soins ophtalmologiques", 
                "category": "optics",
                "common_values": ["IS 100%", "PEC"]
            },
            "SVIL": {
                "full_name": "Soins de Ville",
                "description": "Soins ambulatoires en ville",
                "category": "general_care",
                "common_values": ["KA/OC PEC", "PEC"]
            },
            "TRAN": {
                "full_name": "Transport Sanitaire",
                "description": "Transport médical et ambulances",
                "category": "transport",
                "common_values": ["IS 100%", "100%"]
            },
            
            # Additional codes from newer document format
            "PHAR": {
                "full_name": "Pharmacie",
                "description": "Médicaments et produits pharmaceutiques",
                "category": "medication",
                "common_values": ["SP 100%", "100%"]
            },
            "MED": {
                "full_name": "Médecine", 
                "description": "Consultations et actes médicaux",
                "category": "general_care",
                "common_values": ["SP 100%", "100%"]
            },
            "DESO": {
                "full_name": "Dépassements Spécialisés",
                "description": "Dépassements d'honoraires spécialistes",
                "category": "specialist_care",
                "common_values": ["SC/TS PEC", "PEC"]
            },
            "DEPR": {
                "full_name": "Dépassements Prothèses",
                "description": "Dépassements pour prothèses",
                "category": "prosthetics",
                "common_values": ["SC/TS PEC", "PEC"]
            },
            "DEOR": {
                "full_name": "Dépassements Orthodontie",
                "description": "Dépassements orthodontiques",
                "category": "dental",
                "common_values": ["SC/TS PEC", "PEC"]
            },
            "OPAU": {
                "full_name": "Optique Autres",
                "description": "Autres frais optiques",
                "category": "optics",
                "common_values": ["SC/TS PEC", "PEC"]
            }
        }
        
        # French healthcare terminology definitions
        self.coverage_terms = {
            "PEC": {
                "full_name": "Prise En Charge",
                "description": "Remboursement selon les conditions spécifiques du contrat",
                "meaning": "La mutuelle prend en charge selon ses barèmes et conditions particulières"
            },
            "IS": {
                "full_name": "Indemnité Supplémentaire", 
                "description": "Remboursement complémentaire à la Sécurité Sociale",
                "meaning": "Complément de remboursement au-delà de la base Sécurité Sociale"
            },
            "KA": {
                "full_name": "Kine/Actes",
                "description": "Kinésithérapie et actes paramédicaux",
                "meaning": "Soins de kinésithérapie et autres actes paramédicaux"
            },
            "OC": {
                "full_name": "Optique/Chirurgie",
                "description": "Soins optiques et chirurgicaux",
                "meaning": "Frais optiques et interventions chirurgicales"
            }
        }
        
        # Additional common abbreviations
        self.general_abbreviations = {
            "PEC": {
                "full_name": "Prise En Charge",
                "description": "Coverage/reimbursement rate",
                "category": "coverage"
            },
            "PRCR": {
                "full_name": "Participation Réduite Conventionnée Réglementée", 
                "description": "Reduced regulated conventional participation",
                "category": "coverage"
            },
            "PRHO": {
                "full_name": "Participation Réduite Hors Optique",
                "description": "Reduced participation excluding optics",
                "category": "coverage"
            },
            "KAHO": {
                "full_name": "Kinésithérapie et Autres Honoraires",
                "description": "Physiotherapy and other professional fees",
                "category": "alternative"
            },
        }
        
        self.coverage_levels = {
            "100%": "Full coverage - no patient contribution",
            "90%": "High coverage - 10% patient contribution", 
            "80%": "Standard coverage - 20% patient contribution",
            "70%": "Basic coverage - 30% patient contribution",
            "60%": "Limited coverage - 40% patient contribution",
            "50%": "Minimal coverage - 50% patient contribution"
        }
        
        self.mutuelle_types = {
            "OCIANE": "Ociane Matmut - Mutual insurance company",
            "MATMUT": "Matmut Group - Insurance and banking",
            "HARMONIE": "Harmonie Mutuelle",
            "MGEN": "MGEN - Public sector mutual",
            "MAAF": "MAAF Assurances"
        }
    
    def interpret_abbreviation(self, abbrev: str) -> Dict[str, Any]:
        """
        Interpret a medical abbreviation
        """
        abbrev_upper = abbrev.upper().strip()
        
        if abbrev_upper in self.medical_abbreviations:
            return {
                "abbreviation": abbrev_upper,
                "found": True,
                **self.medical_abbreviations[abbrev_upper]
            }
        
        return {
            "abbreviation": abbrev_upper,
            "found": False,
            "description": "Unknown abbreviation"
        }
    
    def interpret_coverage_percentage(self, percentage: str) -> str:
        """
        Interpret coverage percentage meaning
        """
        clean_pct = percentage.strip().replace('%', '') + '%'
        return self.coverage_levels.get(clean_pct, f"Coverage at {clean_pct}")
    
    def interpret_coverage_value(self, code: str, value: str) -> Dict[str, Any]:
        """
        Interpret the actual coverage value (PEC, IS 100%, etc.) for a specific medical code
        """
        interpretation = {
            "code": code,
            "value": value,
            "type": "unknown",
            "meaning": "",
            "professional_explanation": ""
        }
        
        # Get base information about the medical code
        base_info = self.interpret_abbreviation(code)
        
        if "PEC" in value.upper():
            interpretation["type"] = "PEC"
            interpretation["meaning"] = "Prise en charge selon barème mutuelle"
            interpretation["professional_explanation"] = f"Pour {base_info.get('description', code)}: remboursement selon les conditions spécifiques du contrat mutuelle, généralement avec des plafonds ou des conditions particulières."
        
        elif "IS" in value and "100%" in value:
            interpretation["type"] = "IS_FULL"
            interpretation["meaning"] = "Couverture intégrale complémentaire"
            interpretation["professional_explanation"] = f"Pour {base_info.get('description', code)}: remboursement complémentaire de 100% au-delà de la base Sécurité Sociale."
        
        elif "100%" in value:
            interpretation["type"] = "FULL_COVERAGE"
            interpretation["meaning"] = "Couverture complète"
            interpretation["professional_explanation"] = f"Pour {base_info.get('description', code)}: prise en charge intégrale à 100%."
        
        else:
            # Try to extract percentage
            pct_match = re.search(r'(\d{1,3})%', value)
            if pct_match:
                percentage = pct_match.group(1)
                interpretation["type"] = "PERCENTAGE"
                interpretation["meaning"] = f"Couverture à {percentage}%"
                interpretation["professional_explanation"] = f"Pour {base_info.get('description', code)}: remboursement à hauteur de {percentage}% des frais engagés."
        
        return interpretation
    
    def extract_member_info_patterns(self) -> Dict[str, str]:
        """
        Return regex patterns for extracting member information
        """
        return {
            "member_name": r"Nom Prénom[:\s]+([A-ZÀ-Ÿ\s]+)",
            "member_number": r"(?:N°|Numéro)[:\s]*([0-9]{10,})",
            "social_security_number": r"(?:N° de sécurité sociale|Numéro SS)[:\s]*([0-9\s]{15,})",
            "validity_period": r"Période de validité[:\s]*([0-9/]{8,})",
            "mutuelle_name": r"(OCIANE|MATMUT|HARMONIE|MGEN|MAAF)",
            "coverage_percentage": r"([0-9]{1,3})%",
            "adherent_number": r"N°\s*adhérent[:\s]*([0-9]+)",
            "amc_number": r"AMC[:\s]*([0-9]+)"
        }
    
    def categorize_benefits(self, benefits_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Categorize extracted benefits by type
        """
        categorized = {
            "medication": [],
            "dental": [],
            "optics": [],
            "hospitalization": [],
            "transport": [],
            "general_care": [],
            "alternative": [],
            "coverage": []
        }
        
        for benefit_code, details in benefits_data.items():
            abbrev_info = self.interpret_abbreviation(benefit_code)
            
            category = abbrev_info.get("category", "general_care")
            
            categorized[category].append({
                "code": benefit_code,
                "interpretation": abbrev_info,
                "details": details
            })
        
        return categorized
