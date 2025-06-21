from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseMCP(ABC):
    @abstractmethod
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a natural language query with optional context"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return MCP capabilities for orchestrator registration"""
        pass

class MCPRegistry:
    def __init__(self):
        self.mcps = {}

    def register(self, name: str, mcp: BaseMCP):
        capabilities = mcp.get_capabilities()
        self.mcps[name] = {
            "instance": mcp,
            "capabilities": capabilities
        }

    def get_mcp(self, name: str) -> BaseMCP:
        return self.mcps.get(name, {}).get("instance")

    def get_capabilities(self, name: str) -> Dict[str, Any]:
        return self.mcps.get(name, {}).get("capabilities", {})
