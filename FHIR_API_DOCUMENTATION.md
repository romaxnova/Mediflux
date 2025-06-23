# Annuaire Santé FHIR API Documentation

## Base Information
- **Base URL**: `https://gateway.api.esante.gouv.fr/fhir/v1/`
- **Authentication**: Header `ESANTE-API-KEY: {api_key}`
- **Format**: JSON (FHIR R4)

## Resources Overview

The Annuaire Santé FHIR API provides 5 main resources:

1. **Organization** - Healthcare organizations (hospitals, clinics, pharmacies)
2. **PractitionerRole** - Healthcare professionals in their professional context
3. **Practitioner** - Individual healthcare professionals (by name)
4. **HealthcareService** - Specific services offered
5. **Device** - Medical devices and equipment

---

## 1. Organization Resource

**Endpoint**: `/Organization`

### Search Parameters
- `name` - Organization name (string)
- `address-city` - City name (string) 
- `address-postalcode` - Postal code (string)
- `type` - Organization type code
- `active` - Active status (true/false)
- `_count` - Number of results (default: 20, max: 100)

### Example Queries
```
GET /Organization?name=hopital
GET /Organization?address-city=Paris
GET /Organization?address-postalcode=75016
GET /Organization?type=PHARMACY
```

### Response Structure
```json
{
  "id": "organization-id",
  "name": "Organization Name",
  "type": [{"coding": [{"code": "TYPE_CODE", "display": "Type Name"}]}],
  "active": true,
  "address": [{
    "text": "Full address",
    "line": ["Street address"],
    "city": "City",
    "postalCode": "Postal code"
  }]
}
```

---

## 2. PractitionerRole Resource

**Endpoint**: `/PractitionerRole`

### Search Parameters
- `practitioner` - Reference to Practitioner
- `organization` - Reference to Organization
- `location` - Reference to Location
- `specialty` - Medical specialty
- `role` - Professional role
- `active` - Active status (true/false)
- `_count` - Number of results

### Code Systems for Profession
- **System**: `https://mos.esante.gouv.fr/NOS/TRE-G15-ProfessionSante/FHIR/TRE-G15-ProfessionSante`
- **Common Codes**:
  - `60` - Médecin généraliste
  - `40` - Kinésithérapeute  
  - `50` - Ostéopathe
  - `86` - Dentiste
  - `31` - Sage-femme
  - `96` - Pharmacien
  - `23` - Infirmier

### Example Queries
```
GET /PractitionerRole?role=60  # General practitioners
GET /PractitionerRole?role=40  # Physiotherapists
```

### Response Structure
```json
{
  "id": "role-id",
  "active": true,
  "practitioner": {"reference": "Practitioner/id", "display": null}, // Often null, need to fetch separately
  "organization": {"reference": "Organization/id", "display": "Org Name"},
  "code": [{
    "coding": [
      {"system": "https://mos.esante.gouv.fr/NOS/TRE-G15-ProfessionSante/FHIR/TRE-G15-ProfessionSante", "code": "40"},
      {"system": "https://mos.esante.gouv.fr/NOS/TRE_R09-CategorieProfessionnelle/FHIR/TRE-R09-CategorieProfessionnelle", "code": "C"}
    ]
  }]
}
```

**Note**: Practitioner display names are often null in PractitionerRole responses. Use the `role` parameter for filtering by profession.

---

## 3. Practitioner Resource

**Endpoint**: `/Practitioner`

### Search Parameters
- `family` - Family name (surname)
- `given` - Given name (first name)
- `name` - Any name (family or given)
- `identifier` - Professional identifier (RPPS, ADELI)
- `active` - Active status
- `_count` - Number of results

### Example Queries
```
GET /Practitioner?family=Dupont
GET /Practitioner?given=Jean
GET /Practitioner?name=Jean Dupont
```

### Response Structure
```json
{
  "id": "practitioner-id",
  "active": true,
  "name": [{
    "family": "Dupont",
    "given": ["Jean"],
    "prefix": ["Dr."]
  }],
  "identifier": [{
    "system": "http://fhir.fr/fhir/core/NamingSystem/rpps",
    "value": "12345678901"
  }]
}
```

---

## 4. HealthcareService Resource

**Endpoint**: `/HealthcareService`

### Search Parameters
- `organization` - Reference to Organization
- `location` - Reference to Location
- `service-category` - Service category
- `service-type` - Specific service type
- `active` - Active status
- `_count` - Number of results

### Example Queries
```
GET /HealthcareService?service-category=emergency
GET /HealthcareService?organization=Organization/123
```

---

## 5. Device Resource

**Endpoint**: `/Device`

### Search Parameters
- `organization` - Reference to Organization
- `location` - Reference to Location
- `type` - Device type
- `status` - Device status
- `_count` - Number of results

---

## Search Strategy Guidelines

### For User Queries:

1. **"Find doctors by name"** → Use `Practitioner` resource with `name` parameter
2. **"Find specialists in a city"** → Use `PractitionerRole` with `role` + location filtering
3. **"Find hospitals/clinics"** → Use `Organization` with `type` and location parameters
4. **"Find specific services"** → Use `HealthcareService` resource
5. **"Find medical equipment"** → Use `Device` resource

### Location Filtering Strategy:
- Use `address-city` for city-based searches
- Use `address-postalcode` for precise location searches
- Convert Paris arrondissements: "16e" → "75016"

### Profession Code Mapping:
```javascript
const PROFESSION_CODES = {
  "généraliste": "60", "médecin": "60", "general practitioner": "60",
  "kinésithérapeute": "40", "kiné": "40", "physiotherapist": "40",
  "ostéopathe": "50", "osteopath": "50",
  "dentiste": "86", "dentist": "86",
  "sage-femme": "31", "midwife": "31",
  "pharmacien": "96", "pharmacist": "96",
  "infirmier": "23", "nurse": "23"
};
```

### Error Handling:
- Status 400: Invalid parameters
- Status 404: Resource not found
- Status 429: Rate limiting
- Timeout: Network issues

### Best Practices:
1. Always include `_count` parameter to limit results
2. Use specific parameters when possible (avoid broad searches)
3. Implement local filtering for complex queries
4. Cache results when appropriate
5. Handle pagination with `next` links in bundle responses

---

## Implementation Notes

- **Organization searches**: Work well with city and name parameters
- **PractitionerRole searches**: Use `role` parameter with profession codes
- **Practitioner searches**: Best for name-based searches
- **Geographic filtering**: Use postal codes when possible, fall back to city names
- **Specialty mapping**: Convert natural language to profession codes before API calls
