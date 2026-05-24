"""
Craving Analyzer Route — POST /api/analyze-craving
"""
import time
from fastapi import APIRouter, HTTPException

from backend.models.schemas import CravingAnalyzeRequest, CravingProfile
from backend.services.craving_service import craving_service
from backend.utils.logger import app_logger

router = APIRouter(prefix="/api", tags=["Craving Analyzer"])


@router.post("/analyze-craving", response_model=CravingProfile)
async def analyze_craving(req: CravingAnalyzeRequest):
    """
    Analyze free-text food craving / mood description and return a
    structured CravingProfile with inferred cuisines, dietary signals,
    budget hint, spice level, and a refined search query suggestion.
    """
    t0 = time.time()
    app_logger.info(f"Craving analysis requested for: '{req.query}'")
    try:
        profile = craving_service.analyze(req.query)
        latency = (time.time() - t0) * 1000
        app_logger.info(f"Craving analysis completed in {latency:.1f}ms | type={profile.craving_type} mood={profile.mood}")
        return profile
    except Exception as e:
        app_logger.error(f"Craving analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Craving analysis failed: {str(e)}")
