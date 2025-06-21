from fastapi import APIRouter, HTTPException
import requests

router = APIRouter()

import logging

# Initialize logging for MCP
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced MCP documentation
"""
This module provides the Modular Capability Provider (MCP) for Annuaire Sante API.
It handles practitioner searches and integrates with the orchestrator.
"""

SPECIALTY_MAP = {
    # ProfessionSante codes (official, unique for each specialty)
    "generaliste": "60",  # Médecin généraliste
    "médecin": "60",
    "medecin": "60",
    "médecin généraliste": "60",
    "medecin generaliste": "60",
    "dentiste": "86",     # Chirurgien-dentiste
    "dentist": "86",
    "dentistes": "86",
    "chirurgien-dentiste": "86",
    "chirurgien": "70",   # Chirurgien (code 70)
    "chirurgiens": "70",
    "dermatologue": "33", # Dermatologue (code 33)
    "dermatologist": "33",
    "dermatologues": "33",
    "allergologue": "36", # Allergologue (code 36)
    "allergist": "36",
    "allergologues": "36",
    "chiropracteur": "54", # Chiropracteur (code 54)
    "chiropractor": "54",
    "chiropracteurs": "54",
    "pédiatre": "77",     # Pédiatre (code 77)
    "pediatre": "77",
    "pediatrician": "77",
    "pédiatres": "77",
    "cardiologue": "38",  # Cardiologue (code 38)
    "cardiologist": "38",
    "cardiologues": "38",
    "gynécologue": "44",  # Gynécologue (code 44)
    "gynecologist": "44",
    "gynécologues": "44",
    "psychiatre": "84",   # Psychiatre (code 84)
    "psychiatrist": "84",
    "psychiatres": "84",
    "psychologue": "101", # Psychologue (code 101)
    "psychologist": "101",
    "psychologues": "101",
    "ophtalmologiste": "61", # Ophtalmologiste (code 61)
    "ophtalmologistes": "61",
    "kinésithérapeute": "80", # Kinésithérapeute (code 80)
    "kinesitherapeute": "80",
    "kinésithérapeutes": "80",
    "podologue": "90",   # Podologue (code 90)
    "podologues": "90",
    "nutritionniste": "50", # Nutritionniste (code 50)
    "nutritionnistes": "50",
    "anesthésiste": "34", # Anesthésiste (code 34)
    "anesthesiste": "34",
    "anesthésistes": "34",
    "urologue": "88",    # Urologue (code 88)
    "urologues": "88",
    "rhumatologue": "83", # Rhumatologue (code 83)
    "rhumatologues": "83",
    "pneumologue": "81", # Pneumologue (code 81)
    "pneumologues": "81",
    "gastroentérologue": "40", # Gastroentérologue (code 40)
    "gastroenterologue": "40",
    "gastroentérologues": "40",
    "endocrinologue": "37", # Endocrinologue (code 37)
    "endocrinologues": "37",
    "neurologue": "59",   # Neurologue (code 59)
    "neurologues": "59",
    "oncologue": "73",    # Oncologue (code 73)
    "oncologues": "73",
    "hématologue": "53",  # Hématologue (code 53)
    "hematologue": "53",
    "hématologues": "53",
    "gériatre": "47",    # Gériatre (code 47)
    "geriatre": "47",
    "gériatres": "47",
    "addictologue": "102", # Addictologue (code 102)
    "addictologues": "102",
    "angiologue": "103",   # Angiologue (code 103)
    "angiologues": "103",
    "andrologue": "104",   # Andrologue (code 104)
    "andrologues": "104",
    "pharmacien": "96",    # Pharmacien
    "pharmacist": "96",
    "pharmaciens": "96",
    "pharmacy": "96",
    "sage-femme": "31",     # Sage-femme
    "sages-femmes": "31"
    # Add more as needed
}

# ProfessionSante code to French label mapping (official TRE_G15)
PROFESSION_SANTE_CODE_TO_LABEL = {
    "60": "Médecin généraliste",
    "95": "Médecin spécialiste",
    "86": "Chirurgien-dentiste",
    "31": "Sage-femme",
    "96": "Pharmacien",
    "34": "Anesthésiste",
    "33": "Dermatologue",
    "36": "Allergologue",
    "54": "Chiropracteur",
    "77": "Pédiatre",
    "38": "Cardiologue",
    "40": "Gastroentérologue",
    "37": "Endocrinologue",
    "50": "Nutritionniste",
    "88": "Urologue",
    "83": "Rhumatologue",
    "81": "Pneumologue",
    "70": "Chirurgien"
}

# French label to ProfessionSante code mapping (reverse mapping)
PROFESSION_SANTE_LABEL_TO_CODE = {v.lower(): k for k, v in PROFESSION_SANTE_CODE_TO_LABEL.items()}

class AnnuaireSanteClient:
    def __init__(self, api_key):
        self.api_key = api_key
        # Use PractitionerRole endpoint for specialty/postal code search
        self.base_url = 'https://gateway.api.esante.gouv.fr/fhir/PractitionerRole'

    def search_medecins(self, specialty=None, cp=None, role=None):
        headers = {'ESANTE-API-KEY': self.api_key}
        params = {}

        # The API doesn't support filtering by specialty and postal code parameters
        # So we fetch all data and filter locally in parse_practitioner_bundle
        # We can add pagination parameters if needed
        params['_count'] = '100'  # Limit results to 100 for performance

        try:
            logger.info(f"Making API call to {self.base_url} with params: {params}")
            response = requests.get(self.base_url, headers=headers, params=params)
            logger.info(f"API response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"API error response: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API call failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

@router.get('/medecins')
def get_medecins(specialty: str = None, cp: str = None):
    client = AnnuaireSanteClient(api_key='b2c9aa48-53c0-4d1b-83f3-7b48a3e26740')
    bundle = client.search_medecins(specialty=specialty, cp=cp)
    if not bundle or 'entry' not in bundle:
        raise HTTPException(status_code=502, detail="No practitioners found or API call failed.")
    practitioners = parse_practitioner_bundle(bundle)
    return practitioners


@router.get('/practitionerrole/search')
def practitionerrole_search(specialty: str = None, address_postalcode: str = None, role: str = None):
    """
    Local proxy endpoint for PractitionerRole search (specialty, address-postalcode, role).
    """
    try:
        client = AnnuaireSanteClient(api_key='b2c9aa48-53c0-4d1b-83f3-7b48a3e26740')
        params = {}
        if specialty:
            params['specialty'] = specialty  # FHIR: PractitionerRole-specialty
        if address_postalcode:
            params['address-postalcode'] = address_postalcode  # FHIR: PractitionerRole-address-postalcode
        if role:
            params['role'] = role  # FHIR: PractitionerRole-role
        
        logger.info(f"Searching with params: {params}")
        bundle = client.search_medecins(**params)
        
        if not bundle:
            logger.warning("API returned None/empty response")
            raise HTTPException(status_code=502, detail="API returned empty response")
        
        if 'entry' not in bundle:
            logger.warning(f"API response missing 'entry' field: {bundle}")
            raise HTTPException(status_code=502, detail="API response format invalid")
        
        practitioners = parse_practitioner_bundle(bundle, specialty, address_postalcode)
        logger.info(f"Found {len(practitioners)} practitioners after filtering")
        return {"entry": practitioners}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in practitionerrole_search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# Build a reverse map for code -> label
SPECIALTY_CODE_TO_LABEL = {v: k for k, v in SPECIALTY_MAP.items()}

def parse_practitioner_bundle(bundle: dict, specialty: str = None, address_postalcode: str = None) -> list[dict]:
    practitioners = []
    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'PractitionerRole':
            # Extract name from extension
            name = 'Unknown'
            for ext in resource.get('extension', []):
                if ext.get('url', '').endswith('PractitionerRole-Name'):
                    vh = ext.get('valueHumanName', {})
                    family = vh.get('family', '')
                    given = ' '.join(vh.get('given', []))
                    name = f"{family} {given}".strip()
                    break

            # Extract specialty code and label
            specialty_code = None
            specialty_label = None
            if 'code' in resource and resource['code']:
                for coding in resource['code'][0].get('coding', []):
                    if 'ProfessionSante' in coding.get('system', ''):
                        specialty_code = coding.get('code')
                        specialty_label = PROFESSION_SANTE_CODE_TO_LABEL.get(specialty_code)
                        break

            # For now, we'll skip postal code filtering since it's not directly available
            # in the PractitionerRole resource. We might need to make additional API calls
            # to the Organization resource to get address information.
            
            # Filtering logic - only filter by specialty for now
            if specialty:
                # If specialty is already a code, use it directly, otherwise look up from map
                if specialty.isdigit():
                    expected_code = specialty
                else:
                    expected_code = SPECIALTY_MAP.get(specialty.lower(), specialty)
                if specialty_code != expected_code:
                    continue
            
            # For postal code filtering, we'd need to make additional API calls
            # to the Organization resource referenced in resource['organization']['reference']
            # For now, we'll skip this filtering
            
            # Map code to label for user-friendly output
            if not specialty_label:
                specialty_label = PROFESSION_SANTE_CODE_TO_LABEL.get(specialty_code)
            
            practitioner = {
                'id': resource.get('id'),
                'name': name,
                'active': resource.get('active', False),
                'identifiers': resource.get('identifier', []),
                'qualifications': [],
                'emails': [],
                'adresse': None,  # Not directly available in PractitionerRole
                'specialite': specialty_code,
                'specialite_label': specialty_label,
                'estimatedTravelTime': None
            }
            practitioners.append(practitioner)
    return practitioners

