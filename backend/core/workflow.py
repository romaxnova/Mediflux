from typing import List, Dict, Any
from .base_mcp import BaseMCP

class WorkflowStep:
    def __init__(self, mcps: List[BaseMCP], parallel: bool = False):
        self.mcps = mcps
        self.parallel = parallel

class Workflow:
    def __init__(self):
        self.steps: List[WorkflowStep] = []

    def add_step(self, mcps: List[BaseMCP], parallel: bool = False):
        """Add a sequential or parallel step to the workflow"""
        self.steps.append(WorkflowStep(mcps, parallel))

class WorkflowEngine:
    def create_workflow(self, intent: Dict[str, Any], mcps: List[BaseMCP]) -> Workflow:
        """Create a workflow based on intent and available MCPs"""
        workflow = Workflow()

        # For now, create a simple parallel workflow for multiple MCPs
        # This can be enhanced with more sophisticated workflow patterns
        if len(mcps) > 1:
            workflow.add_step(mcps, parallel=True)
        else:
            workflow.add_step(mcps, parallel=False)

        return workflow
