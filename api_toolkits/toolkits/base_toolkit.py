from abc import ABC, abstractmethod
import typing
from typing import List, Dict

class APIToolkitBase(ABC):
    @abstractmethod
    def get_endpoints(self) -> List[str]:
        pass

    @abstractmethod
    def execute(self, endpoint: str, params: Dict) -> Dict:
        pass