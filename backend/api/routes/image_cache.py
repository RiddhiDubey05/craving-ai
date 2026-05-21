from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import requests
import urllib.parse
from backend.services.food_pipeline import food_pipeline

router = APIRouter()

IMAGE_DIR = os.path.join("backend", "data", "images")
# Ensure the directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

# Helper to load the catalog once or whenever needed
# For scale, it's better to cache this in memory, but loading it is fast enough for <1000 items.
_catalog_cache = None

def get_dish_prompt(dish_id: str) -> str:
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = food_pipeline.load_catalog()
        _catalog_cache = food_pipeline.enrich(_catalog_cache)
        
    for dish in _catalog_cache:
        if dish.get("id") == dish_id:
            return dish.get("cinematic_prompt")
    return None

@router.get("/{dish_id}")
async def get_dish_image(dish_id: str):
    """
    Returns the cinematic AI-generated image for a dish.
    If it's already cached, returns the local file immediately.
    Otherwise, generates it using Pollinations.ai, saves it, and returns it.
    """
    filepath = os.path.join(IMAGE_DIR, f"{dish_id}.jpg")
    
    # 1. Return cached image if exists
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/jpeg")
        
    # 2. Find the cinematic prompt
    prompt = get_dish_prompt(dish_id)
    if not prompt:
        # Fallback prompt if dish is unknown
        prompt = f"Cinematic luxury food photography of dish {dish_id}, warm restaurant lighting, shallow depth of field, Pinterest aesthetic, highly detailed, 8k"
        
    # 3. Generate image via Pollinations.ai (Free, dynamic API)
    encoded_prompt = urllib.parse.quote(prompt)
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"
    
    try:
        response = requests.get(pollinations_url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return FileResponse(filepath, media_type="image/jpeg")
        else:
            raise HTTPException(status_code=500, detail="Failed to generate image")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
