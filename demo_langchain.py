#!/usr/bin/env python3
"""
LangChain Integration Demo for Mediflux
Demonstrates healthcare agent orchestration capabilities
"""

import asyncio
import sys
from typing import Dict, Any

# Add modules to path
sys.path.append('/Users/romanstadnikov/Desktop/Mediflux')

from modules.langchain_orchestrator import LangChainOrchestrator
from modules.specialized_agents import AgentOrchestrator, MedicationAgent, PathwayAgent, ReimbursementAgent
from modules.workflow_engine import HealthcareWorkflowEngine

class LangChainDemo:
    """Demo class for LangChain healthcare integration"""
    
    def __init__(self):
        self.orchestrator = LangChainOrchestrator()
        self.agent_orchestrator = AgentOrchestrator()
        self.workflow_engine = HealthcareWorkflowEngine()
    
    async def demo_tool_creation(self):
        """Demonstrate healthcare tool creation"""
        
        print("🔧 Healthcare Tools Available:")
        print("=" * 40)
        
        # Get health check to see what tools are available
        health_check = await self.orchestrator.health_check()
        
        tools = health_check.get("available_tools", [])
        
        for tool in tools:
            print(f"✅ {tool}")
        
        print(f"\nTotal tools available: {len(tools)}")
        
        return tools
    
    async def demo_specialized_agents(self):
        """Demonstrate specialized healthcare agents"""
        
        print("\n🤖 Specialized Healthcare Agents:")
        print("=" * 40)
        
        # Medication Agent Demo
        print("\n💊 Medication Agent Capabilities:")
        medication_agent = MedicationAgent()
        med_tools = medication_agent.get_available_tools()
        
        for tool in med_tools:
            print(f"  • {tool}")
        
        # Care Pathway Agent Demo
        print("\n🏥 Care Pathway Agent Capabilities:")
        pathway_agent = PathwayAgent()
        pathway_tools = pathway_agent.get_available_tools()
        
        for tool in pathway_tools:
            print(f"  • {tool}")
        
        # Reimbursement Agent Demo
        print("\n💰 Reimbursement Agent Capabilities:")
        reimbursement_agent = ReimbursementAgent()
        reimb_tools = reimbursement_agent.get_available_tools()
        
        for tool in reimb_tools:
            print(f"  • {tool}")
        
        return {
            "medication": med_tools,
            "pathway": pathway_tools,
            "reimbursement": reimb_tools
        }
    
    async def demo_workflow_chains(self):
        """Demonstrate workflow chains"""
        
        print("\n⛓️  Healthcare Workflow Chains:")
        print("=" * 40)
        
        workflows = self.workflow_engine.get_available_workflows()
        
        workflow_descriptions = {
            "medication_analysis": "Complete medication analysis with cost optimization",
            "pathway_optimization": "Care pathway planning with resource optimization",
            "health_journey": "Comprehensive health journey planning and tracking",
            "document_integration": "Document analysis and integration workflows"
        }
        
        for workflow in workflows:
            description = workflow_descriptions.get(workflow, "Healthcare workflow")
            print(f"🔗 {workflow}: {description}")
        
        return workflows
    
    async def demo_simulated_interaction(self):
        """Simulate healthcare interactions"""
        
        print("\n🎭 Simulated Healthcare Interactions:")
        print("=" * 40)
        
        # Simulate different types of healthcare queries
        simulated_queries = [
            {
                "type": "medication",
                "query": "Je cherche des informations sur le prix du Doliprane 1000mg",
                "expected_agent": "Medication Agent",
                "expected_tools": ["bdpm_lookup", "price_calculation", "reimbursement_check"]
            },
            {
                "type": "pathway",
                "query": "J'ai mal au dos depuis 2 semaines, quel parcours de soins ?",
                "expected_agent": "Care Pathway Agent",
                "expected_tools": ["pathway_analysis", "practitioner_search", "appointment_optimization"]
            },
            {
                "type": "reimbursement",
                "query": "Combien me coûtera une consultation chez un cardiologue secteur 2 ?",
                "expected_agent": "Reimbursement Agent",
                "expected_tools": ["cost_calculation", "reimbursement_simulation", "mutual_optimization"]
            },
            {
                "type": "complex",
                "query": "Parcours complet pour diabète : médicaments, consultations et remboursements",
                "expected_agent": "Multi-Agent Orchestration",
                "expected_tools": ["all_agents", "workflow_coordination", "comprehensive_planning"]
            }
        ]
        
        for i, sim in enumerate(simulated_queries, 1):
            print(f"\n📝 Simulation {i}: {sim['type'].title()} Query")
            print(f"Query: {sim['query']}")
            print(f"Expected Agent: {sim['expected_agent']}")
            print(f"Expected Tools: {', '.join(sim['expected_tools'])}")
            
            # Simulate agent selection logic
            if sim['type'] == 'medication':
                print("🤖 → Routing to Medication Agent")
            elif sim['type'] == 'pathway':
                print("🤖 → Routing to Care Pathway Agent")
            elif sim['type'] == 'reimbursement':
                print("🤖 → Routing to Reimbursement Agent")
            else:
                print("🤖 → Routing to Multi-Agent Orchestrator")
            
            print("✅ Simulated processing complete")
        
        return simulated_queries
    
    async def demo_integration_benefits(self):
        """Show benefits of LangChain integration"""
        
        print("\n🚀 LangChain Integration Benefits:")
        print("=" * 40)
        
        benefits = [
            "🧠 Intelligent Intent Recognition: Better understanding of French healthcare queries",
            "🔗 Tool Orchestration: Seamless coordination between healthcare modules",
            "💬 Conversational Memory: Context-aware multi-turn conversations",
            "⚡ Dynamic Routing: Smart agent selection based on query complexity",
            "🎯 Specialized Agents: Domain-specific expertise for medication, pathways, and costs",
            "📊 Workflow Chains: Multi-step healthcare processes automation",
            "🔄 Error Handling: Robust fallback mechanisms and retries",
            "📈 Monitoring: Built-in tracing and performance analytics",
            "🌐 Scalable Architecture: Easy addition of new healthcare capabilities",
            "🇫🇷 French Healthcare: Optimized for French healthcare system specifics"
        ]
        
        for benefit in benefits:
            print(benefit)
        
        return benefits
    
    async def demo_next_steps(self):
        """Show next steps for implementation"""
        
        print("\n📋 Implementation Roadmap:")
        print("=" * 40)
        
        steps = [
            "1. 🔑 Configure OpenAI API key in .env file",
            "2. 🧪 Run comprehensive test suite",
            "3. 🎨 Integrate with frontend interface",
            "4. 📊 Add LangSmith monitoring",
            "5. 🔄 Implement user feedback loops",
            "6. 📈 Add analytics and metrics",
            "7. 🚀 Deploy to production environment",
            "8. 📱 Extend to mobile applications"
        ]
        
        for step in steps:
            print(step)
        
        print("\n💡 Quick Start Commands:")
        print("=" * 25)
        print("# Copy example environment")
        print("cp .env.example .env")
        print()
        print("# Add your OpenAI API key to .env")
        print("# OPENAI_API_KEY=your_key_here")
        print()
        print("# Run comprehensive tests")
        print("python test_langchain_integration.py")
        print()
        print("# Start development server")
        print("python start_api.py")
        
        return steps

async def main():
    """Run the complete demo"""
    
    print("🏥 Mediflux LangChain Integration Demo")
    print("🇫🇷 Advanced Healthcare Agent Orchestration")
    print("=" * 60)
    
    demo = LangChainDemo()
    
    try:
        # Run all demo sections
        await demo.demo_tool_creation()
        await demo.demo_specialized_agents()
        await demo.demo_workflow_chains()
        await demo.demo_simulated_interaction()
        await demo.demo_integration_benefits()
        await demo.demo_next_steps()
        
        print("\n✨ Demo completed successfully!")
        print("The LangChain integration is ready for French healthcare workflows.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("Check the error details above and ensure all dependencies are installed.")

if __name__ == "__main__":
    asyncio.run(main())
