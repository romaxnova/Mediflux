from fastapi import FastAPI
import uvicorn
from routers.sante import router as sante_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Include routers
app.include_router(sante_router, prefix="/api")

if __name__ == "__main__":
    logger.info("Starting API server on http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)
