# Mediflux V2

## Patient-Centric Healthcare Orchestration Platform

Mediflux V2 is a modular, lightweight healthcare orchestration system designed to optimize patient care pathways, simulate reimbursement costs, and provide intelligent healthcare guidance through AI-powered query interpretation.

### 🏗️ Architecture

**Modular Design**: Each component is independent, testable, and focused on a specific healthcare domain.

```
v2/
├── modules/
│   ├── orchestrator.py          # Main coordinator with intent routing
│   ├── interpreter/             # Query interpretation & intent routing
│   ├── memory/                  # User profiles & session management
│   ├── data_hub/               # External data source integrations
│   │   ├── bdpm.py             # French medication database
│   │   ├── annuaire.py         # Healthcare directory (FHIR)
│   │   ├── odisse.py           # Regional healthcare metrics
│   │   └── open_medic.py       # Medication reimbursement trends
│   ├── reimbursement/          # Cost simulation & breakdown
│   ├── document_analyzer/      # OCR & healthcare document parsing
│   └── care_pathway/           # Intelligent care sequence optimization
├── data/                       # Local SQLite storage & cache
├── frontend/                   # UI components (future)
└── v2*.md                     # Planning & progress documentation
```

### 🚀 Key Features

**Intent-Based Routing**: Natural language queries are automatically routed to appropriate modules
- Cost simulation: "Combien coûte le Doliprane?"
- Care pathways: "Parcours de soins pour diabète"
- Document analysis: "Analyser ma carte tiers payant"
- Practitioner search: "Cardiologue à Paris"

**Reimbursement Simulation**: Real-time cost breakdown with Sécurité Sociale and mutuelle coverage
- Medication costs with generic alternatives
- Consultation fees by practitioner sector
- Regional cost variations
- Savings optimization tips

**Care Pathway Optimization**: Intelligent sequencing of healthcare consultations
- Condition-specific pathways
- Cost and time optimization
- Regional healthcare density integration
- Wait time estimation

**Document Intelligence**: OCR and rule-based extraction for healthcare documents
- Carte tiers payant parsing
- Feuille de soins analysis
- Prescription medication extraction

### 🔧 Quick Start

1. **Install Dependencies**
   ```bash
   cd v2/
   pip install -r requirements.txt
   ```

2. **Run Demo**
   ```bash
   python demo_v2.py
   ```

3. **Test Modules** (Async testing)
   ```bash
   python test_v2.py
   ```

### 🌐 Data Sources

**Real-Time APIs**:
- **BDPM GraphQL**: French medication database with reimbursement rates
- **Annuaire Santé FHIR**: Healthcare practitioner directory
- **Odissé API**: Regional healthcare access indicators

**Batch Processing**:
- **Open Medic CSV**: Historical medication reimbursement trends

### 💾 Privacy & Storage

**Local-First**: All user data stored locally in SQLite
- User profiles with mutuelle and pathology information
- Session history with automatic compression
- GDPR compliance with data export/deletion

**No Cloud Dependencies**: Core functionality works entirely offline after initial data loading

### 🤖 AI Integration

**Hybrid Approach**:
- **Rule-based**: Fast pattern matching for common queries
- **Local AI**: Mixtral fallback for complex interpretations (TODO)
- **No External APIs**: Privacy-preserving on-device processing

### 📊 Current Status (Week 1 Complete)

✅ **Architecture**: Complete modular structure  
✅ **Core Modules**: All 7 modules implemented with async support  
✅ **Data Integration**: 4 data source clients ready  
✅ **User Management**: Privacy-first memory store  
✅ **Cost Simulation**: Full reimbursement calculator  
✅ **Testing**: Demo and test frameworks working  

### 🎯 Next Steps

**Week 2**: Implement simulators, document analyzer, expand data hub
- OCR integration (Tesseract)
- Real API testing and error handling
- Cost calculation refinement

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
