from typing import Dict, Any

class ResponseBuilder:
    @staticmethod
    def build(results: Dict[str, Any]) -> Dict[str, Any]:
        """Build a standardized response from API results"""
        if not results:
            return {
                "status": "success",
                "data": [],
                "message": "No results found"
            }

        return {
            "status": "success",
            "data": results,
            "message": "Query processed successfully"
        }