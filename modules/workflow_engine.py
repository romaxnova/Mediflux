"""
LangChain Workflow Engine for Complex Healthcare Processes
Implements chains and workflows for multi-step healthcare journeys
Uses XAI (Grok) API for French healthcare optimization
"""

import os
import logging
from typing import Dict, List, Any, Optional, Sequence
from datetime import datetime
from dotenv import load_dotenv

from langchain.chains import LLMChain, SequentialChain
from langchain.chains.base import Chain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

# Import existing modules
from .memory.store import MemoryStore
from .care_pathway.advisor import CarePathwayAdvisor
from .data_hub.bdpm import BDPMClient
from .data_hub.annuaire import AnnuaireClient
from .reimbursement.simulator import ReimbursementSimulator


class HealthcareWorkflowEngine:
    """
    Advanced workflow engine for complex healthcare processes
    Uses LangChain chains to orchestrate multi-step journeys
    """
    
    def __init__(self):
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        
        # Use XAI (Grok) API if available, fallback to OpenAI
        self.xai_api_key = os.getenv("XAI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.xai_api_key:
            # Configure for XAI (Grok)
            self.llm = ChatOpenAI(
                model="grok-2",
                temperature=0.3,
                api_key=self.xai_api_key,
                base_url="https://api.x.ai/v1"
            )
            self.logger.info("Using XAI (Grok) API for workflow engine")
        elif self.openai_api_key:
            # Fallback to OpenAI
            self.llm = ChatOpenAI(
                model="gpt-4-0125-preview",
                temperature=0.3,
                api_key=self.openai_api_key
            )
            self.logger.info("Using OpenAI API for workflow engine")
        else:
            # No API key available - create a mock LLM for development
            self.llm = None
            self.logger.warning("No LLM API key found - workflow engine in mock mode")
        
        # Initialize existing modules
        self.memory_store = MemoryStore()
        self.care_pathway_advisor = CarePathwayAdvisor()
        self.bdpm_client = BDPMClient()
        self.annuaire_client = AnnuaireClient()
        self.reimbursement_simulator = ReimbursementSimulator()
        
        # Initialize workflow chains
        self.workflows = self._create_workflows()
    
    def _create_workflows(self) -> Dict[str, Chain]:
        """Create specialized workflow chains"""
        
        workflows = {}
        
        # Workflow 1: Complete Medication Analysis
        workflows["medication_analysis"] = self._create_medication_workflow()
        
        # Workflow 2: Care Pathway with Cost Optimization
        workflows["pathway_optimization"] = self._create_pathway_workflow()
        
        # Workflow 3: Comprehensive Health Journey Planning
        workflows["health_journey"] = self._create_health_journey_workflow()
        
        # Workflow 4: Document Analysis and Integration
        workflows["document_integration"] = self._create_document_workflow()
        
        return workflows
    
    def _create_medication_workflow(self) -> SequentialChain:
        """Create medication analysis workflow"""
        
        # Step 1: Extract medication information
        extract_prompt = PromptTemplate(
            input_variables=["query"],
            template="""Analyse cette demande sur un médicament et extrait les informations clés :

Demande utilisateur : {query}

Extrait :
- Nom du médicament exact
- Information recherchée (prix, effet, alternative, etc.)
- Contexte médical si mentionné
- Urgence de la demande

Format de réponse :
Médicament: [nom]
Type de recherche: [prix/info/alternative]
Contexte: [contexte ou "non spécifié"]
Urgence: [normale/élevée]"""
        )
        
        extract_chain = LLMChain(
            llm=self.llm,
            prompt=extract_prompt,
            output_key="extraction"
        )
        
        # Step 2: Database lookup simulation
        lookup_prompt = PromptTemplate(
            input_variables=["extraction"],
            template="""Basé sur cette extraction d'informations médicament :

{extraction}

Simule une recherche dans la base BDPM française :
- Prix public si demandé
- Statut de commercialisation
- Alternatives génériques disponibles
- Taux de remboursement de base

Réponse structurée avec données simulées réalistes."""
        )
        
        lookup_chain = LLMChain(
            llm=self.llm,
            prompt=lookup_prompt,
            output_key="database_info"
        )
        
        # Step 3: Cost calculation
        cost_prompt = PromptTemplate(
            input_variables=["database_info"],
            template="""Avec ces informations BDPM :

{database_info}

Calcule les coûts détaillés :
- Prix public total
- Remboursement Sécurité Sociale (65% ou 35%)
- Estimation complémentaire mutuelle
- Reste à charge patient
- Alternatives économiques

Fournis un tableau de coûts clair et actionnable."""
        )
        
        cost_chain = LLMChain(
            llm=self.llm,
            prompt=cost_prompt,
            output_key="cost_analysis"
        )
        
        # Combine into sequential workflow
        return SequentialChain(
            chains=[extract_chain, lookup_chain, cost_chain],
            input_variables=["query"],
            output_variables=["extraction", "database_info", "cost_analysis"],
            verbose=True
        )
    
    def _create_pathway_workflow(self) -> SequentialChain:
        """Create care pathway optimization workflow"""
        
        # Step 1: Medical condition analysis
        condition_prompt = PromptTemplate(
            input_variables=["query", "user_profile"],
            template="""Analyse cette demande de parcours de soins :

Demande : {query}
Profil utilisateur : {user_profile}

Identifie :
- Condition médicale principale
- Symptômes ou besoins exprimés
- Urgence clinique estimée
- Contraintes géographiques
- Préférences coût/qualité

Analyse médicale structurée."""
        )
        
        condition_chain = LLMChain(
            llm=self.llm,
            prompt=condition_prompt,
            output_key="condition_analysis"
        )
        
        # Step 2: Pathway generation
        pathway_prompt = PromptTemplate(
            input_variables=["condition_analysis"],
            template="""Basé sur cette analyse médicale :

{condition_analysis}

Génère un parcours de soins optimisé selon les guidelines HAS :
- Étape 1 : Médecin traitant (obligatoire)
- Étapes suivantes selon condition
- Timing et urgence de chaque étape
- Spécialistes recommandés
- Examens complémentaires éventuels

Parcours détaillé et justifié."""
        )
        
        pathway_chain = LLMChain(
            llm=self.llm,
            prompt=pathway_prompt,
            output_key="pathway_plan"
        )
        
        # Step 3: Resource optimization
        optimization_prompt = PromptTemplate(
            input_variables=["pathway_plan", "user_profile"],
            template="""Avec ce parcours de soins :

{pathway_plan}

Et ce profil utilisateur :
{user_profile}

Optimise les ressources :
- Praticiens secteur 1 vs secteur 2
- Délais d'attente régionaux
- Alternatives géographiques
- Optimisation coût total
- Conseils pratiques

Plan optimisé avec recommandations concrètes."""
        )
        
        optimization_chain = LLMChain(
            llm=self.llm,
            prompt=optimization_prompt,
            output_key="optimized_pathway"
        )
        
        return SequentialChain(
            chains=[condition_chain, pathway_chain, optimization_chain],
            input_variables=["query", "user_profile"],
            output_variables=["condition_analysis", "pathway_plan", "optimized_pathway"],
            verbose=True
        )
    
    def _create_health_journey_workflow(self) -> SequentialChain:
        """Create comprehensive health journey planning workflow"""
        
        # Step 1: Journey scoping
        scope_prompt = PromptTemplate(
            input_variables=["query", "user_context"],
            template="""Analyse cette demande de parcours santé global :

Demande : {query}
Contexte utilisateur : {user_context}

Définis le scope du journey :
- Objectifs santé court/moyen/long terme
- Priorités et contraintes
- Ressources disponibles
- Timeline souhaité
- Facteurs de succès

Cadrage du parcours santé."""
        )
        
        scope_chain = LLMChain(
            llm=self.llm,
            prompt=scope_prompt,
            output_key="journey_scope"
        )
        
        # Step 2: Multi-dimensional planning
        planning_prompt = PromptTemplate(
            input_variables=["journey_scope"],
            template="""Avec ce scope de parcours santé :

{journey_scope}

Planifie un journey multi-dimensionnel :

MÉDICAL :
- Consultations et suivis
- Examens et dépistages
- Traitements et thérapies

ADMINISTRATIF :
- Démarches remboursements
- Dossiers et documents
- Droits et aides

LOGISTIQUE :
- Planning et organisation
- Transport et accompagnement
- Outils et ressources

Plan intégré avec timeline."""
        )
        
        planning_chain = LLMChain(
            llm=self.llm,
            prompt=planning_prompt,
            output_key="comprehensive_plan"
        )
        
        # Step 3: Actionable roadmap
        roadmap_prompt = PromptTemplate(
            input_variables=["comprehensive_plan"],
            template="""Avec ce plan complet :

{comprehensive_plan}

Crée une roadmap actionnable :
- Actions immédiates (semaine 1)
- Étapes à court terme (mois 1)
- Objectifs moyen terme (3-6 mois)
- Suivi et ajustements
- Métriques de succès
- Points de validation

Roadmap concrète avec next steps."""
        )
        
        roadmap_chain = LLMChain(
            llm=self.llm,
            prompt=roadmap_prompt,
            output_key="actionable_roadmap"
        )
        
        return SequentialChain(
            chains=[scope_chain, planning_chain, roadmap_chain],
            input_variables=["query", "user_context"],
            output_variables=["journey_scope", "comprehensive_plan", "actionable_roadmap"],
            verbose=True
        )
    
    def _create_document_workflow(self) -> SequentialChain:
        """Create document analysis and integration workflow"""
        
        # Step 1: Document classification
        classify_prompt = PromptTemplate(
            input_variables=["document_type", "extracted_text"],
            template="""Analyse ce document de santé français :

Type de document : {document_type}
Texte extrait : {extracted_text}

Classification :
- Type exact (carte vitale, carte tiers payant, ordonnance, etc.)
- Émetteur (CPAM, mutuelle, médecin, etc.)
- Informations clés contenues
- Statut et validité
- Actions possibles

Analyse structurée du document."""
        )
        
        classify_chain = LLMChain(
            llm=self.llm,
            prompt=classify_prompt,
            output_key="document_classification"
        )
        
        # Step 2: Data extraction
        extract_prompt = PromptTemplate(
            input_variables=["document_classification", "extracted_text"],
            template="""Avec cette classification :

{document_classification}

Et ce texte source :
{extracted_text}

Extrait les données structurées :
- Identifiants (numéros, codes)
- Dates (validité, émission)
- Montants et taux
- Bénéficiaires et ayants droit
- Conditions et exclusions

Données extraites en format structuré."""
        )
        
        extract_data_chain = LLMChain(
            llm=self.llm,
            prompt=extract_prompt,
            output_key="structured_data"
        )
        
        # Step 3: Integration recommendations
        integration_prompt = PromptTemplate(
            input_variables=["structured_data", "user_profile"],
            template="""Avec ces données extraites :

{structured_data}

Et ce profil existant :
{user_profile}

Recommande l'intégration :
- Mise à jour du profil utilisateur
- Nouveaux services disponibles
- Optimisations possibles
- Actions recommandées
- Alertes ou notifications

Plan d'intégration avec next steps."""
        )
        
        integration_chain = LLMChain(
            llm=self.llm,
            prompt=integration_prompt,
            output_key="integration_plan"
        )
        
        return SequentialChain(
            chains=[classify_chain, extract_data_chain, integration_chain],
            input_variables=["document_type", "extracted_text", "user_profile"],
            output_variables=["document_classification", "structured_data", "integration_plan"],
            verbose=True
        )
    
    async def execute_workflow(self, workflow_name: str, **inputs) -> Dict[str, Any]:
        """Execute a specific workflow"""
        
        if workflow_name not in self.workflows:
            return {
                "success": False,
                "error": f"Workflow '{workflow_name}' not found",
                "available_workflows": list(self.workflows.keys())
            }
        
        try:
            self.logger.info(f"Executing workflow: {workflow_name}")
            
            workflow = self.workflows[workflow_name]
            result = await workflow.arun(**inputs)
            
            return {
                "success": True,
                "workflow": workflow_name,
                "result": result,
                "executed_at": datetime.now().isoformat(),
                "inputs": inputs
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution error: {str(e)}")
            return {
                "success": False,
                "workflow": workflow_name,
                "error": str(e),
                "inputs": inputs
            }
    
    async def execute_medication_journey(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Execute complete medication analysis journey"""
        
        # Get user context
        user_context = await self.memory_store.get_user_context(user_id)
        
        result = await self.execute_workflow(
            "medication_analysis",
            query=query
        )
        
        # Store results in user memory
        if result.get("success"):
            await self.memory_store.update_session_history(
                user_id,
                query,
                {"workflow_result": result}
            )
        
        return result
    
    async def execute_pathway_journey(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Execute care pathway optimization journey"""
        
        # Get user context
        user_context = await self.memory_store.get_user_context(user_id)
        user_profile = user_context.get("profile", {})
        
        result = await self.execute_workflow(
            "pathway_optimization",
            query=query,
            user_profile=str(user_profile)
        )
        
        # Store results in user memory
        if result.get("success"):
            await self.memory_store.update_session_history(
                user_id,
                query,
                {"workflow_result": result}
            )
        
        return result
    
    async def execute_health_journey(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Execute comprehensive health journey planning"""
        
        # Get user context
        user_context = await self.memory_store.get_user_context(user_id)
        
        result = await self.execute_workflow(
            "health_journey",
            query=query,
            user_context=str(user_context)
        )
        
        # Store results in user memory
        if result.get("success"):
            await self.memory_store.update_session_history(
                user_id,
                query,
                {"workflow_result": result}
            )
        
        return result
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows"""
        return list(self.workflows.keys())
    
    async def get_workflow_status(self, user_id: str = "default") -> Dict[str, Any]:
        """Get status of workflows for a user"""
        
        try:
            user_context = await self.memory_store.get_user_context(user_id)
            session_history = user_context.get("session_history", [])
            
            workflow_sessions = [
                session for session in session_history
                if "workflow_result" in session.get("response", {})
            ]
            
            return {
                "user_id": user_id,
                "total_sessions": len(session_history),
                "workflow_sessions": len(workflow_sessions),
                "last_workflow": workflow_sessions[-1] if workflow_sessions else None,
                "available_workflows": self.get_available_workflows()
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "error": str(e),
                "available_workflows": self.get_available_workflows()
            }
