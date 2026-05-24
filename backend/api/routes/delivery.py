"""
Delivery Comparison Routes — POST /api/delivery-comparison  |  GET /api/delivery/compare
"""
import time
import random
from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    DeliveryComparisonRequest,
    DeliveryComparisonResponse,
)
from backend.services.delivery_service import delivery_service
from backend.utils.logger import app_logger

router = APIRouter(prefix="/api", tags=["Delivery Comparison"])


@router.post("/delivery-comparison", response_model=DeliveryComparisonResponse)
async def get_delivery_comparison(req: DeliveryComparisonRequest):
    """
    Compare delivery platform pricing, ratings, and ETAs for a specific dish.
    Returns Swiggy, Zomato, and Uber Eats options plus AI-powered
    best-value and highest-rated recommendations.

    Note: Platform data is AI-generated for demonstration purposes.
    Plug in real Swiggy/Zomato API credentials to enable live data.
    """
    t0 = time.time()
    app_logger.info(
        f"Delivery comparison requested for '{req.dish_name}' @ {req.restaurant_name}"
    )
    try:
        result = delivery_service.compare(
            dish_name=req.dish_name,
            restaurant_name=req.restaurant_name,
            base_price=req.base_price,
            location=req.location,
        )
        result.latency_ms = round((time.time() - t0) * 1000, 2)
        app_logger.info(
            f"Delivery comparison completed in {result.latency_ms:.1f}ms | "
            f"{len(result.platforms)} platforms returned"
        )
        return result
    except Exception as e:
        app_logger.error(f"Delivery comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delivery comparison failed: {str(e)}")


@router.get("/delivery/compare")
async def delivery_compare_get(dish_price: float = Query(default=12.0, description="Base dish price")):
    """
    GET convenience endpoint for the app.js frontend.
    Returns mocked platform comparison data for the given dish_price.
    """
    platforms = [
        {"platform": "Swiggy", "logo": "🍊", "rating": round(3.8 + random.random() * 1.1, 1),
         "eta_minutes": random.randint(22, 45), "delivery_fee": round(1.5 + random.random() * 2.5, 2),
         "discount": round(random.choice([0, 0, 0.5, 1.0, 1.5]), 2), "is_best_value": False},
        {"platform": "Zomato", "logo": "🔴", "rating": round(3.9 + random.random() * 1.0, 1),
         "eta_minutes": random.randint(18, 40), "delivery_fee": round(1.0 + random.random() * 2.0, 2),
         "discount": round(random.choice([0, 0, 0.5, 1.0]), 2), "is_best_value": False},
        {"platform": "Uber Eats", "logo": "⚡", "rating": round(4.0 + random.random() * 0.9, 1),
         "eta_minutes": random.randint(20, 38), "delivery_fee": round(2.0 + random.random() * 2.0, 2),
         "discount": 0.0, "is_best_value": False},
    ]
    # Compute totals and mark best value
    for p in platforms:
        p["total_price"] = round(dish_price + p["delivery_fee"] - p["discount"], 2)
    best = min(platforms, key=lambda x: x["total_price"])
    best["is_best_value"] = True
    return platforms
