Prompt Sequence for V2 Testing & Development
--------------------------------------------

### **Prompt 1: Core Architecture & API Testing**

**Objective**: Verify existing functionality and fix critical issues**Deliverables**:

*   Test V1 migrated components (BDPM, Annuaire Santé) still work after refactoring
    
*   Replace any local LLM references with XAI API calls (maintain V1 approach for development)
    
*   Fix import issues and module connectivity
    
*   Create basic test runner script
    

**Instructions**: "Test all migrated V1 components (BDPM GraphQL, Annuaire Santé FHIR). Ensure the refactored code in data\_hub/bdmp.py and data\_hub/annuaire.py still functions correctly. Remove any local LLM implementations and maintain XAI API usage from V1. Fix all import errors and create a basic test script that validates each module works independently. Update v2progress.md with test results."

### **Prompt 2: Database Architecture Decision**

**Objective**: Choose optimal database solution for development and production**Deliverables**:

*   Evaluate SQLite vs PostgreSQL (NeonDB) for this use case
    
*   Implement chosen database with proper schema
    
*   Create migration scripts if needed
    

**Instructions**: "Analyze database needs for Mediflux V2: user profiles (JSON), session history, cached data from APIs, document analysis results. Compare SQLite vs PostgreSQL (NeonDB available). Consider: development ease, production scalability, JSON support, concurrent access, deployment complexity. Implement the chosen solution with proper schemas for memory store and data caching. Document your choice and reasoning in v2progress.md."

### **Prompt 3: New Data Sources Integration**

**Objective**: Set up and test Odissé API and Open Medic integration**Deliverables**:

*   Working Odissé API connection with relevant datasets
    
*   Open Medic CSV parsing and data storage
    
*   API key management and rate limiting
    

**Instructions**: "Implement and test the two new data sources: 1) Odissé API ([https://odisse.santepubliquefrance.fr/api/explore/v2.1/console](https://odisse.santepubliquefrance.fr/api/explore/v2.1/console)) - focus on 'densities\_professionnels\_sante', 'delais\_rendezvous\_specialistes', 'indicateurs\_acces\_soins' datasets. 2) Open Medic CSV processing from [https://www.data.gouv.fr/datasets/open-medic-base-complete-sur-les-depenses-de-medicaments-interregimes/](https://www.data.gouv.fr/datasets/open-medic-base-complete-sur-les-depenses-de-medicaments-interregimes/). Create data update scripts and test actual API calls. Handle errors and rate limits appropriately."

### **Prompt 4: End-to-End Architecture Testing**

**Objective**: Verify complete workflow functionality**Deliverables**:

*   Integration tests for all user journeys
    
*   Performance benchmarks
    
*   Error handling validation
    

**Instructions**: "Create comprehensive integration tests for the three main user journeys from v2summary.md: 1) Reimbursement simulation (text input and document upload), 2) Care pathway optimization, 3) Document analysis. Test the complete flow: user input → orchestrator → intent router → relevant modules → data hub queries → response generation. Identify bottlenecks and fix integration issues. Measure response times and memory usage."

### **Prompt 5: Frontend Planning & Prototype**

**Objective**: Design UI architecture and create initial prototype**Deliverables**:

*   UI/UX wireframes for hybrid interface (chat + visualizations)
    
*   React frontend architecture plan
    
*   Basic prototype or mockup
    

**Instructions**: "Based on the hybrid interface requirements in v2summary.md (chat + data visualization), design the React frontend architecture. Create wireframes for: 1) Chat interface with document upload, 2) Visualization panels (cost breakdowns, care pathways, document analysis), 3) User profile management. Consider mobile responsiveness and accessibility. Create a basic prototype or detailed mockup showing the three main user journeys. Plan component structure and state management approach."

### **Prompt 6: Production Readiness Assessment**

**Objective**: Prepare for deployment and identify remaining gaps**Deliverables**:

*   Production deployment checklist
    
*   Security audit
    
*   Performance optimization recommendations
    

**Instructions**: "Evaluate V2 for production readiness: 1) Security (GDPR compliance, data encryption, API key management), 2) Performance (database optimization, caching strategy, API rate limiting), 3) Deployment (Docker configuration, environment management, monitoring), 4) Error handling and logging, 5) Documentation and testing coverage. Create a production deployment plan and identify any remaining development tasks needed before launch."