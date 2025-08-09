"""
AI Response Generator for Mediflux V2
Generates intelligent, contextual responses using Grok API
Combines structured data with natural language generation
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
import aiohttp
import logging
from dotenv import load_dotenv


class AIResponseGenerator:
    """
    Generates intelligent responses using Grok API
    Combines orchestrator results with user context for natural responses
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        
        # Try to get Grok API key from environment
        self.api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.api_base = "https://api.x.ai/v1"
        
        # Fallback to OpenAI-compatible API if no Grok key
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.api_base = "https://api.openai.com/v1"
        
        self.model = "grok-2" if "x.ai" in self.api_base else "gpt-3.5-turbo"
        
    async def generate_response(
        self, 
        user_query: str, 
        intent: str, 
        orchestrator_results: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> str:
        """
        Generate intelligent response based on query, intent, and results
        
        Args:
            user_query: Original user question
            intent: Detected intent from orchestrator
            orchestrator_results: Structured data from orchestrator
            user_context: User profile and history
            
        Returns:
            Natural language response
        """
        try:
            # If no API key, return enhanced fallback
            if not self.api_key:
                return self._generate_fallback_response(user_query, intent, orchestrator_results, user_context)
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(user_query, intent, orchestrator_results, user_context)
            
            # Call LLM API
            response = await self._call_llm_api(system_prompt, user_prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"AI response generation failed: {str(e)}")
            return self._generate_fallback_response(user_query, intent, orchestrator_results, user_context)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for French healthcare AI assistant"""
        return """Tu es un assistant IA expert du système de santé français. 

🎯 OBJECTIF : Fournir des réponses DIRECTES, UTILES et ACTIONABLES.

📋 TES CAPACITÉS :
- Base BDPM (médicaments officiels + prix + remboursements)
- Annuaire Santé CNAM (praticiens + secteurs + spécialités)
- Simulation remboursements (Sécu + mutuelles)
- Analyse documents médicaux
- Parcours de soins optimisés

✅ STYLE DE RÉPONSE REQUIS :
- DIRECTE : Réponds immédiatement à la question
- CONCRÈTE : Donne des informations précises et actionables
- STRUCTURÉE : Utilise des emojis (💊 médicaments, 💰 coûts, 🏥 praticiens)
- FRANÇAISE : Exclusivement en français
- SOURCES : Mentionne les bases de données utilisées
- ACTIONS : Propose des étapes concrètes

❌ ÉVITE ABSOLUMENT :
- Les introductions longues ("Tout d'abord, analysons...")
- Les explications de ton processus de réflexion
- Les répétitions de la question utilisateur
- Les réponses vagues ou générales

� EXEMPLE DE BONNE RÉPONSE :
User: "Prix du Doliprane ?"
Toi: "💊 DOLIPRANE 1000mg : 2,50€ (BDPM)
💰 Remboursement : 15% Sécu + mutuelle
🎯 Action : Présenter ordonnance en pharmacie"

Réponds TOUJOURS de manière directe et utile."""

    def _build_user_prompt(
        self, 
        user_query: str, 
        intent: str, 
        results: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> str:
        """Build user-specific prompt with context and results"""
        
        prompt = f"QUESTION DE L'UTILISATEUR : {user_query}\n\n"
        prompt += f"INTENT DÉTECTÉ : {intent}\n\n"
        
        # Add user context if available
        profile = user_context.get("profile", {})
        if profile:
            prompt += "PROFIL UTILISATEUR :\n"
            if "mutuelle_type" in profile:
                prompt += f"- Mutuelle : {profile['mutuelle_type']}\n"
            if "pathology" in profile:
                prompt += f"- Pathologie : {profile['pathology']}\n"
            if "preferences" in profile:
                prompt += f"- Préférences : {profile['preferences']}\n"
            prompt += "\n"
        
        # Add orchestrator results
        if results and results.get("success", True):
            # For care pathway with structured data, provide minimal context to avoid duplication
            if intent == "care_pathway" and results.get("type") == "care_pathway" and results.get("pathway", {}).get("evidence"):
                prompt += "RÉSULTATS DU SYSTÈME :\n"
                pathway = results.get("pathway", {})
                prompt += f"- Condition: {pathway.get('condition', 'N/A')}\n"
                prompt += f"- Evidence: {pathway.get('evidence', {}).get('level', 'N/A')} ({pathway.get('evidence', {}).get('source', 'N/A')})\n"
                prompt += f"- Structured data available: pathway steps, medications, quality indicators\n\n"
            else:
                prompt += "RÉSULTATS DU SYSTÈME :\n"
                prompt += json.dumps(results, indent=2, ensure_ascii=False)
                prompt += "\n\n"
        
        prompt += """CONSIGNES DE RÉPONSE :
1. RÉPONDS DIRECTEMENT à la question sans préambule
2. Pour les parcours de soins avec données structurées: DONNE SEULEMENT UN TITRE COURT ET REDIRIGE vers les détails visuels
3. ÉVITE ABSOLUMENT de mentionner des étapes spécifiques, médicaments, ou coûts qui seront affichés visuellement
4. FORMAT: Titre + brève mention de fiabilité + direction vers les détails structurés
5. MAXIMUM 2-3 lignes de texte pour les parcours avec données structurées
6. MENTIONNE la source d'évidence si pertinente
7. PAS de questions de suivi pour les parcours structurés

EXEMPLE POUR PARCOURS STRUCTURÉ:
"📋 **Parcours personnalisé** (Niveau A, 95% fiabilité)

Consultez les recommandations détaillées ci-dessous."

RÉPONSE CONCISE :"""
        
        return prompt
    
    async def _call_llm_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM API (Grok or OpenAI) with rate limiting"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        choice = data["choices"][0]["message"]
                        # grok-4-0709 provides direct content (no reasoning_content needed)
                        content = choice.get("content", "").strip()
                        return content
                    elif response.status == 429:
                        # Rate limited - wait and retry once
                        self.logger.warning("Rate limited, waiting 5 seconds...")
                        await asyncio.sleep(5)
                        
                        # Retry once
                        async with session.post(
                            f"{self.api_base}/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as retry_response:
                            if retry_response.status == 200:
                                retry_data = await retry_response.json()
                                retry_choice = retry_data["choices"][0]["message"]
                                retry_content = retry_choice.get("content", "").strip()
                                return retry_content
                            else:
                                retry_error = await retry_response.text()
                                raise Exception(f"Retry failed {retry_response.status}: {retry_error}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")
                        
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
    
    def _generate_fallback_response(
        self, 
        user_query: str, 
        intent: str, 
        results: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate intelligent fallback when LLM is not available"""
        
        profile = user_context.get("profile", {})
        
        if intent == "medication_info":
            medication_data = results.get("medication_data", {})
            if medication_data.get("success"):
                meds = medication_data.get("results", [])
                if meds:
                    med = meds[0]
                    return f"💊 **{med.get('denomination', 'Médicament')}**\n\n" \
                           f"💰 Prix public : {med.get('public_price', 'N/A')}€\n" \
                           f"📋 Statut : {med.get('commercialization_status', 'N/A')}\n\n" \
                           f"*Données BDPM officielles*\n\n" \
                           f"Souhaitez-vous simuler le remboursement ?"
            return f"💊 Je recherche des informations sur ce médicament...\n\n" \
                   f"Puis-je vous aider avec autre chose ?"
        
        elif intent == "practitioner_search":
            search_results = results.get("search_results", {})
            if search_results.get("success"):
                total = search_results.get("total_found", 0)
                specialty = search_results.get("specialty", "praticiens")
                location = search_results.get("location", "")
                
                response = f"👩‍⚕️ **Recherche de {specialty}**\n\n"
                if total > 0:
                    response += f"✅ {total} {specialty}s trouvés"
                    if location:
                        response += f" (recherche nationale)"
                    response += f"\n\n📍 *Filtrage par ville non disponible dans l'API Annuaire Santé*"
                else:
                    response += f"❌ Aucun {specialty} trouvé"
                
                response += f"\n\n💡 Astuce : Préférez les praticiens secteur 1 pour minimiser les frais"
                return response
            
        elif intent == "care_pathway":
            pathway_data = results.get("pathway", {})
            if pathway_data.get("success"):
                condition = pathway_data.get("condition", "votre pathologie")
                evidence_level = pathway_data.get("evidence", {}).get("level", "")
                confidence = pathway_data.get("evidence", {}).get("confidence", 0)
                
                # Check if we have comprehensive structured data
                has_rich_data = (
                    pathway_data.get("evidence") and 
                    pathway_data.get("medications") and 
                    len(pathway_data.get("medications", [])) > 0 and
                    pathway_data.get("pathway_steps") and 
                    len(pathway_data.get("pathway_steps", [])) > 0
                )
                
                if has_rich_data:
                    # Minimal, non-redundant response for rich structured data
                    confidence_text = f"{int(confidence*100)}% fiabilité" if confidence > 0 else "haute fiabilité"
                    return f"📋 **Parcours personnalisé** (Niveau {evidence_level}, {confidence_text})\n\nConsultez les recommandations détaillées ci-dessous."
                else:
                    # Detailed fallback when no structured data available
                    return f"🗺️ **Parcours de soins optimisé**\n\n" \
                           f"📋 Recommandations établies selon votre profil\n" \
                           f"💰 Estimation des coûts incluse\n\n" \
                           f"Souhaitez-vous plus de détails sur une étape ?"
        
        elif intent == "simulate_cost":
            simulation = results.get("simulation", {})
            if simulation.get("success"):
                return f"💰 **Simulation de remboursement**\n\n" \
                       f"📊 Calculs effectués" + (f" pour votre mutuelle {profile.get('mutuelle_type', '')}" if profile else "") + \
                       f"\n\n💡 Les montants dépendent de votre situation exacte"
        
        # General fallback
        user_name = profile.get("name", "")
        greeting = f"Bonjour{' ' + user_name if user_name else ''} ! "
        
        return f"{greeting}Je comprends que vous vous renseignez sur : **{user_query}**\n\n" \
               f"🔧 *Système en cours de traitement...*\n\n" \
               f"💡 En attendant, je peux vous aider avec :\n" \
               f"• 💊 Informations sur les médicaments\n" \
               f"• 💰 Simulations de remboursement\n" \
               f"• 🏥 Recherche de praticiens\n" \
               f"• 📄 Analyse de documents médicaux\n\n" \
               f"Que souhaitez-vous faire ?"
