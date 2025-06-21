import importlib

def unified_search_context(query: str):
    """
    Unified MCP tool: routes to PractitionerRole or Organization search based on query content.
    """
    # Import routers
    org_mod = importlib.import_module("organization_mcp")
    prac_mod = importlib.import_module("practitioner_role_mcp")
    # Heuristic: if query contains a known specialty, use PractitionerRole
    for spec in prac_mod.SPECIALTY_MAP.keys():
        if spec in query.lower():
            result = prac_mod.practitioner_role_context(query)
            if result and "No practitioners found" not in result:
                return result
            # Fallback to organization if no practitioners found
            return org_mod.organization_context(query)
    # Otherwise, use Organization
    return org_mod.organization_context(query)

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "find 2 dentists from 75002"
    result = unified_search_context(query)
    print(result)
