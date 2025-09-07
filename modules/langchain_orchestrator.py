"""
LangChain-based Orchestrator for Mediflux Healthcare System
Replaces the rule-based intent routing with intelligent LangChain agents
Uses XAI (Grok) API for French healthcare optimization
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI
from langchain.schema import BaseOutputParser

# Import existing modules to wrap as tools
from .memory.store import MemoryStore
from .care_pathway.advisor import CarePathwayAdvisor
from .data_hub.bdpm import BDPMClient
from .data_hub.annuaire import AnnuaireClient
from .reimbursement.simulator import ReimbursementSimulator

import os
import logging
from typing import Dict, List, Any, Optional, Callable
from dotenv import load_dotenv

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool, StructuredTool
from langchain.schema import AgentAction, AgentFinish
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback

# Import existing modules for tool creation
from .memory.store import MemoryStore
from .data_hub.bdpm import BDPMClient
from .data_hub.annuaire import AnnuaireClient
from .data_hub.odisse import OdisseClient
from .care_pathway.advisor import CarePathwayAdvisor
from .reimbursement.simulator import ReimbursementSimulator
from .document_analyzer.handler import DocumentAnalyzer


class LangChainOrchestrator:
    """
    Advanced healthcare orchestrator using LangChain agents and tools
    Provides intelligent reasoning and tool coordination for healthcare workflows
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
            self.logger.info("Using XAI (Grok) API for LangChain orchestration")
        elif self.openai_api_key:
            # Fallback to OpenAI
            self.llm = ChatOpenAI(
                model="gpt-4-0125-preview",
                temperature=0.3,
                api_key=self.openai_api_key
            )
            self.logger.info("Using OpenAI API for LangChain orchestration")
        else:
            # No API key available - create a mock LLM for development
            self.llm = None
            self.logger.warning("No LLM API key found - running in mock mode")
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=True
        )
        
        # Initialize existing modules as tools
        self.memory_store = MemoryStore()
        self.bdpm_client = BDPMClient()
        self.annuaire_client = AnnuaireClient()
        self.odisse_client = OdisseClient()
        self.care_pathway_advisor = CarePathwayAdvisor()
        self.reimbursement_simulator = ReimbursementSimulator()
        self.document_analyzer = DocumentAnalyzer()
        
        # Create tools from existing modules
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List[BaseTool]:
        """Create LangChain tools from existing Mediflux modules"""
        
        tools = []
        
        # BDPM Medication Search Tool
        async def search_medication(query: str, search_type: str = "name") -> str:
            """Search for medication information in BDPM database"""
            try:
                result = await self.bdpm_client.search_medication(query, search_type)
                if result.get("success") and result.get("results"):
                    med = result["results"][0]
                    return f"Médicament trouvé: {med.get('denomination', 'N/A')}, Prix: {med.get('public_price', 'N/A')}€, Statut: {med.get('commercialization_status', 'N/A')}"
                return f"Aucun médicament trouvé pour: {query}"
            except Exception as e:
                return f"Erreur lors de la recherche de médicament: {str(e)}"
        
        tools.append(StructuredTool.from_function(
            func=search_medication,
            name="search_medication",
            description="Recherche d'informations sur les médicaments français dans la base BDPM. Paramètres: query (nom du médicament), search_type (optionnel: 'name', 'substance', 'cis_code')"
        ))
        
        # Annuaire Santé Practitioner Search Tool
        async def search_practitioners(specialty: str, location: str = None) -> str:
            """Search for healthcare practitioners in Annuaire Santé"""
            try:
                params = {"specialty": specialty}
                if location:
                    params["location"] = location
                
                result = await self.annuaire_client.search_practitioners(params)
                if result.get("success"):
                    total = result.get("total_found", 0)
                    return f"Trouvé {total} {specialty}s" + (f" près de {location}" if location else " en France")
                return f"Aucun {specialty} trouvé"
            except Exception as e:
                return f"Erreur lors de la recherche de praticiens: {str(e)}"
        
        tools.append(StructuredTool.from_function(
            func=search_practitioners,
            name="search_practitioners",
            description="Recherche de praticiens de santé dans l'Annuaire Santé. Paramètres: specialty (spécialité médicale), location (optionnel: ville ou région)"
        ))
        
        # Care Pathway Advisor Tool
        async def get_care_pathway(condition: str, location: str = None, preferences: str = None) -> str:
            """Get optimized care pathway recommendations"""
            try:
                params = {"condition": condition}
                if location:
                    params["location"] = location
                if preferences:
                    params["preferences"] = {"cost_preference": preferences}
                
                result = await self.care_pathway_advisor.get_optimized_pathway(params)
                if result.get("success"):
                    steps = result.get("pathway_steps", [])
                    timeline = result.get("estimated_timeline", {})
                    return f"Parcours recommandé pour {condition}: {len(steps)} étapes, durée estimée: {timeline.get('total_duration', 'N/A')}"
                return f"Impossible de générer un parcours pour: {condition}"
            except Exception as e:
                return f"Erreur lors de la génération du parcours: {str(e)}"
        
        tools.append(StructuredTool.from_function(
            func=get_care_pathway,
            name="get_care_pathway",
            description="Génère un parcours de soins optimisé. Paramètres: condition (état de santé), location (optionnel), preferences (optionnel: 'low-cost', 'fast', 'quality')"
        ))
        
        # Reimbursement Simulation Tool
        async def simulate_reimbursement(medication_or_procedure: str, mutuelle_type: str = None) -> str:
            """Simulate reimbursement costs"""
            try:
                params = {"item": medication_or_procedure}
                if mutuelle_type:
                    params["mutuelle_type"] = mutuelle_type
                
                result = await self.reimbursement_simulator.simulate_costs(params)
                if result.get("success"):
                    total_cost = result.get("total_cost", 0)
                    reimbursed = result.get("total_reimbursed", 0)
                    out_of_pocket = total_cost - reimbursed
                    return f"Coût total: {total_cost}€, Remboursé: {reimbursed}€, Reste à charge: {out_of_pocket}€"
                return f"Simulation impossible pour: {medication_or_procedure}"
            except Exception as e:
                return f"Erreur lors de la simulation: {str(e)}"
        
        tools.append(StructuredTool.from_function(
            func=simulate_reimbursement,
            name="simulate_reimbursement",
            description="Simule les coûts et remboursements. Paramètres: medication_or_procedure (médicament ou acte médical), mutuelle_type (optionnel: type de mutuelle)"
        ))
        
        # Odissé Regional Data Tool
        async def get_regional_health_data(location: str, specialty: str = None) -> str:
            """Get regional healthcare access data"""
            try:
                result = await self.odisse_client.get_comprehensive_data(location, specialty)
                if result.get("success"):
                    insights = result.get("insights", {})
                    recommendations = insights.get("recommendations", [])
                    return f"Données régionales pour {location}: " + ", ".join(recommendations[:2]) if recommendations else "Données disponibles"
                return f"Pas de données régionales pour: {location}"
            except Exception as e:
                return f"Erreur lors de la récupération des données régionales: {str(e)}"
        
        tools.append(StructuredTool.from_function(
            func=get_regional_health_data,
            name="get_regional_health_data",
            description="Récupère les données d'accès aux soins régionales d'Odissé. Paramètres: location (région ou département), specialty (optionnel: spécialité médicale)"
        ))
        
        # User Profile Management Tool
        async def get_user_profile(user_id: str = "default") -> str:
            """Get user profile information"""
            try:
                context = await self.memory_store.get_user_context(user_id)
                profile = context.get("profile", {})
                if profile:
                    info = []
                    if "location" in profile:
                        info.append(f"Localisation: {profile['location']}")
                    if "mutuelle" in profile:
                        info.append(f"Mutuelle: {profile['mutuelle']}")
                    if "pathology" in profile:
                        info.append(f"Pathologie: {profile['pathology']}")
                    return "Profil utilisateur: " + ", ".join(info) if info else "Profil utilisateur basique"
                return "Aucun profil utilisateur trouvé"
            except Exception as e:
                return f"Erreur lors de la récupération du profil: {str(e)}"
        
        tools.append(StructuredTool.from_function(
            func=get_user_profile,
            name="get_user_profile",
            description="Récupère le profil utilisateur stocké. Paramètres: user_id (optionnel, par défaut 'default')"
        ))
        
        return tools
    
    def _create_agent(self) -> OpenAIFunctionsAgent:
        """Create the main healthcare agent with specialized prompts"""
        
        system_prompt = """Tu es un assistant IA expert du système de santé français, spécialisé dans l'orchestration intelligente des soins de santé.

🎯 TON RÔLE :
- Analyser les besoins de santé des utilisateurs français
- Orchestrer les outils appropriés pour fournir des réponses complètes
- Optimiser les parcours de soins et les coûts
- Fournir des conseils pratiques et actionables

🔧 TES OUTILS :
- search_medication: Base BDPM officielle pour médicaments
- search_practitioners: Annuaire Santé pour praticiens
- get_care_pathway: Générateur de parcours de soins optimisés
- simulate_reimbursement: Simulateur de remboursements Sécu + mutuelles
- get_regional_health_data: Données Odissé pour optimisation régionale
- get_user_profile: Profil utilisateur pour personnalisation

🎯 MÉTHODE DE TRAVAIL :
1. Analyse du besoin utilisateur
2. Récupération du profil utilisateur si pertinent
3. Orchestration des outils appropriés dans l'ordre logique
4. Synthèse des informations pour une réponse cohérente
5. Conseils pratiques et étapes suivantes

💡 PRINCIPES :
- Privilégie les sources officielles françaises (BDPM, Annuaire Santé, Odissé)
- Optimise coût/qualité selon le profil utilisateur
- Propose des parcours concrets et réalisables
- Respecte les spécificités du système de santé français

🔍 EXEMPLES D'ORCHESTRATION :
- Pour "prix Doliprane" → search_medication + simulate_reimbursement
- Pour "mal de dos Paris" → get_user_profile + get_care_pathway + search_practitioners
- Pour "parcours diabète" → get_user_profile + get_care_pathway + get_regional_health_data

Réponds TOUJOURS en français et de manière structurée avec des actions concrètes."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    async def process_query(self, user_query: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process user query using LangChain agent orchestration
        
        Args:
            user_query: Natural language query from user
            user_id: User identifier for context retrieval
            
        Returns:
            Structured response with agent reasoning and results
        """
        try:
            self.logger.info(f"[LANGCHAIN_ORCHESTRATOR] Processing query: {user_query}")
            
            # Track token usage
            with get_openai_callback() as cb:
                # Execute the agent with proper input format
                result = await self.agent_executor.ainvoke({
                    "input": user_query
                })
                
                # Update user memory with session data
                await self.memory_store.update_session_history(
                    user_id, 
                    user_query, 
                    {"agent_response": result["output"]}
                )
                
                return {
                    "success": True,
                    "response": result["output"],
                    "agent_type": "langchain_orchestrator",
                    "reasoning_steps": result.get("intermediate_steps", []),
                    "tokens_used": {
                        "total_tokens": cb.total_tokens,
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_cost": cb.total_cost
                    },
                    "user_id": user_id,
                    "memory_updated": True
                }
                
        except Exception as e:
            self.logger.error(f"[LANGCHAIN_ORCHESTRATOR_ERROR] {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": "langchain_orchestrator",
                "fallback_message": "Je rencontre une difficulté technique. Pourriez-vous reformuler votre question ?"
            }
    
    async def get_conversation_history(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        try:
            context = await self.memory_store.get_user_context(user_id)
            return context.get("session_history", [])
        except Exception as e:
            self.logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    async def clear_conversation_memory(self, user_id: str = "default") -> bool:
        """Clear conversation memory for a user"""
        try:
            self.memory.clear()
            # Also clear from persistent store
            await self.memory_store.clear_user_session(user_id)
            return True
        except Exception as e:
            self.logger.error(f"Error clearing conversation memory: {str(e)}")
            return False
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return [tool.name for tool in self.tools]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all integrated modules"""
        health_status = {
            "langchain_orchestrator": "healthy",
            "llm_connection": "unknown",
            "tools_status": {},
            "memory_status": "unknown"
        }
        
        # Test LLM connection
        try:
            test_response = await self.llm.ainvoke("Ping")
            health_status["llm_connection"] = "healthy"
        except Exception as e:
            health_status["llm_connection"] = f"error: {str(e)}"
        
        # Test memory store
        try:
            await self.memory_store.get_user_context("health_check")
            health_status["memory_status"] = "healthy"
        except Exception as e:
            health_status["memory_status"] = f"error: {str(e)}"
        
        # Test individual tools (simplified check)
        for tool in self.tools:
            try:
                # Basic validation that tool is properly configured
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    health_status["tools_status"][tool.name] = "configured"
                else:
                    health_status["tools_status"][tool.name] = "misconfigured"
            except Exception as e:
                health_status["tools_status"][tool.name] = f"error: {str(e)}"
        
        return health_status
