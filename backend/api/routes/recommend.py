"""
Recommendation Routes — Semantic Retrieval Engine
==================================================
Query pipeline:

  User Query
    ↓
  Query Preprocessing + Alias Expansion (FoodOntology)
    ↓
  Embedding Generation (Bedrock Titan / food-semantic-local)
    ↓
  FAISS Candidate Retrieval (top-N broad search)
    ↓
  SemanticReranker
      - food concept overlap score   (35%)
      - cuisine family boost          (25%)
      - ingredient/keyword match      (20%)
      - dietary intent match          (10%)
      - popularity signal             (10%)
    ↓
  LLM Reasoning per top-K result
    ↓
  Return ranked results
"""
import os
import time
import json
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any, Set

from backend.api.routes.auth import get_current_user_id
from backend.db.db_manager import db_manager
from backend.db.faiss_store import faiss_store
from backend.services.embedding_service import embedding_service
from backend.services.llm_service import llm_service
from backend.services.craving_service import craving_service
from backend.services.food_ontology import food_ontology
from backend.models.schemas import (
    TextQueryRequest,
    MultimodalQueryRequest,
    QueryResponse,
    EnrichedQueryResponse,
    DishResult,
    CravingProfile,
)
from backend.utils.logger import app_logger
from backend.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api", tags=["Recommendations"])

CACHE_DIR = os.path.join("data", "embeddings")


# ══════════════════════════════════════════════════════════════════════════════
#  QUERY PREPROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_query(query: str) -> Dict[str, Any]:
    """
    Expand a raw user query into a rich semantic representation.

    Returns:
        raw_query      : original user text
        expanded_query : alias-expanded version for embedding
        concepts       : set of food concept tokens
        wants_veg      : True if user explicitly wants vegetarian/vegan
        wants_nonveg   : True if user explicitly wants meat/seafood
        cuisine_hints  : list of cuisine names detected in query
        flavor_hints   : list of flavors detected
        meal_hints     : list of meal type hints
    """
    q_lower = query.lower().strip()

    # ── Expand via food ontology ──────────────────────────────────────
    expanded = food_ontology.expand_query(query)
    concepts = food_ontology.get_query_concepts(query)

    # ── Dietary intent ────────────────────────────────────────────────
    veg_keywords = {"veg", "vegetarian", "vegan", "plant-based", "meatless", "veggie", "no meat"}
    nonveg_keywords = {"chicken", "beef", "pork", "lamb", "mutton", "fish", "seafood",
                       "shrimp", "prawn", "tuna", "salmon", "duck", "crab", "lobster",
                       "meat", "non-veg", "nonveg"}
    wants_veg = any(k in q_lower for k in veg_keywords)
    wants_nonveg = any(k in q_lower for k in nonveg_keywords)

    # ── Cuisine detection ─────────────────────────────────────────────
    known_cuisines = [
        "Japanese", "Korean", "Chinese", "Thai", "Vietnamese", "Indian",
        "Italian", "French", "Mexican", "American", "Mediterranean",
        "Middle Eastern", "Malaysian", "Singaporean", "Indonesian",
        "African", "Ethiopian", "Moroccan", "Latin American", "Peruvian",
        "Colombian", "Argentine", "Turkish", "Lebanese", "Greek",
        "Spanish", "British", "German", "Taiwanese", "Filipino",
    ]
    cuisine_hints = [c for c in known_cuisines if c.lower() in q_lower]

    # ── Flavor hints ──────────────────────────────────────────────────
    flavor_words = ["spicy", "creamy", "sweet", "savory", "tangy", "smoky",
                    "aromatic", "rich", "light", "umami", "crispy", "fresh"]
    flavor_hints = [f for f in flavor_words if f in q_lower]

    # ── Meal type hints ───────────────────────────────────────────────
    meal_words = ["breakfast", "lunch", "dinner", "dessert", "snack", "brunch", "beverage"]
    meal_hints = [m for m in meal_words if m in q_lower]

    return {
        "raw_query": query,
        "expanded_query": f"{query} {expanded}",
        "concepts": concepts,
        "wants_veg": wants_veg,
        "wants_nonveg": wants_nonveg,
        "cuisine_hints": cuisine_hints,
        "flavor_hints": flavor_hints,
        "meal_hints": meal_hints,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SEMANTIC RERANKER
# ══════════════════════════════════════════════════════════════════════════════

class SemanticReranker:
    """
    Multi-signal reranker that scores each candidate dish against the query context.

    Scoring formula:
      final = 0.35 * concept_overlap
            + 0.25 * cuisine_family_score
            + 0.20 * keyword_match
            + 0.10 * dietary_match
            + 0.10 * popularity_score

    The 35% weight on concept_overlap replaces the 45% weight that was
    previously given to random FAISS similarity scores — now it's real
    semantic relevance based on food concept intersection.
    """

    def score(
        self,
        dish: Dict[str, Any],
        faiss_sim: float,
        query_ctx: Dict[str, Any],
        cuisine_filter: Optional[str] = None,
        craving_profile: Optional[CravingProfile] = None,
    ) -> float:

        # ── 1. Food concept overlap (35%) ─────────────────────────────
        query_concepts: Set[str] = query_ctx.get("concepts", set())
        dish_concepts = food_ontology.get_dish_concepts(dish)
        concept_score = food_ontology.compute_concept_overlap(query_concepts, dish_concepts)

        # Boost if FAISS also agrees (secondary signal, weighted low)
        blended_semantic = 0.70 * concept_score + 0.30 * faiss_sim
        w_sem = 0.35

        # ── 2. Cuisine family score (25%) ─────────────────────────────
        w_cui = 0.25
        s_cui = 0.0
        dish_cuisine = dish.get("cuisine", "")
        cuisine_hints: List[str] = query_ctx.get("cuisine_hints", [])
        inferred_cuisines = (
            craving_profile.inferred_cuisines if craving_profile and craving_profile.inferred_cuisines else []
        )
        all_target_cuisines = cuisine_hints + inferred_cuisines + ([cuisine_filter] if cuisine_filter else [])

        for target in all_target_cuisines:
            if dish_cuisine.lower() == target.lower():
                s_cui = 1.0
                break
            if food_ontology.cuisines_are_related(dish_cuisine, target):
                s_cui = max(s_cui, 0.6)  # partial credit for same family

        # If no explicit cuisine target, check if dish cuisine appears in query concepts
        if not all_target_cuisines:
            if dish_cuisine.lower() in query_concepts:
                s_cui = 0.8

        # ── 3. Keyword match (20%) ────────────────────────────────────
        w_kw = 0.20
        s_kw = 0.0
        raw_query = query_ctx.get("raw_query", "").lower()
        stop_words = {"a","an","the","in","with","of","for","to","and","or",
                      "some","i","want","like","crave","craving","order",
                      "food","dish","me","please","give","show","find"}
        query_tokens = [
            w.strip(".,!?\"'") for w in raw_query.split()
            if len(w) > 2 and w.strip(".,!?\"'") not in stop_words
        ]

        if query_tokens:
            name_lower = dish.get("name", "").lower()
            desc_lower = dish.get("description", "").lower()
            all_aliases = " ".join(dish.get("aliases", [])).lower()
            all_tags = " ".join(dish.get("semantic_tags", []) + dish.get("tags", [])).lower()
            ingredients = " ".join(dish.get("ingredients", [])).lower()

            hits = 0
            for token in query_tokens:
                if (token in name_lower or token in desc_lower or
                        token in all_aliases or token in all_tags or
                        token in ingredients):
                    hits += 1
            s_kw = min(hits / len(query_tokens), 1.0)

        # ── 4. Dietary intent match (10%) ─────────────────────────────
        w_diet = 0.10
        s_diet = 1.0
        is_veg = dish.get("is_veg", False)
        wants_veg = query_ctx.get("wants_veg", False)
        wants_nonveg = query_ctx.get("wants_nonveg", False)

        if wants_veg and not is_veg:
            s_diet = 0.0  # Hard mismatch — never show meat to a vegan query
        elif wants_nonveg and is_veg:
            s_diet = 0.4  # Soft mismatch
        elif craving_profile and craving_profile.dietary_signals:
            wants_veg_from_profile = any("veg" in sig.lower() for sig in craving_profile.dietary_signals)
            if wants_veg_from_profile and not is_veg:
                s_diet = 0.0

        # ── 5. Popularity signal (10%) ────────────────────────────────
        w_pop = 0.10
        rating = dish.get("rating", 4.0)
        reviews = dish.get("review_count", 100)
        pop_score = dish.get("popularity_score", 80)
        s_pop = (pop_score / 100.0) * 0.5 + (rating / 5.0) * 0.3 + (min(reviews, 500) / 500.0) * 0.2
        s_pop = min(max(s_pop, 0.0), 1.0)

        final = (
            w_sem * blended_semantic +
            w_cui * s_cui +
            w_kw  * s_kw +
            w_diet * s_diet +
            w_pop * s_pop
        )
        return round(float(final), 4)

    def rerank(
        self,
        candidates: List[tuple],  # List of (meta, faiss_sim)
        query_ctx: Dict[str, Any],
        cuisine_filter: Optional[str] = None,
        craving_profile: Optional[CravingProfile] = None,
        top_k: int = 10,
    ) -> List[tuple]:  # List of (meta, final_score)
        """Score all candidates and return top_k sorted by final_score."""
        scored = []
        seen_ids: set = set()

        for meta, faiss_sim in candidates:
            dish_id = meta.get("id", meta.get("name", ""))
            if dish_id in seen_ids:
                continue
            seen_ids.add(dish_id)

            score = self.score(
                dish=meta,
                faiss_sim=faiss_sim,
                query_ctx=query_ctx,
                cuisine_filter=cuisine_filter,
                craving_profile=craving_profile,
            )
            scored.append((meta, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


_reranker = SemanticReranker()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_cached_image_embedding(image_id: str) -> List[float]:
    cache_path = os.path.join(CACHE_DIR, f"{image_id}.json")
    if not os.path.exists(cache_path):
        raise HTTPException(
            status_code=404,
            detail=f"Uploaded image ID {image_id} not found or expired."
        )
    try:
        with open(cache_path, "r") as f:
            data = json.load(f)
        return data["embedding"]
    except Exception as e:
        app_logger.error(f"Failed to load cached embedding for {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Error reading cached image embedding.")


def _build_dish_result(meta: Dict[str, Any], score: float, rank: int, reasoning: str) -> DishResult:
    return DishResult(
        id=meta.get("id", meta.get("name", f"dish_{rank}")),
        name=meta["name"],
        description=meta["description"],
        cuisine=meta["cuisine"],
        restaurant_name=meta["restaurant_name"],
        restaurant_address=meta["restaurant_address"],
        price=meta["price"],
        rating=meta["rating"],
        review_count=meta.get("review_count", 100),
        image_url=meta.get("image_url", ""),
        tags=meta.get("tags", []),
        is_veg=meta.get("is_veg", False),
        spice_level=int(meta.get("spice_level", 0)) if str(meta.get("spice_level", "0")).isdigit() else 2,
        score=score,
        reasoning=reasoning,
        rank=rank,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TEXT QUERY ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/query", response_model=QueryResponse)
async def query_recommendations(
    req: TextQueryRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
):
    """
    Semantic food search with hybrid reranking.

    Pipeline:
      1. Preprocess + expand query via FoodOntology
      2. Embed expanded query
      3. Broad FAISS candidate retrieval
      4. SemanticReranker scores all candidates
      5. LLM generates reasoning for top-K
      6. Return ranked results
    """
    start_time = time.time()
    app_logger.info(f"Text query: '{req.query}'")

    try:
        # ── Step 0: User Profile Injection ────────────────────────────
        if user_id:
            profile = db_manager.get_user_profile(user_id)
            if profile and profile.get("preferences"):
                prefs = profile["preferences"]
                
                # Force vegetarian mode if user selected it
                if "Vegetarian" in prefs or "Vegan" in prefs:
                    req.veg_only = True
                    app_logger.info("Forced veg_only=True based on user profile.")
                
                # Semantic query augmentation for flavors
                augments = []
                if "Spicy" in prefs and "spicy" not in req.query.lower():
                    augments.append("spicy")
                if "Gluten-Free" in prefs and "gluten" not in req.query.lower():
                    augments.append("gluten-free")
                    
                if augments:
                    req.query = f"{req.query} {' '.join(augments)}"
                    app_logger.info(f"Augmented query with profile preferences: '{req.query}'")
        # ── Step 1: Optional craving analysis ────────────────────────
        craving_profile = None
        if req.include_craving_analysis:
            try:
                craving_profile = craving_service.analyze(req.query)
            except Exception as ce:
                app_logger.warning(f"Craving analysis skipped: {ce}")

        # ── Step 2: Query preprocessing + expansion ───────────────────
        query_ctx = preprocess_query(req.query)
        app_logger.info(
            f"Query concepts: {list(query_ctx['concepts'])[:10]} | "
            f"cuisine hints: {query_ctx['cuisine_hints']} | "
            f"wants_veg: {query_ctx['wants_veg']}"
        )

        # ── Step 3: Embed the EXPANDED query (richer signal) ─────────
        embed_text = query_ctx["expanded_query"]
        query_emb = embedding_service.get_text_embedding(embed_text)

        # ── Step 4: Broad FAISS retrieval ────────────────────────────
        # Retrieve generously — reranker filters down to top_k
        total_in_index = faiss_store.index.ntotal if faiss_store.index else 0
        candidate_k = min(total_in_index, max(req.top_k * 10, 80))

        raw_results = faiss_store.search(
            query_embedding=query_emb,
            top_k=candidate_k,
            cuisine_filter=req.cuisine_filter,
            max_price=req.max_price,
            min_rating=req.min_rating,
            veg_only=req.veg_only,
        )

        query_summary_note = ""
        if not raw_results:
            app_logger.info("No results with filters — relaxing to unfiltered fallback.")
            raw_results = faiss_store.search(
                query_embedding=query_emb,
                top_k=candidate_k,
                veg_only=req.veg_only,
            )
            query_summary_note = " (Some filters relaxed to find relevant results)"

        if not raw_results:
            return QueryResponse(
                results=[],
                total_found=0,
                query_summary=f"No dishes found for '{req.query}'",
                latency_ms=(time.time() - start_time) * 1000,
                model_used=settings.bedrock_llm_model_id,
            )

        # ── Step 5: Semantic reranking ────────────────────────────────
        reranked = _reranker.rerank(
            candidates=raw_results,
            query_ctx=query_ctx,
            cuisine_filter=req.cuisine_filter,
            craving_profile=craving_profile,
            top_k=req.top_k,
        )

        # ── Step 6: Build results with LLM reasoning ──────────────────
        final_results: List[DishResult] = []
        for rank, (meta, score) in enumerate(reranked, 1):
            reasoning = llm_service.get_recommendation_reasoning(req.query, meta)
            final_results.append(_build_dish_result(meta, score, rank, reasoning))

        # ── Optional sort override ────────────────────────────────────
        if req.sort_by == "price_low":
            final_results.sort(key=lambda x: x.price)
        elif req.sort_by == "price_high":
            final_results.sort(key=lambda x: x.price, reverse=True)
        elif req.sort_by == "rating":
            final_results.sort(key=lambda x: x.rating, reverse=True)
        for i, item in enumerate(final_results, 1):
            item.rank = i

        latency = (time.time() - start_time) * 1000
        app_logger.info(
            f"Query '{req.query}' → top result: '{reranked[0][0]['name']}' "
            f"(score={reranked[0][1]}) | {latency:.0f}ms"
        )

        # ── Log to user craving history ───────────────────────────────
        if user_id and req.query:
            try:
                db_manager.add_craving_log(
                    user_id=user_id,
                    query=req.query,
                    craving_type=craving_profile.craving_type if craving_profile else None,
                    mood=craving_profile.mood if craving_profile else None,
                )
            except Exception as le:
                app_logger.warning(f"Failed to log craving history: {le}")

        summary = f"Dishes curated for: '{req.query}'{query_summary_note}"

        if craving_profile is not None:
            return EnrichedQueryResponse(
                results=final_results,
                total_found=len(final_results),
                query_summary=summary,
                latency_ms=latency,
                model_used=settings.bedrock_llm_model_id,
                craving_profile=craving_profile,
            )

        return QueryResponse(
            results=final_results,
            total_found=len(final_results),
            query_summary=summary,
            latency_ms=latency,
            model_used=settings.bedrock_llm_model_id,
        )

    except Exception as e:
        app_logger.error(f"Text query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Recommendation query failed: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
#  MULTIMODAL QUERY ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/multimodal-query", response_model=QueryResponse)
async def query_multimodal_recommendations(
    req: MultimodalQueryRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
):
    """
    Combined Image + Text Query with semantic reranking.
    Blends image and text embeddings weighted by req.text_weight / req.image_weight,
    then reranks candidates using SemanticReranker.
    """
    start_time = time.time()

    if not req.query and not req.image_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'query' text or an uploaded 'image_id'."
        )

    try:
        # ── Resolve embeddings ────────────────────────────────────────
        text_emb: Optional[List[float]] = None
        image_emb: Optional[List[float]] = None
        query_ctx = {}
        summary = ""

        if req.query:
            query_ctx = preprocess_query(req.query)
            text_emb = embedding_service.get_text_embedding(query_ctx["expanded_query"])

        if req.image_id:
            image_emb = _get_cached_image_embedding(req.image_id)

        # ── Blend embeddings ──────────────────────────────────────────
        if text_emb and image_emb:
            combined = (
                req.text_weight * np.array(text_emb, dtype=np.float32) +
                req.image_weight * np.array(image_emb, dtype=np.float32)
            )
            norm = np.linalg.norm(combined)
            query_emb = (combined / norm if norm > 0 else combined).tolist()
            summary = f"Visual + text match for: '{req.query}'"
        elif text_emb:
            query_emb = text_emb
            summary = f"Text match for: '{req.query}'"
        else:
            query_emb = image_emb
            summary = "Visual match for uploaded dish image"

        # ── FAISS retrieval ───────────────────────────────────────────
        total_in_index = faiss_store.index.ntotal if faiss_store.index else 0
        candidate_k = min(total_in_index, max(req.top_k * 10, 80))

        raw_results = faiss_store.search(
            query_embedding=query_emb,
            top_k=candidate_k,
            cuisine_filter=req.cuisine_filter,
            max_price=req.max_price,
            veg_only=req.veg_only,
        )

        if not raw_results:
            raw_results = faiss_store.search(
                query_embedding=query_emb,
                top_k=candidate_k,
                veg_only=req.veg_only,
            )
            summary += " (Filters relaxed)"

        # ── Semantic reranking ────────────────────────────────────────
        reranked = _reranker.rerank(
            candidates=raw_results,
            query_ctx=query_ctx if query_ctx else {"raw_query": "", "concepts": set()},
            cuisine_filter=req.cuisine_filter,
            top_k=req.top_k,
        )

        # ── Build results ─────────────────────────────────────────────
        final_results: List[DishResult] = []
        for rank, (meta, score) in enumerate(reranked, 1):
            query_text = req.query or f"an image of {meta['name']}"
            reasoning = llm_service.get_recommendation_reasoning(query_text, meta)
            final_results.append(_build_dish_result(meta, score, rank, reasoning))

        latency = (time.time() - start_time) * 1000

        if user_id and req.query:
            try:
                db_manager.add_craving_log(user_id=user_id, query=req.query, craving_type=None, mood=None)
            except Exception:
                pass

        return QueryResponse(
            results=final_results,
            total_found=len(final_results),
            query_summary=summary,
            latency_ms=latency,
            model_used=settings.bedrock_llm_model_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Multimodal query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multimodal search failed: {str(e)}")
