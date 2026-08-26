from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router as api_router
from app.api.websocket import ws_router

app = FastAPI(
    title="Agentic RAG for GitHub Trending Repos",
    description="Backend service providing real-time trending GitHub repository RAG via LangGraph, Qdrant, and AWS Bedrock.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST and WebSocket routers
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/health")
async def health_check():
    """Simple health check endpoint returning server status."""
    return {
        "status": "ok",
        "service": "agentic-rag-backend",
        "version": "1.0.0",
        "qdrant_host": settings.QDRANT_HOST,
        "aws_region": settings.AWS_REGION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
