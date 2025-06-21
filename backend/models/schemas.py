from pydantic import BaseModel

class MedecinResponse(BaseModel):
    id: int
    nom: str
    specialite: str
    adresse: str
    coordinates: dict