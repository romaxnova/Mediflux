from fastapi import APIRouter, HTTPException
import requests
from typing import Dict, List, Any

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
    # ProfessionSante codes (updated based on API testing)
    # General practitioners
    "generaliste": "60",  # Médecin généraliste
    "médecin": "60",
    "medecin": "60",
    "médecin généraliste": "60",
    "medecin generaliste": "60",
    
    # Specialists - most use code "95" (Médecin spécialiste)
    "chirurgien": "95",   # Médecin spécialiste
    "chirurgiens": "95",
    "dermatologue": "95", # Médecin spécialiste
    "dermatologist": "95",
    "dermatologues": "95",
    "allergologue": "95", # Médecin spécialiste
    "allergist": "95",
    "allergologues": "95",
    "pédiatre": "95",     # Médecin spécialiste
    "pediatre": "95",
    "pediatrician": "95",
    "pédiatres": "95",
    "cardiologue": "95",  # Médecin spécialiste
    "cardiologist": "95",
    "cardiologues": "95",
    "gynécologue": "95",  # Médecin spécialiste
    "gynecologist": "95",
    "gynécologues": "95",
    "psychiatre": "95",   # Médecin spécialiste
    "psychiatrist": "95",
    "psychiatres": "95",
    "ophtalmologiste": "95", # Médecin spécialiste
    "ophtalmologistes": "95",
    "urologue": "95",    # Médecin spécialiste
    "urologues": "95",
    "rhumatologue": "95", # Médecin spécialiste
    "rhumatologues": "95",
    "pneumologue": "95", # Médecin spécialiste
    "pneumologues": "95",
    "gastroentérologue": "95", # Médecin spécialiste
    "gastroenterologue": "95",
    "gastroentérologues": "95",
    "endocrinologue": "95", # Médecin spécialiste
    "endocrinologues": "95",
    "neurologue": "95",   # Médecin spécialiste
    "neurologues": "95",
    "oncologue": "95",    # Médecin spécialiste
    "oncologues": "95",
    "hématologue": "95",  # Médecin spécialiste
    "hematologue": "95",
    "hématologues": "95",
    "gériatre": "95",    # Médecin spécialiste
    "geriatre": "95",
    "gériatres": "95",
    "addictologue": "95", # Médecin spécialiste
    "addictologues": "95",
    "angiologue": "95",   # Médecin spécialiste
    "angiologues": "95",
    "andrologue": "95",   # Médecin spécialiste
    "andrologues": "95",
    
    # Other healthcare professionals with specific codes
    "dentiste": "86",     # Chirurgien-dentiste
    "dentist": "86",
    "dentistes": "86",
    "chirurgien-dentiste": "86",
    "chiropracteur": "54", # Chiropracteur (has specific code)
    "chiropractor": "54",
    "chiropracteurs": "54",
    "psychologue": "101", # Psychologue (has specific code)
    "psychologist": "101",
    "psychologues": "101",
    "kinésithérapeute": "80", # Kinésithérapeute (has specific code)
    "kinesitherapeute": "80",
    "kinésithérapeutes": "80",
    "podologue": "90",   # Podologue (has specific code)
    "podologues": "90",
    "nutritionniste": "50", # Nutritionniste (has specific code)
    "nutritionnistes": "50",
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

# Mode d'exercice mapping for user-friendly display
MODE_EXERCICE_LABELS = {
    "S": "Secteur libéral",
    "L": "Libéral", 
    "B": "Bénévole",
    "E": "Établissement",
    "P": "Public"
}

# Genre d'activité mapping
GENRE_ACTIVITE_LABELS = {
    "GENR01": "Activité principale",
    "GENR02": "Activité secondaire"
}

# Fonction mapping (simplified)
FONCTION_LABELS = {
    "FON-33": "Exercice régulier",
    "FON-01": "Chef de service",
    "FON-02": "Praticien hospitalier",
    "FON-03": "Praticien associé",
    "FON-17": "Remplaçant",
    "FON-22": "Attaché",
    "FON-AU": "Autre fonction"
}

class AnnuaireSanteClient:
    def __init__(self, api_key):
        self.api_key = api_key
        # Use PractitionerRole endpoint for specialty/postal code search
        self.base_url = 'https://gateway.api.esante.gouv.fr/fhir/PractitionerRole'

    def search_medecins(self, specialty=None, cp=None, role=None):
        headers = {'ESANTE-API-KEY': self.api_key}
        params = {}

        # Use supported API parameters: role and specialty are supported, but NOT address-postalcode
        if role:
            params['role'] = role  # This maps to ProfessionSante codes (31, 86, 60, etc.)
        elif specialty:
            # Map specialty to role if not already provided
            code = SPECIALTY_MAP.get(specialty.lower(), specialty)
            params['role'] = code
        
        # Set reasonable limit for performance
        params['_count'] = '200'  # Increase count since we'll filter locally by postal code

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
    Local proxy endpoint for PractitionerRole search (role, address-postalcode).
    Uses the correct API parameter 'role' instead of 'specialty'.
    """
    try:
        client = AnnuaireSanteClient(api_key='b2c9aa48-53c0-4d1b-83f3-7b48a3e26740')
        
        # Determine which role parameter to use
        search_role = role
        if not search_role and specialty:
            # Map specialty to role code
            search_role = SPECIALTY_MAP.get(specialty.lower(), specialty)
        
        logger.info(f"Searching with role: {search_role}, postal_code: {address_postalcode}")
        bundle = client.search_medecins(role=search_role)
        
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
            # Extract enhanced practitioner information
            practitioner_data = extract_practitioner_details(resource)
            
            # Apply specialty filtering (already handled by API role parameter, but double-check)
            if specialty:
                # If specialty is already a code, use it directly, otherwise look up from map
                if specialty.isdigit():
                    expected_code = specialty
                else:
                    expected_code = SPECIALTY_MAP.get(specialty.lower(), specialty)
                if practitioner_data['specialite'] != expected_code:
                    continue
            
            practitioners.append(practitioner_data)
    
    # Apply intelligent geographic filtering if postal code is specified
    if address_postalcode:
        practitioners = filter_by_geographic_proximity(practitioners, address_postalcode, 'b2c9aa48-53c0-4d1b-83f3-7b48a3e26740')
    
    return practitioners

def extract_practitioner_details(resource: dict) -> dict:
    """Extract comprehensive practitioner information from FHIR PractitionerRole resource"""
    
    # Extract name from extension
    name = 'Unknown'
    title = ''
    for ext in resource.get('extension', []):
        if ext.get('url', '').endswith('PractitionerRole-Name'):
            vh = ext.get('valueHumanName', {})
            family = vh.get('family', '')
            given = ' '.join(vh.get('given', []))
            suffix = ' '.join(vh.get('suffix', []))
            name = f"{family} {given}".strip()
            if suffix:
                title = suffix
            break

    # Extract specialty information
    specialty_code = None
    specialty_label = None
    mode_exercice = None
    genre_activite = None
    fonction = None
    
    if 'code' in resource and resource['code']:
        for coding in resource['code'][0].get('coding', []):
            system = coding.get('system', '')
            code = coding.get('code', '')
            
            if 'ProfessionSante' in system:
                specialty_code = code
                specialty_label = PROFESSION_SANTE_CODE_TO_LABEL.get(code)
            elif 'ModeExercice' in system:
                mode_exercice = code
            elif 'GenreActivite' in system:
                genre_activite = code
            elif 'Fonction' in system:
                fonction = code

    # Extract organization information
    organization_ref = None
    organization_name = None
    if 'organization' in resource and resource['organization']:
        organization_ref = resource['organization'].get('reference', '')
        # Extract organization ID for potential future lookups
        if organization_ref:
            org_id = organization_ref.split('/')[-1] if '/' in organization_ref else organization_ref

    # Extract practitioner reference
    practitioner_ref = None
    if 'practitioner' in resource and resource['practitioner']:
        practitioner_ref = resource['practitioner'].get('reference', '')

    # Extract smart card information (if available)
    smart_card_info = {}
    for ext in resource.get('extension', []):
        if ext.get('url', '').endswith('PractitionerRole-SmartCard'):
            card_extensions = ext.get('extension', [])
            for card_ext in card_extensions:
                url = card_ext.get('url', '')
                if url == 'type':
                    smart_card_info['type'] = card_ext.get('valueCodeableConcept', {}).get('coding', [{}])[0].get('code', '')
                elif url == 'number':
                    smart_card_info['number'] = card_ext.get('valueString', '')
                elif url == 'period':
                    period = card_ext.get('valuePeriod', {})
                    smart_card_info['valid_from'] = period.get('start', '')
                    smart_card_info['valid_until'] = period.get('end', '')

    # Extract specialty details (for specialists)
    specializations = []
    if 'specialty' in resource and resource['specialty']:
        for spec in resource['specialty']:
            for coding in spec.get('coding', []):
                system = coding.get('system', '')
                code = coding.get('code', '')
                if 'SpecialiteOrdinale' in system:
                    specializations.append({
                        'code': code,
                        'system': system
                    })

    # Determine practice type based on mode exercice
    practice_type = MODE_EXERCICE_LABELS.get(mode_exercice, "Cabinet privé")
    
    # Get user-friendly labels
    genre_activite_label = GENRE_ACTIVITE_LABELS.get(genre_activite, "")
    fonction_label = FONCTION_LABELS.get(fonction, "")

    # Create comprehensive practitioner data
    practitioner = {
        'id': resource.get('id'),
        'name': name,
        'title': title,
        'active': resource.get('active', False),
        'specialty_code': specialty_code,
        'specialty_label': specialty_label,
        'practice_type': practice_type,
        'mode_exercice': mode_exercice,
        'genre_activite': genre_activite,
        'genre_activite_label': genre_activite_label,
        'fonction': fonction,
        'fonction_label': fonction_label,
        'organization_ref': organization_ref,
        'practitioner_ref': practitioner_ref,
        'smart_card': smart_card_info,
        'specializations': specializations,
        'language': resource.get('language', 'fr'),
        
        # Legacy fields for backward compatibility
        'specialite': specialty_code,
        'specialite_label': specialty_label,
        'identifiers': resource.get('identifier', []),
        'qualifications': specializations,
        'emails': [],  # Not available in PractitionerRole
        'adresse': None,  # Requires Organization lookup
        'estimatedTravelTime': None
    }
    
    return practitioner

# Geographic filtering utilities
def extract_location_from_organization(organization_ref: str, api_key: str) -> Dict[str, Any]:
    """Extract location information from organization reference"""
    if not organization_ref:
        return {}
    
    try:
        org_id = organization_ref.split('/')[-1] if '/' in organization_ref else organization_ref
        org_url = f"https://gateway.api.esante.gouv.fr/fhir/Organization/{org_id}"
        headers = {'ESANTE-API-KEY': api_key}
        
        response = requests.get(org_url, headers=headers, timeout=10)
        if response.status_code == 200:
            org_data = response.json()
            addresses = org_data.get('address', [])
            if addresses:
                address = addresses[0]
                return {
                    'postal_code': address.get('postalCode', ''),
                    'city': address.get('city', ''),
                    'line': ' '.join(address.get('line', [])),
                    'district': address.get('district', '')
                }
    except Exception as e:
        logger.warning(f"Failed to fetch organization {org_id}: {e}")
    
    return {}

def filter_by_geographic_proximity(practitioners: List[Dict], target_postal_code: str, api_key: str) -> List[Dict]:
    """Filter practitioners by geographic proximity using intelligent postal code matching"""
    if not target_postal_code:
        return practitioners
    
    # Extract target arrondissement/department for intelligent matching
    target_dept = target_postal_code[:2] if len(target_postal_code) >= 2 else ""
    target_arr = target_postal_code[:3] if len(target_postal_code) >= 3 else ""
    
    filtered = []
    for practitioner in practitioners:
        org_ref = practitioner.get('organization_ref')
        if org_ref:
            # Try to get location from organization
            location = extract_location_from_organization(org_ref, api_key)
            if location and location.get('postal_code'):
                postal_code = location['postal_code']
                
                # Exact match
                if postal_code == target_postal_code:
                    practitioner['location_match'] = 'exact'
                    practitioner['address_info'] = location
                    filtered.append(practitioner)
                # Same arrondissement (for Paris)
                elif target_postal_code.startswith('750') and postal_code.startswith('750') and postal_code[:3] == target_arr:
                    practitioner['location_match'] = 'same_arrondissement'
                    practitioner['address_info'] = location
                    filtered.append(practitioner)
                # Same department
                elif postal_code[:2] == target_dept:
                    practitioner['location_match'] = 'same_department'
                    practitioner['address_info'] = location
                    filtered.append(practitioner)
        else:
            # No organization reference - include but mark as unknown location
            practitioner['location_match'] = 'unknown'
            practitioner['address_info'] = {}
            filtered.append(practitioner)
    
    # Sort by location relevance: exact > same_arrondissement > same_department > unknown
    location_priority = {'exact': 0, 'same_arrondissement': 1, 'same_department': 2, 'unknown': 3}
    filtered.sort(key=lambda x: location_priority.get(x.get('location_match', 'unknown'), 3))
    
    return filtered

