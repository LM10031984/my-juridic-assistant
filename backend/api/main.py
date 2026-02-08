"""
My Juridic Assistant - Main API Application
FastAPI backend with RAG (Retrieval-Augmented Generation)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="My Juridic Assistant API",
    description="API RAG pour conseils juridiques en immobilier francais",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, specifier les origines autorisees
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "My Juridic Assistant API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }


# Import and include routers
from api.routes.ask import router as ask_router
app.include_router(ask_router, prefix="/api", tags=["ask"])


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))

    print(f"Starting My Juridic Assistant API on {host}:{port}")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)
