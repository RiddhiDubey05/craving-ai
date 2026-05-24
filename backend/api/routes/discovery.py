from fastapi import APIRouter
from typing import List, Optional
from backend.db.faiss_store import faiss_store
from backend.models.schemas import DishResult

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])

@router.get("/trending", response_model=List[DishResult])
async def get_trending(limit: int = 6):
    """Returns dishes with the highest review count globally."""
    items = faiss_store.get_all_items()
    # Sort by review_count descending, default to 0 if missing
    sorted_items = sorted(items, key=lambda x: x.get("review_count", 0), reverse=True)
    return [DishResult(**item, score=1.0, rank=idx+1) for idx, item in enumerate(sorted_items[:limit])]

@router.get("/hidden-gems", response_model=List[DishResult])
async def get_hidden_gems(limit: int = 6):
    """Returns dishes with high ratings but low review counts (Hidden Gems)."""
    items = faiss_store.get_all_items()
    # Filter: rating >= 4.7 and review_count < 150
    filtered = [
        item for item in items 
        if item.get("rating", 0) >= 4.7 and item.get("review_count", 0) < 150
    ]
    # Sort by rating descending
    sorted_items = sorted(filtered, key=lambda x: x.get("rating", 0), reverse=True)
    
    # If not enough hidden gems, fallback to highly rated
    if len(sorted_items) < limit:
        sorted_items = sorted(items, key=lambda x: x.get("rating", 0), reverse=True)
        
    return [DishResult(**item, score=1.0, rank=idx+1) for idx, item in enumerate(sorted_items[:limit])]

@router.get("/budget", response_model=List[DishResult])
async def get_budget_friendly(limit: int = 6):
    """Returns highest rated dishes under $15.00."""
    items = faiss_store.get_all_items()
    # Filter: price < 15.0
    filtered = [
        item for item in items 
        if item.get("price", 999) < 15.0
    ]
    # Sort by rating descending
    sorted_items = sorted(filtered, key=lambda x: x.get("rating", 0), reverse=True)
    return [DishResult(**item, score=1.0, rank=idx+1) for idx, item in enumerate(sorted_items[:limit])]
