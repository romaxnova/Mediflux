from fastapi import APIRouter, Request, HTTPException
import requests

router = APIRouter()
FHIR_BASE_URL = "https://gateway.api.esante.gouv.fr/fhir/Organization"
API_KEY = "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740"

@router.post("/v1/context")
async def mcp_context(request: Request):
    """
    Accepts: { "query": "last 3 CABINET D'OSTEOPATHIE in 75003" }
    Returns: { "context": [ ... ] }
    """
    data = await request.json()
    query = data.get("query", "")
    # Simple extraction (for demo, improve with NLP for production)
    name = None
    postal_code = None
    import re
    # Extract postal code (5 digits)
    m = re.search(r"\\b(\\d{5})\\b", query)
    if m:
        postal_code = m.group(1)
    # Extract name (naive: look for quoted or after 'CABINET')
    m = re.search(r"CABINET\\s+([\\w' ]+)", query, re.IGNORECASE)
    if m:
        name = "CABINET " + m.group(1).strip()
    # Fallback: look for 'OSTEOPATHIE'
    if not name and "OSTEOPATHIE" in query.upper():
        name = "OSTEOPATHIE"
    params = {}
    if name:
        params["name"] = name
    if postal_code:
        params["address-postalcode"] = postal_code
    headers = {"ESANTE-API-KEY": API_KEY}
    try:
        resp = requests.get(FHIR_BASE_URL, params=params, headers=headers)
        resp.raise_for_status()
        bundle = resp.json()
        # Sort by lastUpdated, get last 3
        orgs = sorted(
            bundle.get("entry", []),
            key=lambda e: e["resource"].get("meta", {}).get("lastUpdated", ""),
            reverse=True
        )[:3]
        context = [
            {
                "id": org["resource"].get("id"),
                "name": org["resource"].get("name"),
                "lastUpdated": org["resource"].get("meta", {}).get("lastUpdated"),
                "address": org["resource"].get("address", [{}])[0].get("text"),
                "type": org["resource"].get("type", [{}])[0].get("text"),
                "active": org["resource"].get("active"),
            }
            for org in orgs
        ]
        return {"context": context}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"MCP Organization API call failed: {str(e)}")
