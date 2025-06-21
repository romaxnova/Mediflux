from typing import Dict, Type
from .base_toolkit import APIToolkitBase
from .annuaire_sante_toolkit import AnnuaireSanteToolkit

class ToolkitRegistry:
    def __init__(self):
        self._toolkits: Dict[str, APIToolkitBase] = {}
        self._register_default_toolkits()

    def _register_default_toolkits(self):
        self.register("annuaire_sante", AnnuaireSanteToolkit())

    def register(self, name: str, toolkit: APIToolkitBase):
        self._toolkits[name] = toolkit

    def get_toolkit(self, name: str) -> APIToolkitBase:
        return self._toolkits.get(name)

    def list_toolkits(self) -> Dict[str, APIToolkitBase]:
        return self._toolkits.copy()