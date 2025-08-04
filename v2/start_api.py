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
    print("🏥 Starting Mediflux V2 API Server...")
    print("📱 Frontend: http://localhost:5173")
    print("🔌 API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Use import string for proper reload support
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
