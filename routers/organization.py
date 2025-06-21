from fastapi import APIRouter, HTTPException, Query
import requests

router = APIRouter()
FHIR_BASE_URL = "https://gateway.api.esante.gouv.fr/fhir/Organization"
API_KEY = "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740"

@router.get("/search")
def search_organizations(
    name: str = Query(None, description="Organization name fragment"),
    postal_code: str = Query(None, alias="address-postalcode", description="Postal code")
):
    params = {}
    if name:
        params["name"] = name
    if postal_code:
        params["address-postalcode"] = postal_code
    headers = {"ESANTE-API-KEY": API_KEY}
    try:
        response = requests.get(FHIR_BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Organization API call failed: {str(e)}")

@router.get("/{org_id}")
def get_organization(org_id: str):
    headers = {"ESANTE-API-KEY": API_KEY}
    try:
        response = requests.get(f"{FHIR_BASE_URL}/{org_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Organization API call failed: {str(e)}")
