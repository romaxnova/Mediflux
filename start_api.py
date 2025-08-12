#!/usr/bin/env python3
"""
Mediflux V2 API Server Startup Script
"""

import sys
import os
import uvicorn

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    # Get environment variables for production deployment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("🏥 Starting Mediflux V2 API Server...")
    print(f"🔌 API: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print("=" * 50)
    
    # Use import string for proper reload support
    uvicorn.run("api.server:app", host=host, port=port, reload=False)
