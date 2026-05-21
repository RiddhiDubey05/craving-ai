import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.utils.logger import app_logger
from backend.models.schemas import HealthResponse
from backend.db.faiss_store import faiss_store
from backend.api.routes import upload, recommend, chat, craving, delivery, recipe, auth, profile, admin, image_cache, discovery, cart

settings = get_settings()

app = FastAPI(
    title="CravingAI — Global Culinary Intelligence Engine",
    description=(
        "Production-grade semantic food search and recommendation API. "
        "Powered by a scalable food knowledge pipeline, FAISS vector indexing, "
        "and a multi-signal semantic reranker. Supports 10,000+ global dishes."
    ),
    version="2.0.0",
)

# Configure CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
allow_all_origins = "*" in origins or not origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else origins,
    allow_credentials=False if allow_all_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local static files for image uploads fallback
local_image_dir = os.path.join("data", "images")
os.makedirs(local_image_dir, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=local_image_dir), name="static_images")

# Mount API Routers
app.include_router(upload.router)
app.include_router(recommend.router)
app.include_router(chat.router)
app.include_router(craving.router)
app.include_router(delivery.router)
app.include_router(recipe.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(discovery.router)
app.include_router(image_cache.router, prefix="/api/images", tags=["Images"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])


@app.on_event("startup")
async def startup_event():
    app_logger.info(f"Starting CravingAI in environment: {settings.app_env}")
    app_logger.info("Initializing food knowledge pipeline, FAISS index, and embedding service...")
    try:
        from backend.db.seed_data import seed_database
        seed_database()
        faiss_size = faiss_store.index.ntotal if faiss_store.index else 0
        app_logger.info(
            f"✓ CravingAI ready — {faiss_size} dishes indexed and searchable. "
            f"Add new dishes via POST /api/admin/ingest"
        )
    except Exception as e:
        app_logger.error(f"Error during startup food knowledge seeding: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    app_logger.info("Shutting down application...")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    app_logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Latency: {duration:.2f}ms"
    )
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check health status of the application and integrated services.
    """
    # Dynamic checks for services
    s3_configured = settings.aws_access_key_id != "your_access_key_here" and bool(settings.aws_access_key_id)
    bedrock_configured = settings.aws_access_key_id != "your_access_key_here" and bool(settings.aws_access_key_id)
    
    faiss_size = faiss_store.index.ntotal if faiss_store.index is not None else 0
    faiss_status = "loaded" if faiss_size > 0 else "empty"

    return HealthResponse(
        status="healthy",
        faiss_index_size=faiss_size,
        services={
            "aws_s3": "initialized" if s3_configured else "local_fallback_mode",
            "aws_bedrock": "initialized" if bedrock_configured else "mock_fallback_mode",
            "faiss": faiss_status,
        },
        version="1.0.0",
    )


# Serve frontend static files at root (must be registered last)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
