from fastapi import FastAPI
from routers import sante, geocode, fhir_public, organization, mcp_organization

app = FastAPI(title="Mediflux API")

# Include routers
app.include_router(sante.router, prefix="/api/sante")
# Add direct proxy for practitionerrole/search for MCP compatibility
app.include_router(sante.router, prefix="/api")
app.include_router(geocode.router, prefix="/api/geocode")
app.include_router(fhir_public.router, prefix="/api/fhir-public")
app.include_router(organization.router, prefix="/api/organization")
app.include_router(mcp_organization.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Mediflux API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
