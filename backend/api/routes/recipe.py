"""
Cook-at-Home Recipe Route — POST /api/cook-at-home
"""
from fastapi import APIRouter, HTTPException

from backend.models.schemas import CookAtHomeRequest, CookAtHomeResponse
from backend.services.recipe_service import recipe_service
from backend.utils.logger import app_logger

router = APIRouter(prefix="/api", tags=["Cook at Home"])


@router.post("/cook-at-home", response_model=CookAtHomeResponse)
async def cook_at_home(req: CookAtHomeRequest):
    """
    Generate a full home-cooking recipe for a dish — including
    ingredients list, step-by-step instructions with chef tips,
    estimated cooking time, calorie count, and storage advice.

    Works with any dish name. Cuisine hint improves recipe specificity.
    """
    app_logger.info(
        f"Recipe generation requested for '{req.dish_name}' "
        f"(cuisine={req.cuisine}, servings={req.servings})"
    )
    try:
        result = recipe_service.generate(
            dish_name=req.dish_name,
            cuisine=req.cuisine,
            servings=req.servings,
            dietary_restrictions=req.dietary_restrictions,
            difficulty_preference=req.difficulty_preference,
        )
        app_logger.info(
            f"Recipe generated in {result.latency_ms:.1f}ms | "
            f"{len(result.ingredients)} ingredients, {len(result.steps)} steps"
        )
        return result
    except Exception as e:
        app_logger.error(f"Recipe generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")


@router.get("/recipe/generate")
async def recipe_generate_get(dish_name: str = "delicious dish"):
    """
    GET convenience endpoint consumed by app.js.
    Wraps the recipe_service using defaults and returns a flat dict.
    """
    try:
        result = recipe_service.generate(
            dish_name=dish_name,
            cuisine=None,
            servings=2,
            dietary_restrictions=[],
            difficulty_preference="medium",
        )
        # Serialize ingredients to display strings  e.g. "300 grams chicken (cut into pieces)"
        ingredients_list = []
        for ing in result.ingredients:
            qty_unit = f"{ing.quantity} {ing.unit}".strip()
            line = f"{qty_unit} {ing.name}"
            if ing.notes:
                line += f" ({ing.notes})"
            ingredients_list.append(line)

        # Serialize steps to plain instruction strings
        steps_list = [step.instruction for step in result.steps]

        # Format time fields
        prep = f"{result.prep_time_minutes} mins" if result.prep_time_minutes else "10 mins"
        cook = f"{result.cook_time_minutes} mins" if result.cook_time_minutes else "20 mins"

        return {
            "title": result.dish_name,
            "prep_time": prep,
            "cook_time": cook,
            "ingredients": ingredients_list,
            "instructions": steps_list,
            "chef_tips": result.chef_tip or result.storage_instructions or "",
        }
    except Exception as e:
        app_logger.error(f"Recipe GET failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")


