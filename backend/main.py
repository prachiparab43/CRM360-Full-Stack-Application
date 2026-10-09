from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings

app = FastAPI(title="CRM360 API")

# Configure CORS using environment variable with fallback
frontend_url = settings.FRONTEND_URL
origins = [url.strip() for url in frontend_url.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# FastAPI /health endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "CRM360 API is running"}
