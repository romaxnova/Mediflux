"""
FastAPI Server for Mediflux V2
Connects React frontend to backend orchestrator
"""

import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uvicorn

# Add parent directory to path to import orchestrator
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
modules_dir = os.path.join(parent_dir, 'modules')
sys.path.insert(0, parent_dir)
sys.path.insert(0, modules_dir)

from modules.orchestrator import MedifluxOrchestrator

app = FastAPI(title="Mediflux V2 API", version="2.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = MedifluxOrchestrator()

# Request/Response models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class UserProfile(BaseModel):
    mutuelle_type: str
    preferences: str
    pathology: Optional[str] = None
    region: Optional[str] = None
    age_range: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Mediflux V2 API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """
    Main chat endpoint - processes user messages through orchestrator
    """
    try:
        result = await orchestrator.process_query(
            user_query=message.message,
            user_id=message.user_id
        )
        
        # Convert orchestrator response to frontend format
        success = result.get("success", False)
        intent = result.get("intent", "unknown")
        results = result.get("results", {})
        
        # Use AI-generated response if available, otherwise fallback
        if success and "response" in result:
            response_text = result["response"]  # AI-generated response
        elif success:
            # Fallback for backward compatibility
            response_text = f"✅ Requête traitée avec succès. Intent: {intent}"
        else:
            error = result.get("error", "Erreur inconnue")
            response_text = f"❌ Erreur: {error}"
        
        return ChatResponse(
            response=response_text,
            intent=intent,
            data=result
        )
    except Exception as e:
        print(f"Error processing chat message: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            response=f"❌ Erreur système: {str(e)}",
            intent="error",
            data={"error": str(e)}
        )

@app.post("/document/analyze")
async def analyze_document(file: UploadFile = File(...), user_id: Optional[str] = "default"):
    """
    Document analysis endpoint
    """
    import tempfile
    import os
    
    temp_file_path = None
    try:
        print(f"Received document upload: {file.filename}, size: {file.size}")
        
        # Create temporary file to save uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            print(f"Saved uploaded file to: {temp_file_path}")
        
        # Process through orchestrator's document analysis workflow
        print(f"Calling orchestrator with user_id: {user_id}")
        result = await orchestrator._handle_document_analysis(
            params={"document_path": temp_file_path, "document_type": "auto_detect"},
            user_context=await orchestrator.memory_store.get_user_context(user_id)
        )
        
        print(f"Orchestrator result: {result}")
        
        return {
            "analysis": result.get("analysis", {}),
            "extracted_data": result.get("analysis", {}),
            "filename": file.filename
        }
    except Exception as e:
        print(f"Error analyzing document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"Error cleaning up temp file: {cleanup_error}")

@app.post("/profile/save")
async def save_profile(profile: UserProfile, user_id: Optional[str] = "default"):
    """
    Save user profile
    """
    try:
        # Save to memory store
        await orchestrator.memory_store.store_user_profile(user_id, profile.dict())
        
        return {"message": "Profil sauvegardé avec succès"}
    except Exception as e:
        print(f"Error saving profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """
    Get user profile
    """
    try:
        profile = await orchestrator.memory_store.get_user_profile(user_id)
        return profile if profile else {}
    except Exception as e:
        print(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/reimbursement/{user_id}")
async def get_reimbursement_analysis(user_id: str):
    """
    Get latest reimbursement analysis for user
    """
    try:
        analysis = await orchestrator.memory_store.get_latest_analysis(user_id, "reimbursement")
        return analysis if analysis else {}
    except Exception as e:
        print(f"Error getting reimbursement analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/pathway/{user_id}")
async def get_pathway_analysis(user_id: str):
    """
    Get latest care pathway analysis for user
    """
    try:
        analysis = await orchestrator.memory_store.get_latest_analysis(user_id, "pathway")
        return analysis if analysis else {}
    except Exception as e:
        print(f"Error getting pathway analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting Mediflux V2 API Server...")
    print("Frontend: http://localhost:5173")
    print("API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
