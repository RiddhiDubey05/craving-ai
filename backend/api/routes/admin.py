"""
Admin Routes — Food Knowledge Management API
=============================================
Endpoints for managing the food knowledge pipeline at runtime,
without requiring server restarts.

POST /api/admin/ingest          — Re-run ingestion pipeline (delta mode)
POST /api/admin/reindex         — Force full re-embed of all dishes
POST /api/admin/ingest/dishes   — Ingest raw dish dicts directly
GET  /api/admin/stats           — Index + pipeline statistics
GET  /api/admin/catalog         — List all dishes currently in FAISS
POST /api/admin/catalog/add     — Add dishes from a new catalog JSON file
"""
import os
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from backend.services.food_pipeline import food_pipeline, CATALOG_DIR
from backend.db.faiss_store import faiss_store
from backend.utils.logger import app_logger

router = APIRouter(prefix="/api/admin", tags=["Admin — Food Knowledge"])


# ── Request/Response models ──────────────────────────────────────────────────

class RawDish(BaseModel):
    """Minimal raw dish schema for direct ingestion via API."""
    id: Optional[str] = None
    name: str
    aliases: Optional[List[str]] = []
    cuisine: str
    country: Optional[str] = ""
    description: str
    ingredients: Optional[List[str]] = []
    meal_type: Optional[str] = None
    is_veg: Optional[bool] = False
    price: Optional[float] = 10.99
    rating: Optional[float] = 4.5
    review_count: Optional[int] = 100
    restaurant_name: Optional[str] = "CravingAI Restaurant"
    restaurant_address: Optional[str] = "Global Cuisine District"
    image_url: Optional[str] = ""
    # Optional pre-filled enrichment (pipeline will auto-generate if missing)
    flavor_profile: Optional[List[str]] = None
    semantic_tags: Optional[List[str]] = None
    dietary_tags: Optional[List[str]] = None
    embedding_text: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    submitted: Optional[int] = None
    newly_indexed: int
    faiss_total: int
    elapsed_seconds: Optional[float] = None
    message: str


class StatsResponse(BaseModel):
    faiss_total: int
    tracked_in_registry: int
    catalog_dir: str
    embedding_mode: str
    catalog_files: List[str]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse, summary="Run delta ingestion pipeline")
async def run_ingestion():
    """
    Re-runs the food ingestion pipeline in delta mode.
    Only newly added or changed dishes in the catalog JSON files
    will be embedded and indexed — existing dishes are skipped.

    Use this after appending dishes to catalog.json.
    """
    try:
        app_logger.info("Admin: triggering delta ingestion pipeline...")
        stats = food_pipeline.run(force_reindex=False)
        return IngestResponse(
            status="success",
            newly_indexed=stats["newly_indexed"],
            faiss_total=stats["faiss_total"],
            elapsed_seconds=stats["elapsed_seconds"],
            message=(
                f"Delta ingestion complete. {stats['newly_indexed']} new dishes indexed. "
                f"FAISS now contains {stats['faiss_total']} dishes from a catalog of {stats['total_in_catalog']}."
            )
        )
    except Exception as e:
        app_logger.error(f"Admin ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline failed: {str(e)}")


@router.post("/reindex", response_model=IngestResponse, summary="Force full re-indexing of all dishes")
async def force_reindex():
    """
    Clears the FAISS index completely and re-embeds ALL dishes in the catalog.
    Use this after modifying existing dish descriptions/ingredients,
    or after upgrading the embedding model.

    ⚠️ This is a heavy operation — avoid during peak traffic.
    """
    try:
        app_logger.info("Admin: triggering FULL re-index (clearing FAISS)...")
        stats = food_pipeline.run(force_reindex=True)
        return IngestResponse(
            status="success",
            newly_indexed=stats["newly_indexed"],
            faiss_total=stats["faiss_total"],
            elapsed_seconds=stats["elapsed_seconds"],
            message=(
                f"Full re-index complete. {stats['newly_indexed']} dishes re-embedded. "
                f"FAISS total: {stats['faiss_total']}."
            )
        )
    except Exception as e:
        app_logger.error(f"Admin reindex failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


@router.post("/ingest/dishes", response_model=IngestResponse, summary="Ingest raw dish objects directly")
async def ingest_raw_dishes(dishes: List[RawDish]):
    """
    Ingest a list of raw dish objects directly via JSON POST body.
    The pipeline auto-enriches each dish (flavor profile, semantic tags, etc.)
    and indexes only new/changed ones.

    Example use: injecting dishes from an external API, web scraper,
    or data migration script without touching catalog files.
    """
    if not dishes:
        raise HTTPException(status_code=400, detail="No dishes provided.")
    if len(dishes) > 5000:
        raise HTTPException(status_code=400, detail="Maximum 5000 dishes per request.")

    try:
        raw = [d.dict(exclude_none=False) for d in dishes]
        # Auto-generate IDs for dishes that don't have one
        import hashlib, time
        for dish in raw:
            if not dish.get("id"):
                dish["id"] = hashlib.md5(f"{dish['name']}{dish['cuisine']}{time.time()}".encode()).hexdigest()[:12]

        result = food_pipeline.ingest_raw(raw)
        return IngestResponse(
            status="success",
            submitted=result["submitted"],
            newly_indexed=result["newly_indexed"],
            faiss_total=result["faiss_total"],
            message=(
                f"Ingested {result['submitted']} dishes. "
                f"{result['newly_indexed']} were new/changed and indexed. "
                f"FAISS total: {result['faiss_total']}."
            )
        )
    except Exception as e:
        app_logger.error(f"Raw dish ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/catalog/add", response_model=IngestResponse, summary="Upload a new catalog JSON file")
async def upload_catalog_file(file: UploadFile = File(...)):
    """
    Upload a new catalog JSON file directly to the catalog directory.
    The file must be a JSON object with a 'dishes' array.
    After upload, it is automatically ingested (delta mode).

    This enables a fully dynamic catalog expansion:
    add a new regional catalog file and it is immediately searchable.
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are accepted.")

    save_path = os.path.join(CATALOG_DIR, file.filename)
    try:
        content = await file.read()
        data = json.loads(content)
        if "dishes" not in data or not isinstance(data["dishes"], list):
            raise HTTPException(status_code=400, detail="JSON must have a 'dishes' array.")

        os.makedirs(CATALOG_DIR, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content)

        app_logger.info(f"Admin: uploaded new catalog file '{file.filename}' with {len(data['dishes'])} dishes.")

        # Ingest immediately
        stats = food_pipeline.run(catalog_path=save_path, force_reindex=False)
        return IngestResponse(
            status="success",
            submitted=len(data["dishes"]),
            newly_indexed=stats["newly_indexed"],
            faiss_total=stats["faiss_total"],
            elapsed_seconds=stats["elapsed_seconds"],
            message=(
                f"Catalog '{file.filename}' uploaded and ingested. "
                f"{stats['newly_indexed']} new dishes indexed. "
                f"FAISS total: {stats['faiss_total']}."
            )
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format.")
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Catalog upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/stats", response_model=StatsResponse, summary="Get index and pipeline statistics")
async def get_stats():
    """
    Returns current status of the FAISS index and food knowledge pipeline.
    """
    try:
        pipeline_stats = food_pipeline.get_stats()
        catalog_files = [
            f for f in os.listdir(CATALOG_DIR)
            if f.endswith(".json")
        ] if os.path.exists(CATALOG_DIR) else []

        return StatsResponse(
            faiss_total=pipeline_stats["faiss_total"],
            tracked_in_registry=pipeline_stats["tracked_in_registry"],
            catalog_dir=pipeline_stats["catalog_dir"],
            embedding_mode=pipeline_stats["embedding_mode"],
            catalog_files=catalog_files,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/catalog", summary="List all dishes currently indexed in FAISS")
async def list_catalog(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    cuisine: Optional[str] = Query(default=None),
):
    """
    List all dishes currently stored in FAISS with optional cuisine filter.
    Supports pagination via limit/offset.
    """
    try:
        all_items = faiss_store.get_all_items()
        if cuisine:
            all_items = [i for i in all_items if i.get("cuisine", "").lower() == cuisine.lower()]

        total = len(all_items)
        page = all_items[offset:offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "dishes": [
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "cuisine": d.get("cuisine"),
                    "country": d.get("country"),
                    "meal_type": d.get("meal_type"),
                    "is_veg": d.get("is_veg"),
                    "price": d.get("price"),
                    "rating": d.get("rating"),
                    "semantic_tags": d.get("semantic_tags", []),
                    "flavor_profile": d.get("flavor_profile", []),
                }
                for d in page
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Catalog listing failed: {str(e)}")


@router.delete("/clear", summary="Clear FAISS index (destructive)")
async def clear_index(confirm: str = Query(..., description="Must be 'CONFIRM' to proceed")):
    """
    Clears the entire FAISS index. This is destructive and irreversible
    without re-running ingestion. Pass confirm=CONFIRM to proceed.
    """
    if confirm != "CONFIRM":
        raise HTTPException(
            status_code=400,
            detail="Pass ?confirm=CONFIRM to confirm this destructive operation."
        )
    try:
        faiss_store.clear()
        food_pipeline._indexed_registry = {}
        food_pipeline._save_registry()
        return {"status": "cleared", "faiss_total": 0, "message": "FAISS index cleared. Run /api/admin/ingest to re-index."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")
