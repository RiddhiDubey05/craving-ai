from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from backend.db.db_manager import db_manager
from backend.api.routes.auth import require_user_id

router = APIRouter()

class AddToCartRequest(BaseModel):
    dish_id: str
    name: str
    price: float
    image_url: str
    restaurant_name: str

class RemoveFromCartRequest(BaseModel):
    dish_id: str

@router.get("/", response_model=List[Dict[str, Any]])
async def get_cart(user_id: int = Depends(require_user_id)):
    return db_manager.get_cart(user_id)

@router.post("/add")
async def add_to_cart(req: AddToCartRequest, user_id: int = Depends(require_user_id)):
    success = db_manager.add_to_cart(
        user_id, req.dish_id, req.name, req.price, req.image_url, req.restaurant_name
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add item to cart")
    return {"message": "Added to cart"}

@router.post("/remove")
async def remove_from_cart(req: RemoveFromCartRequest, user_id: int = Depends(require_user_id)):
    success = db_manager.remove_from_cart(user_id, req.dish_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove item from cart")
    return {"message": "Removed from cart"}

@router.post("/checkout")
async def checkout(user_id: int = Depends(require_user_id)):
    order_id = db_manager.checkout(user_id)
    if not order_id:
        raise HTTPException(status_code=400, detail="Cart is empty or checkout failed")
    return {"message": "Order placed successfully", "order_id": order_id}

@router.post("/clear")
async def clear_cart(user_id: int = Depends(require_user_id)):
    success = db_manager.clear_cart(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear cart")
    return {"message": "Cart cleared"}
