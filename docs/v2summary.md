### Mediflux MVP Plan

### **Overview**

The MVP focuses on a lean, patient-centric orchestrator that streamlines healthcare journeys by simulating reimbursements, optimizing care paths, and analyzing documents—all without replicating Doctolib-like booking. It leverages AI agents for natural interactions, emphasizing efficiency, cost transparency, and system savings (e.g., reducing affluences via informed routing). Built with modularity for easy debugging, zero-cost data integrations, and local AI (e.g., Mixtral) to minimize expenses. Target: 4-6 weeks to prototype, with hybrid UI (chat + visualizations). Core tech stack: Python (FastAPI for backend), SQLite for local storage, React for frontend, and X API for agents/RAG (in prod we will use a local open source LLM).

### **Architecture**

Modular microservices design for isolation and debugging:

*   **Data Hub Module**: Central ETL pipeline (Python scripts with Pandas/BeautifulSoup) for scraping/parsing/storing data sources in SQLite. Cron jobs for daily/weekly refreshes. Outputs structured JSON for quick queries.
    
*   **AI Orchestrator Module**: Main agent (X API for dev, local Mixtral LLM for prod) with RAG (using FAISS for vector embeddings of user context/documents + pre-loaded reimbursement rules). Handles user queries, tool calls (e.g., to data hub or sub-agents), and context management.
    
*   **Document Analyzer Sub-Agent**: Specialized lightweight agent (pre-prompted LLM instance) for parsing uploads (e.g., carte tiers payant via Tesseract OCR + rule-based extraction). Outputs to RAG store.
    
*   **Memory Optimizer**: Efficient storage in SQLite (key-value pairs for user profiles: e.g., {user\_id: {mutuelle\_type: "AXA Basic", pathology: "chronic back pain", preferences: "low-cost public"}}). Summarize sessions (e.g., via LLM) to compress data; purge after 30 days or user consent. Use session tokens for stateless API calls.
    
*   **Frontend Module**: Hybrid interface—conversational chat (WebSocket-based) + dynamic visualizations (e.g., Dash/Plotly for cost charts, care path maps). Backend exposes REST endpoints for modularity.
    
*   **Deployment**: Local/serverless (e.g., Docker) for MVP; debug via logging (e.g., ELK-lite) per module.
    

This setup ensures feasibility: No cloud costs, modular tests (e.g., unit-test data hub independently), and scalable RAG for context-aware responses.

### **Features**

Prioritize 3 core features for instant utility, avoiding overcomplexity:

1.  **Reimbursement Simulator**: Estimates out-of-pocket costs based on user profile, pathology, and mutuelle—integrates document analysis for personalized calcs.
    
2.  **Optimized Care Pathway Advisor**: Suggests informed care sequences (e.g., "Start with GP consult, then low-affluence specialist") tailored to profile/preferences, using aggregated data for efficiency (not individual bookings).
    
3.  **Document Analyzer**: Parses uploads (e.g., carte tiers payant, feuilles de soins) to extract/explain coverage, feeding into simulations/advice.
    

### **Approach to Data Source Integration**

Integrate via Data Hub for offline-first access (cache locally, query live if needed). Updated to emphasize unique value: Aggregate/analyze for informed paths, not listings.

*   **Open Medic (CSV, annual refresh)**: Parse for regional reimbursement aggregates (e.g., avg costs by age/pathology). Use in simulator for baseline estimates (e.g., "Chronic meds: 70% reimbursed in your region").
    
*   **Annuaire Santé de la CNAM (FHIR API/CSV, monthly refresh)**: Aggregate for path optimization—e.g., compute avg tariffs/sectors by specialty/region (not list individuals). Combine with user profile (e.g., "For your mutuelle, prioritize sector 1 GPs in low-tariff areas"). Differentiates from Doctolib by focusing on sequence advice (e.g., "Public path saves €50 vs. private").
    
*   **API BDPM GraphQL (Live queries)**: Real-time lookups for med details/reimbursement bases. Integrate into analyzer/simulator (e.g., match extracted drug codes to rates/generics).
    
*   **DREES Datasets (CSV, annual refresh)**: Parse for specialist density, wait times, and access statistics by region/territory. Use for affluence ratios and pathway optimization (e.g., "Low-density specialist area, expect 10-day wait vs. 3-day in high-density zones").
    
*   **ScanSanté ATIH (CSV/API, weekly refresh)**: Hospital indicators including wait times, activity volumes, and market shares by facility/region. Enable routing to less congested facilities (e.g., "Hospital A has 20% shorter ER waits than Hospital B").
    
*   **IQSS Quality Indicators (CSV, annual refresh)**: Care quality metrics including patient satisfaction and safety scores. Enhance pathway recommendations by factoring quality alongside efficiency (e.g., "High-quality, moderate-wait option available").
    

Integration flow: User input → Orchestrator RAG query → Tool call to Data Hub → Enrich response. Test: Scripted prototypes (e.g., query Odissé API for "density in Paris" and parse JSON).

### **Desired User Journeys, Workflows, and Interface Suggestions**

**Journey 1: Reimbursement Simulation for Prescription (Focus: Cost Transparency)**

*   **User Flow**: User chats "Estimate cost for my back pain meds" or uploads feuille de soins/carte tiers payant.
    
*   **App Workflow**: 1) Orchestrator captures input, retrieves stored profile (e.g., mutuelle/pathology from memory). 2) Calls Document Analyzer sub-agent (OCR + pre-prompt: "Extract drugs, coverage tiers"). 3) Queries Data Hub (BDPM for rates, Open Medic for regional avgs). 4) RAG enriches with context (e.g., "User prefers generics"). 5) Returns summary + vis.
    
*   **Interface**: Chat bubble: "Based on your AXA mutuelle and chronic status: €15 out-of-pocket (70% Secu-covered)." Visualization pane: Pie chart of cost breakdown + generic alternatives list. Button: "Save to profile."
    

**Journey 2: Optimized Care Path Advice (Focus: Informed Routing)**

*   **User Flow**: User asks "Best path for chronic back pain treatment near Paris, low-cost preference."
    
*   **App Workflow**: 1) Orchestrator pulls profile/preferences from memory. 2) Tool calls: Odissé API for affluence/wait times; Annuaire Santé aggregate for tariff sectors by specialty. 3) Analyzes (e.g., score paths: GP → low-affluence physio → specialist). 4) Simulates costs via Open Medic/BDPM. 5) Stores summary in memory for future chats.
    
*   **Interface**: Chat response: "Suggested path: Start with sector 1 GP (avg wait 5 days, €23), then physio in under-afflued area." Vis pane: Flowchart/map of steps with cost/affluence badges. Toggle: "Adjust for private options."
    

**Journey 3: Document Upload and Analysis (Focus: Bureaucracy Reduction)**

*   **User Flow**: User uploads carte tiers payant and asks "What does this cover for dentistry?"
    
*   **App Workflow**: 1) Sub-agent parses (OCR → extract tiers, exclusions). 2) Orchestrator RAG-integrates with profile/pathology. 3) Cross-references Data Hub (e.g., BDPM for dental meds, Open Medic for avgs). 4) Generates explanation + simulation. 5) Compresses/summarizes to memory (e.g., key: "dental\_coverage: 80%").
    
*   **Interface**: Upload button in chat; response: "Your mutuelle covers 80% for checkups." Vis: Highlighted PDF with annotations + table of covered acts. Save prompt: "Add to profile?"
    

This MVP delivers unique value through AI-orchestrated, profile-aware insights, ensuring feasibility with modular components and efficient memory.Sources

**Interface Suggestions**
-------------------------

*   **Main Split:** Chat (conversation with orchestrator) + data/visual panel (for simulation outputs, pathway visuals, contract summaries).
    
*   **Drag-and-Drop Area:** For uploading docs (carte, feuilles de soins).
    
*   **Context Panel:** Quick reference to current “coverage context” (summarized in 1-2 lines, expandable).
    
*   **Efficient Data Summaries:** Clicking on any piece of data shows recent sources or analysis explanation.
    
*   **Privacy Controls:** Visible to user, easy data clearing/export.
    
