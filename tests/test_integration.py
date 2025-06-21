import sys
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_existing_structure():
    """Verify existing files are still intact"""
    mcp_server_path = "mcp_server.py"
    assert os.path.exists(mcp_server_path), "mcp_server.py should still exist"
    routers_path = "routers"
    assert os.path.exists(routers_path), "routers directory should exist"
    organization_router = os.path.join(routers_path, "organization.py")
    if os.path.exists(organization_router):
        print("✅ Existing organization router preserved")
    print("✅ Integration test passed - existing structure intact")

if __name__ == "__main__":
    test_existing_structure()