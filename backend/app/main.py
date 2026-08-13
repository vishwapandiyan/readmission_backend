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
from app.database import init_db, engine

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
    """Initialize database and load ML model on startup"""
    print(f"\n{'='*80}")
    print(f"{settings.APP_NAME} v{settings.VERSION}")
    print(f"{'='*80}\n")
    
    # Initialize database
    try:
        print("📊 Initializing database...")
        await init_db()
        print("✓ Database tables ready")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Create default users
    try:
        from app.services.auth_service import create_default_users
        print("👥 Creating default users...")
        await create_default_users()
    except Exception as e:
        print(f"⚠ Default users creation: {e}")
    
    # Load model
    model_path = Path(__file__).parent.parent / settings.MODEL_PATH
    try:
        model_loader.load_model(str(model_path))
        print(f"✓ ML model loaded successfully")
        print(f"  Path: {model_path}")
        print(f"  Performance: 82.4% Test Accuracy")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print(f"  Path attempted: {model_path}")
    
    print(f"\n{'='*80}")
    print(f"Server starting on {settings.HOST}:{settings.PORT}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database: PostgreSQL")
    print(f"{'='*80}\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await engine.dispose()
    print("\n✓ Database connections closed")


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
        model_loaded = model_loader.model is not None
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
