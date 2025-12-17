from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from services.memory_service import memory_service
from utils.logger import logger

app = FastAPI(title="AI Multi-Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize conversation history table on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing conversation history storage...")
    # Table creation is handled in memory_service.__init__()

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
