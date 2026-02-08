"""
Vercel serverless entry point for FastAPI
"""
from api.main import app

# Export for Vercel
handler = app
