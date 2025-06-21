**Project Description: Modular Healthcare API Orchestrator**

We are building a modular healthcare API orchestrator platform that provides natural language access to multiple French healthcare data sources, with Annuaire Santé API as our initial integration.

**Product Goal:**
- Enable users to input natural language queries such as "find a dermatologue in 75017" or "list clinics in Lyon"
- Implement a robust, extensible orchestrator layer that can intelligently route queries to multiple healthcare APIs and databases
- Maintain a modular architecture where each API integration is encapsulated in its own toolkit or module
- Provide a base agentic user request handling system that interprets user queries, maps them to intents, and orchestrates multi-API workflows
- Ensure consistent data normalization and response aggregation across diverse healthcare data sources

**Current State and Future Vision:**
- Currently integrated with Annuaire Santé API as the primary data source
- Plan to integrate additional public healthcare APIs and databases seamlessly
- The orchestrator and agentic layers form the core foundation, enabling easy addition and management of new APIs

**Cleanup and Architecture Objectives:**
- Organize the codebase into clear modules: core orchestration, agentic user interface, API toolkits, and routers
- Remove redundant or incomplete code to improve maintainability
- Establish clear interfaces and contracts between modules to support independent development
- Prepare the system for scalable growth as new healthcare data sources are added
