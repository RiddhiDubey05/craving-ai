from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from backend.db.db_manager import db_manager
from backend.api.routes.auth import require_user_id

router = APIRouter(prefix="/api/profile", tags=["User Profile"])

# Pydantic Schemas
class FavoriteDishRequest(BaseModel):
    id: str
    name: str
    cuisine: str
    price: float
    rating: float
    restaurant_name: str
    image_url: Optional[str] = None

class SavedRecipeRequest(BaseModel):
    dish_id: str
    title: str
    prep_time: str
    cook_time: str
    ingredients: List[str]
    instructions: List[str]
    chef_tips: Optional[str] = ""


@router.get("/favorites")
async def list_favorites(user_id: int = Depends(require_user_id)):
    return db_manager.get_favorites(user_id)


@router.post("/favorites")
async def add_favorite(req: FavoriteDishRequest, user_id: int = Depends(require_user_id)):
    success = db_manager.add_favorite(user_id, req.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add to favorites.")
    return {"message": "Dish added to favorites successfully."}


@router.delete("/favorites/{dish_id}")
async def remove_favorite(dish_id: str, user_id: int = Depends(require_user_id)):
    success = db_manager.remove_favorite(user_id, dish_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove from favorites.")
    return {"message": "Dish removed from favorites successfully."}


@router.get("/recipes")
async def list_recipes(user_id: int = Depends(require_user_id)):
    return db_manager.get_saved_recipes(user_id)


@router.post("/recipes")
async def save_recipe(req: SavedRecipeRequest, user_id: int = Depends(require_user_id)):
    success = db_manager.save_recipe(
        user_id=user_id,
        dish_id=req.dish_id,
        title=req.title,
        prep_time=req.prep_time,
        cook_time=req.cook_time,
        ingredients=req.ingredients,
        instructions=req.instructions,
        chef_tips=req.chef_tips
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save recipe.")
    return {"message": "Recipe saved successfully."}


@router.delete("/recipes/{recipe_id}")
async def remove_recipe(recipe_id: int, user_id: int = Depends(require_user_id)):
    success = db_manager.remove_recipe(user_id, recipe_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete recipe.")
    return {"message": "Recipe deleted successfully."}


@router.get("/history")
async def list_history(user_id: int = Depends(require_user_id)):
    return db_manager.get_craving_logs(user_id)
