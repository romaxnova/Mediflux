"""
Contains mapping data for medical specialties in French and English.
"""

SPECIALTY_MAP = {
    # French specialties
    "allergologue": "10",
    "anesthésiste": "01",
    "cardiologue": "03",
    "dermatologue": "04",
    "dentiste": "DC",
    "gastro-entérologue": "08",
    "gynécologue": "07",
    "neurologue": "17",
    "ophtalmologue": "15",
    "pédiatre": "19",
    "psychiatre": "22",
    "radiologue": "06",
    "chiropracteur": "CH",
    "sage-femme": "SF",
    "médecin": "MD",
    "généraliste": "MD",

    # English translations
    "allergist": "10",
    "anesthetist": "01",
    "cardiologist": "03",
    "dermatologist": "04",
    "dentist": "DC",
    "gastroenterologist": "08",
    "gynecologist": "07",
    "neurologist": "17",
    "ophthalmologist": "15",
    "pediatrician": "19",
    "psychiatrist": "22",
    "radiologist": "06",
    "chiropractor": "CH",
    "midwife": "SF",
    "doctor": "MD",
    "general practitioner": "MD",
}

# Add common variations and misspellings
SPECIALTY_VARIATIONS = {
    "dermato": "dermatologue",
    "allergist-immunologist": "allergologue",
    "allergy": "allergologue",
    "chirurgien dentiste": "dentiste",
    "dental surgeon": "dentiste",
    "chiro": "chiropracteur",
}
