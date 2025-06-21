# Mediflux Project

## Overview
This project aims to create a healthcare bureaucracy assistant targeting French administrative challenges.

## Setup Instructions

### 1. API Test
To test the API, use the following command:
```bash
curl -H "ESANTE-API-KEY: b2c9aa48-53c0-4d1b-83f3-7b48a3e26740" "http://localhost:8000/api/sante/medecins?specialite=generaliste&cp=75001"
```

### 2. Frontend Check
To run the frontend, navigate to the frontend directory and start the development server:
```bash
cd frontend && npm run dev
```

### 3. Docker Build
To build and run the Docker container, use the following commands:
```bash
docker build -t mediflux-api .
docker run -p 8000:8000 mediflux-api
```

## Deliverables
- Functional React components with TypeScript interfaces
- FastAPI routes with Pydantic validation
- Dockerfile with Python 3.10 & production-ready config
- Vite proxy setup for seamless frontend-backend communication

## Validation Protocol
- Ensure all components are working as expected by following the setup instructions.