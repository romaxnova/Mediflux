# Mediflux V2 - Healthcare Journey Orchestrator

## Overview

Mediflux V2 is a lean, patient-centric healthcare orchestrator that streamlines healthcare journeys by simulating reimbursements, optimizing care paths, and analyzing documents. Built with AI agents for natural interactions, it emphasizes efficiency, cost transparency, and system optimization without replicating traditional booking platforms.

### Key Features

🔍 **Document Analyzer**: OCR-powered analysis of French healthcare documents (carte tiers payant, feuilles de soins)  
💰 **Reimbursement Simulator**: Personalized cost estimates based on user profile and mutuelle coverage  
🗺️ **Care Pathway Advisor**: AI-driven recommendations for optimal healthcare sequences  
🤖 **Conversational Interface**: Natural language interaction with specialized healthcare AI agents

## Architecture

### Modular Microservices Design
- **Data Hub Module**: ETL pipeline for healthcare data sources (SQLite storage)
- **AI Orchestrator Module**: Main agent with RAG capabilities for context-aware responses  
- **Document Analyzer Sub-Agent**: Specialized OCR and rule-based extraction
- **Memory Optimizer**: Efficient user profile and session management
- **Frontend Module**: Hybrid chat interface with dynamic visualizations

### Technology Stack
- **Backend**: Python (FastAPI), SQLite, Tesseract OCR
- **Frontend**: React, TypeScript, Vite
- **AI/ML**: X API (dev), local Mixtral LLM (production)
- **Data Processing**: Pandas, BeautifulSoup, FAISS for vector embeddings

```
v2/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── core_orchestration/     # AI agents and orchestration
│   ├── document_analyzer/      # OCR and extraction logic
│   └── tests/                  # Test suite
├── agentic_user_interface/     # React frontend
├── data/                       # Healthcare datasets
└── docs/                       # Documentation
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Tesseract OCR
- Git

### Local Development

1. **Clone and setup backend**:
```bash
git clone https://github.com/romaxnova/Mediflux.git
cd Mediflux/v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Install Tesseract OCR**:
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-fra

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

3. **Setup frontend**:
```bash
cd agentic_user_interface
npm install
```

4. **Environment Configuration**:
```bash
# Copy example environment file
cp .env.example .env

# Configure your settings:
# - X_API_KEY for AI services
# - DATABASE_URL for SQLite
# - UPLOAD_PATH for document storage
```

5. **Run the application**:
```bash
# Terminal 1: Backend
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend  
cd agentic_user_interface
npm run dev
```

6. **Access the application**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
## Deployment

### Local Production

1. **Build frontend**:
```bash
cd agentic_user_interface
npm run build
```

2. **Run with production settings**:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Web Hosting (Render/Railway/Heroku)

1. **Prepare for deployment**:
```bash
# Ensure requirements.txt includes all dependencies
pip freeze > requirements.txt

# Configure runtime
echo "python-3.9.0" > runtime.txt
```

2. **Render Deployment**:
   - Connect GitHub repository
   - Build Command: `pip install -r requirements.txt && cd agentic_user_interface && npm install && npm run build`
   - Start Command: `python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Set required environment variables

3. **Docker Deployment**:
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Data Sources Integration

### Integrated Sources
- **Open Medic**: Regional reimbursement aggregates (CSV, annual refresh)
- **Annuaire Santé CNAM**: Healthcare provider data (FHIR API, monthly refresh)  
- **API BDPM**: Medication database (GraphQL, real-time)
- **Odissé**: Healthcare access metrics (API v2.1, daily refresh)

### Data Flow
User Input → AI Orchestrator → RAG Query → Data Hub Tool Call → Enriched Response

## User Journeys

### 1. Reimbursement Simulation
Upload prescription or chat about medication costs → Get personalized cost breakdown with generic alternatives

### 2. Care Pathway Optimization  
Ask "Best path for chronic back pain near Paris" → Receive optimized sequence considering cost, wait times, and preferences

### 3. Document Analysis
Upload carte tiers payant → Get coverage explanation and integration with user profile

## Development

### Running Tests
```bash
# Backend tests
python -m pytest src/tests/

# Frontend tests  
cd agentic_user_interface
npm test
```

### Code Quality
```bash
# Linting
flake8 src/
cd agentic_user_interface && npm run lint

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Known Issues

- BDPM GraphQL API occasionally returns 503 errors (external dependency)
- OCR table extraction needs optimization for some document formats
- See [v2issues.md](docs/v2issues.md) and [v2todo.md](v2todo.md) for detailed status

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For questions or support, please open an issue on GitHub or contact the development team.

---

**MVP Target**: 4-6 weeks to prototype with focus on reimbursement simulation, care path optimization, and document analysis.

**Week 3**: Care pathway advisor, memory store, Odissé integration
- Local AI (Mixtral) integration
- Regional optimization algorithms
- Advanced pathway recommendations

**Week 4**: Testing, debugging, frontend prototype
- Web interface development
- Comprehensive test coverage
- Performance optimization

### 🏥 Example Usage

```python
from orchestrator import MedifluxOrchestrator

orchestrator = MedifluxOrchestrator()

# Cost simulation
result = await orchestrator.process_query(
    "Combien coûte le Doliprane avec ma mutuelle?", 
    user_id="patient_123"
)

# Care pathway
pathway = await orchestrator.process_query(
    "Parcours de soins pour mal de dos chronique",
    user_id="patient_123"  
)

# Document analysis  
doc_result = await orchestrator.upload_document(
    "carte_vitale.jpg", 
    "carte_tiers_payant",
    user_id="patient_123"
)
```

### 📈 Differentiators

**vs. Doctolib**: Focus on care optimization and cost transparency, not booking  
**vs. Ameli**: Patient-centric with mutuelle integration and regional insights  
**vs. Generic AI**: Healthcare-specific with French regulatory compliance  

### 🛠️ Technology Stack

- **Backend**: Python 3.8+ with asyncio
- **Database**: SQLite for local storage  
- **APIs**: FHIR, GraphQL, REST integration
- **AI**: Rule-based + local LLM (Mixtral)
- **OCR**: Tesseract (planned)
- **Frontend**: React/Streamlit (planned)

---

*Built with modularity, privacy, and patient empowerment in mind.*
