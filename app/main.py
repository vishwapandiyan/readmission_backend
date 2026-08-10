"""
FastAPI Application - Hospital Readmission Prediction System
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.api.v1.router import api_router
from app.models.schemas import HealthResponse
from app.ml.model_loader import model_loader

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade API for hospital readmission prediction with 89% accuracy",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load ML model on startup"""
    print(f"\n{'='*80}")
    print(f"{settings.APP_NAME} v{settings.VERSION}")
    print(f"{'='*80}\n")
    
    # Load model
    model_path = Path(__file__).parent.parent / settings.MODEL_PATH
    try:
        model_loader.load_comprehensive_system(str(model_path))
        print(f"✓ ML model loaded successfully")
        print(f"  Path: {model_path}")
        print(f"  Performance: 89.9% AUC, 89% Accuracy")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print(f"  Path attempted: {model_path}")
    
    print(f"\n{'='*80}")
    print(f"Server starting on {settings.HOST}:{settings.PORT}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"{'='*80}\n")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        model_loaded = model_loader.get_system() is not None
    except:
        model_loaded = False
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        version=settings.VERSION,
        model_loaded=model_loaded,
        timestamp=datetime.now()
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
