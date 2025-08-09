"""
Intelligent Medical Condition Extractor
Uses NLP and medical knowledge to extract conditions from user queries
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import spacy
from fuzzywuzzy import fuzz


@dataclass
class ExtractedCondition:
    """Represents an extracted medical condition"""
    condition: str
    confidence: float
    synonyms: List[str]
    category: str
    icd10_code: Optional[str] = None


class MedicalConditionExtractor:
    """
    Intelligent extraction of medical conditions from natural language queries
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Medical condition mappings with synonyms and variations
        self.condition_mappings = {
            "infection_urinaire": {
                "primary": "infection urinaire",
                "synonyms": [
                    "infection urinaire", "cystite", "uti", "infection des voies urinaires",
                    "infection vésicale", "brûlures mictionnelles", "cystite aiguë",
                    "infection tractus urinaire", "pyurie", "dysurie"
                ],
                "category": "infectious_disease",
                "icd10": "N39.0"
            },
            "hypertension": {
                "primary": "hypertension",
                "synonyms": [
                    "hypertension", "hta", "tension artérielle élevée", "pression artérielle élevée",
                    "hypertension artérielle", "haute tension", "tension haute",
                    "pression sanguine élevée", "hypertonie"
                ],
                "category": "cardiovascular",
                "icd10": "I10"
            },
            "diabete_type2": {
                "primary": "diabète type 2",
                "synonyms": [
                    "diabète type 2", "diabète de type 2", "dt2", "diabète non insulino-dépendant",
                    "diabète adulte", "diabète sucré type 2", "diabète mellitus type 2",
                    "dnid", "hyperglycémie chronique"
                ],
                "category": "endocrine",
                "icd10": "E11"
            },
            "mal_de_dos": {
                "primary": "mal de dos",
                "synonyms": [
                    "mal de dos", "douleur dorsale", "lombalgie", "dorsalgie",
                    "douleur lombaire", "lumbago", "sciatique", "douleur rachidienne",
                    "douleur colonne vertébrale", "rachialgie", "back pain"
                ],
                "category": "musculoskeletal",
                "icd10": "M54"
            },
            "depression": {
                "primary": "dépression",
                "synonyms": [
                    "dépression", "épisode dépressif", "trouble dépressif",
                    "déprime", "syndrome dépressif", "humeur dépressive",
                    "état dépressif", "mélancolie"
                ],
                "category": "mental_health",
                "icd10": "F32"
            },
            "anxiete": {
                "primary": "anxiété",
                "synonyms": [
                    "anxiété", "trouble anxieux", "angoisse", "stress",
                    "anxiété généralisée", "panique", "phobies",
                    "trouble anxieux généralisé", "tag"
                ],
                "category": "mental_health", 
                "icd10": "F41"
            }
        }
        
        # Regex patterns for medical conditions
        self.condition_patterns = [
            # Direct condition mentions
            r'\b(infection\s+urinaire|cystite|uti)\b',
            r'\b(hypertension|hta|tension\s+(?:artérielle\s+)?élevée)\b',
            r'\b(diabète\s+(?:de\s+)?type\s+2|dt2|diabète\s+adulte)\b',
            r'\b(mal\s+de\s+dos|lombalgie|dorsalgie|lumbago)\b',
            r'\b(dépression|épisode\s+dépressif|trouble\s+dépressif)\b',
            r'\b(anxiété|trouble\s+anxieux|angoisse)\b',
            
            # Symptom-based patterns
            r'\b(brûlures?\s+(?:en\s+)?urinant|dysurie)\b',
            r'\b(tension\s+haute|pression\s+élevée)\b',
            r'\b(glycémie\s+élevée|hyperglycémie)\b',
            r'\b(douleur\s+(?:au\s+)?dos|douleur\s+lombaire)\b'
        ]
        
        # Try to load spaCy model (optional, fallback to rule-based if not available)
        try:
            self.nlp = spacy.load("fr_core_news_sm")
            self.use_spacy = True
        except OSError:
            self.logger.warning("spaCy French model not found, using rule-based extraction only")
            self.nlp = None
            self.use_spacy = False
    
    def extract_condition(self, query: str) -> Optional[ExtractedCondition]:
        """
        Extract medical condition from user query
        """
        try:
            query_lower = query.lower()
            self.logger.info(f"Extracting condition from query: '{query}'")
            
            # 1. Try exact matching first
            exact_match = self._extract_exact_match(query_lower)
            if exact_match:
                self.logger.info(f"Found exact match: {exact_match}")
                return exact_match
            
            # 2. Try fuzzy matching
            fuzzy_match = self._extract_fuzzy_match(query_lower)
            if fuzzy_match:
                self.logger.info(f"Found fuzzy match: {fuzzy_match}")
                return fuzzy_match
            
            # 3. Try regex pattern matching
            pattern_match = self._extract_pattern_match(query_lower)
            if pattern_match:
                self.logger.info(f"Found pattern match: {pattern_match}")
                return pattern_match
            
            # 4. Try spaCy NER if available
            if self.use_spacy:
                spacy_match = self._extract_with_spacy(query)
                if spacy_match:
                    self.logger.info(f"Found spaCy match: {spacy_match}")
                    return spacy_match
            
            # 5. Try contextual keywords
            context_match = self._extract_contextual_match(query_lower)
            if context_match:
                self.logger.info(f"Found contextual match: {context_match}")
                return context_match
            
            self.logger.warning(f"No condition extracted from query: '{query}'")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting condition: {e}")
            return None
    
    def _extract_exact_match(self, query: str) -> Optional[ExtractedCondition]:
        """Find exact matches in condition synonyms"""
        for condition_key, condition_data in self.condition_mappings.items():
            for synonym in condition_data["synonyms"]:
                if synonym.lower() in query:
                    return ExtractedCondition(
                        condition=condition_key,
                        confidence=1.0,
                        synonyms=condition_data["synonyms"],
                        category=condition_data["category"],
                        icd10_code=condition_data["icd10"]
                    )
        return None
    
    def _extract_fuzzy_match(self, query: str) -> Optional[ExtractedCondition]:
        """Find fuzzy matches using string similarity"""
        best_match = None
        best_score = 0
        
        for condition_key, condition_data in self.condition_mappings.items():
            for synonym in condition_data["synonyms"]:
                # Calculate similarity score
                score = fuzz.partial_ratio(synonym.lower(), query)
                
                if score > best_score and score >= 80:  # 80% similarity threshold
                    best_score = score
                    best_match = ExtractedCondition(
                        condition=condition_key,
                        confidence=score / 100.0,
                        synonyms=condition_data["synonyms"],
                        category=condition_data["category"],
                        icd10_code=condition_data["icd10"]
                    )
        
        return best_match
    
    def _extract_pattern_match(self, query: str) -> Optional[ExtractedCondition]:
        """Use regex patterns to find conditions"""
        for pattern in self.condition_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                matched_text = match.group(0)
                
                # Map matched text to condition
                condition_key = self._map_text_to_condition(matched_text)
                if condition_key:
                    condition_data = self.condition_mappings[condition_key]
                    return ExtractedCondition(
                        condition=condition_key,
                        confidence=0.85,
                        synonyms=condition_data["synonyms"],
                        category=condition_data["category"],
                        icd10_code=condition_data["icd10"]
                    )
        
        return None
    
    def _extract_with_spacy(self, query: str) -> Optional[ExtractedCondition]:
        """Use spaCy NLP for condition extraction"""
        if not self.nlp:
            return None
        
        doc = self.nlp(query)
        
        # Look for medical entities
        for ent in doc.ents:
            if ent.label_ in ["MISC", "ORG"]:  # Medical terms often tagged as MISC
                entity_text = ent.text.lower()
                condition_key = self._map_text_to_condition(entity_text)
                
                if condition_key:
                    condition_data = self.condition_mappings[condition_key]
                    return ExtractedCondition(
                        condition=condition_key,
                        confidence=0.75,
                        synonyms=condition_data["synonyms"],
                        category=condition_data["category"],
                        icd10_code=condition_data["icd10"]
                    )
        
        return None
    
    def _extract_contextual_match(self, query: str) -> Optional[ExtractedCondition]:
        """Extract conditions based on contextual keywords"""
        context_mappings = {
            "urine": "infection_urinaire",
            "urinant": "infection_urinaire",
            "brûlures": "infection_urinaire",
            "brûlure": "infection_urinaire",
            "vessie": "infection_urinaire",
            "miction": "infection_urinaire",
            "dysurie": "infection_urinaire",
            "tension": "hypertension",
            "pression": "hypertension",
            "cardiovasculaire": "hypertension",
            "glycémie": "diabete_type2",
            "sucre": "diabete_type2",
            "insuline": "diabete_type2",
            "dos": "mal_de_dos",
            "colonne": "mal_de_dos",
            "vertèbre": "mal_de_dos",
            "déprim": "depression",
            "tristesse": "depression",
            "mélancolie": "depression",
            "stress": "anxiete",
            "peur": "anxiete",
            "panique": "anxiete"
        }
        
        for keyword, condition_key in context_mappings.items():
            if keyword in query:
                condition_data = self.condition_mappings[condition_key]
                return ExtractedCondition(
                    condition=condition_key,
                    confidence=0.65,
                    synonyms=condition_data["synonyms"],
                    category=condition_data["category"],
                    icd10_code=condition_data["icd10"]
                )
        
        return None
    
    def _map_text_to_condition(self, text: str) -> Optional[str]:
        """Map extracted text to condition key"""
        text_lower = text.lower()
        
        mapping = {
            "infection urinaire": "infection_urinaire",
            "cystite": "infection_urinaire",
            "uti": "infection_urinaire",
            "hypertension": "hypertension",
            "hta": "hypertension",
            "tension élevée": "hypertension",
            "diabète type 2": "diabete_type2",
            "dt2": "diabete_type2",
            "mal de dos": "mal_de_dos",
            "lombalgie": "mal_de_dos",
            "dorsalgie": "mal_de_dos",
            "lumbago": "mal_de_dos",
            "dépression": "depression",
            "anxiété": "anxiete"
        }
        
        # Direct mapping
        if text_lower in mapping:
            return mapping[text_lower]
        
        # Partial matching
        for key, condition in mapping.items():
            if key in text_lower or text_lower in key:
                return condition
        
        return None
    
    def get_condition_info(self, condition_key: str) -> Dict:
        """Get detailed information about a condition"""
        if condition_key in self.condition_mappings:
            return self.condition_mappings[condition_key]
        return {}
    
    def list_supported_conditions(self) -> List[str]:
        """List all supported conditions"""
        return list(self.condition_mappings.keys())
    
    def validate_extraction(self, query: str, expected_condition: str) -> bool:
        """Validate extraction accuracy (for testing)"""
        extracted = self.extract_condition(query)
        if extracted:
            return extracted.condition == expected_condition
        return False


# Test the extractor
if __name__ == "__main__":
    extractor = MedicalConditionExtractor()
    
    test_queries = [
        "J'ai des problèmes d'hypertension",
        "Je souffre de mal de dos",
        "Infection urinaire récurrente",
        "Mon diabète de type 2 n'est pas bien contrôlé",
        "Brûlures en urinant depuis 3 jours",
        "Ma tension est trop élevée"
    ]
    
    for query in test_queries:
        result = extractor.extract_condition(query)
        print(f"Query: {query}")
        print(f"Extracted: {result}")
        print("---")
