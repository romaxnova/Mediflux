from backend.routers.sante import parse_practitioner_bundle
import requests
import sys
import argparse

url = "https://gateway.api.esante.gouv.fr/fhir/Practitioner"
headers = {"ESANTE-API-KEY": "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740"}

def test_parse_practitioner_bundle():
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        bundle = response.json()
        practitioners = parse_practitioner_bundle(bundle)
        print(practitioners[:3])
    else:
        print(f"Failed: {response.status_code}")

def test_doctor_card():
    print("DoctorCard is a React component. Please run the frontend and test it in the browser.")

def test_doctor_list():
    print("DoctorList is a React component. Please run the frontend and test it in the browser.")

def test_app():
    print("App is a React component. Please run the frontend and test it in the browser.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Mediflux components")
    parser.add_argument("component", choices=["backend", "doctorcard", "doctorlist", "app"], help="Component to test")
    args = parser.parse_args()

    if args.component == "backend":
        test_parse_practitioner_bundle()
    elif args.component == "doctorcard":
        test_doctor_card()
    elif args.component == "doctorlist":
        test_doctor_list()
    elif args.component == "app":
        test_app()
