import requests
from fastapi import APIRouter

router = APIRouter()

def get_coordinates(address: str):
    response = requests.get(f'https://api-adresse.data.gouv.fr/search/?q={{address}}')
    return response.json()

@router.get('/geocode')
def geocode(address: str):
    return get_coordinates(address)