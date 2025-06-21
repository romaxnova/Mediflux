from fastapi import APIRouter, HTTPException, Query
import requests

FHIR_BASE = "https://gateway.api.esante.gouv.fr/fhir/"
API_KEY = "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740"
HEADERS = {"ESANTE-API-KEY": API_KEY}

router = APIRouter()

@router.get("/devices")
def search_devices(
    manufacturer: str = Query(None, description="Device manufacturer name"),
    model: str = Query(None, description="Device model name"),
    status: str = Query(None, description="Device status (active|inactive|unknown)")
):
    params = {}
    if manufacturer:
        params["manufacturer"] = manufacturer
    if model:
        params["model"] = model
    if status:
        params["status"] = status
    try:
        resp = requests.get(f"{FHIR_BASE}Device", headers=HEADERS, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Device API call failed: {str(e)}")

@router.get("/organizations")
def search_organizations(
    name: str = Query(None, description="Organization name"),
    city: str = Query(None, alias="address-city", description="City in address"),
    postalcode: str = Query(None, alias="address-postalcode", description="Postal code in address")
):
    params = {}
    if name:
        params["name"] = name  # FHIR: Organization-name
    if city:
        params["address-city"] = city  # FHIR: Organization-address-city
    if postalcode:
        params["address-postalcode"] = postalcode  # FHIR: Organization-address-postalcode
    try:
        resp = requests.get(f"{FHIR_BASE}Organization", headers=HEADERS, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Organization API call failed: {str(e)}")
