import uuid
import time
from fastapi import APIRouter, HTTPException
from typing import List

from backend.db.faiss_store import faiss_store
from backend.services.embedding_service import embedding_service
from backend.services.llm_service import llm_service
from backend.models.schemas import ChatRequest, ChatResponse, DishResult
from backend.utils.logger import app_logger

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_assistant(req: ChatRequest):
    """
    Conversational Recommendation Assistant (Conversational RAG).
    Embeds the user's message to retrieve relevant dishes from FAISS,
    and calls Bedrock (Claude) to hold a dialogue with context injected.
    """
    start_time = time.time()
    app_logger.info(f"Received chat message: '{req.message}'")

    try:
        # 1. Retrieve relevant context dishes from FAISS
        query_emb = embedding_service.get_text_embedding(req.message)
        raw_results = faiss_store.search(
            query_embedding=query_emb,
            top_k=req.top_k
        )

        # 2. Extract dish metadata for LLM context injection
        retrieved_dishes_meta = [meta for meta, _ in raw_results]

        # 3. Format history for LLM service
        history_list = []
        for msg in req.history:
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })

        # 4. Invoke conversational model
        reply = llm_service.chat_recommendation(
            user_message=req.message,
            history=history_list,
            retrieved_dishes=retrieved_dishes_meta
        )

        # 5. Format matching dishes for response schema
        recommended_dishes = []
        for rank, (meta, score) in enumerate(raw_results, 1):
            dish_result = DishResult(
                id=meta["id"],
                name=meta["name"],
                description=meta["description"],
                cuisine=meta["cuisine"],
                restaurant_name=meta["restaurant_name"],
                restaurant_address=meta["restaurant_address"],
                price=meta["price"],
                rating=meta["rating"],
                review_count=meta["review_count"],
                image_url=meta.get("image_url"),
                tags=meta.get("tags", []),
                is_veg=meta.get("is_veg", False),
                spice_level=meta.get("spice_level", 2),
                score=score,
                reasoning=None,  # Chat response has its own dialog explanation
                rank=rank
            )
            recommended_dishes.append(dish_result)

        session_id = req.session_id or str(uuid.uuid4())
        latency = (time.time() - start_time) * 1000
        app_logger.info(f"Chat recommendation response completed in {latency:.2f}ms")

        return ChatResponse(
            reply=reply,
            recommendations=recommended_dishes,
            session_id=session_id,
            latency_ms=latency
        )

    except Exception as e:
        app_logger.error(f"Error in chat assistant route: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat assistant error: {str(e)}"
        )
