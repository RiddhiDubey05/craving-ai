"""
Pydantic schemas for request/response models across all API routes.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class CuisineType(str, Enum):
    INDIAN = "Indian"
    CHINESE = "Chinese"
    ITALIAN = "Italian"
    MEXICAN = "Mexican"
    JAPANESE = "Japanese"
    THAI = "Thai"
    AMERICAN = "American"
    MEDITERRANEAN = "Mediterranean"
    CONTINENTAL = "Continental"
    STREET_FOOD = "Street Food"
    OTHER = "Other"


class SortBy(str, Enum):
    RELEVANCE = "relevance"
    RATING = "rating"
    PRICE_LOW = "price_low"
    PRICE_HIGH = "price_high"


# ── Restaurant / Dish entities ────────────────────────────────────────────────

class DishMeta(BaseModel):
    """Metadata stored alongside each FAISS vector."""
    id: str
    name: str
    description: str
    cuisine: str
    restaurant_name: str
    restaurant_address: str
    price: float
    rating: float
    review_count: int
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_veg: bool = False
    spice_level: int = Field(default=2, ge=0, le=5)  # 0=none, 5=extra hot


class DishResult(DishMeta):
    """A single search result with relevance score and LLM reasoning."""
    score: float = Field(description="Cosine similarity score 0-1")
    reasoning: Optional[str] = Field(
        default=None, description="LLM-generated explanation"
    )
    rank: int = Field(description="Position in ranked list (1-indexed)")


# ── Upload ────────────────────────────────────────────────────────────────────

class ImageUploadResponse(BaseModel):
    image_id: str
    s3_url: str
    embedding_dim: int
    latency_ms: float
    message: str = "Image uploaded and embedded successfully"


# ── Query ─────────────────────────────────────────────────────────────────────

class TextQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    cuisine_filter: Optional[str] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    veg_only: bool = False
    sort_by: SortBy = SortBy.RELEVANCE
    include_craving_analysis: bool = Field(
        default=False,
        description="When True, runs Craving Analyzer before FAISS search and enriches response"
    )


class MultimodalQueryRequest(BaseModel):
    query: Optional[str] = Field(default=None, max_length=500)
    image_id: Optional[str] = Field(
        default=None, description="image_id returned by /upload-image"
    )
    top_k: int = Field(default=5, ge=1, le=20)
    text_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    image_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    cuisine_filter: Optional[str] = None
    max_price: Optional[float] = None
    veg_only: bool = False


class QueryResponse(BaseModel):
    results: List[DishResult]
    total_found: int
    query_summary: str
    latency_ms: float
    model_used: str


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list)
    session_id: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=10)


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[DishResult] = Field(default_factory=list)
    session_id: str
    latency_ms: float


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    faiss_index_size: int
    services: Dict[str, Any]
    version: str = "1.0.0"


# ── Craving / Mood Analyzer ────────────────────────────────────────────────────

class CravingAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500,
                       description="Free-text craving or mood description")


class CravingProfile(BaseModel):
    """Structured output from the Craving Analyzer Service."""
    craving_type: str = Field(
        description="e.g. 'comfort', 'healthy', 'indulgent', 'refreshing', 'adventurous'"
    )
    mood: str = Field(
        description="e.g. 'stressed', 'celebratory', 'late_night', 'light', 'romantic'"
    )
    inferred_cuisines: List[str] = Field(
        default_factory=list,
        description="Most likely cuisine types matching this craving"
    )
    dietary_signals: List[str] = Field(
        default_factory=list,
        description="e.g. ['vegetarian', 'high-protein', 'gluten-free']"
    )
    budget_hint: str = Field(
        default="moderate",
        description="'budget' | 'moderate' | 'premium'"
    )
    spice_preference: int = Field(
        default=2, ge=0, le=5,
        description="Inferred spice level 0 (none) to 5 (extra hot)"
    )
    occasion: str = Field(
        default="any",
        description="e.g. 'dinner', 'quick_lunch', 'date_night', 'family_meal'"
    )
    temperature_preference: str = Field(
        default="any",
        description="'hot' | 'cold' | 'any'"
    )
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0,
        description="Confidence score of the craving analysis (0-1)"
    )
    suggested_query: Optional[str] = Field(
        default=None,
        description="Refined, optimised search query generated by the analyzer"
    )


# ── Delivery Platform Comparison ───────────────────────────────────────────────

class DeliveryComparisonRequest(BaseModel):
    dish_name: str = Field(..., min_length=2)
    restaurant_name: str = Field(..., min_length=2)
    base_price: float = Field(..., gt=0)
    location: Optional[str] = Field(default=None, description="City / locality hint")


class DeliveryPlatformEntry(BaseModel):
    """A single delivery platform's offer for a dish."""
    platform: str              # "Swiggy" | "Zomato" | "Uber Eats"
    price: float               # Final price including platform markup
    platform_rating: float     # Rating on that platform
    delivery_time_minutes: int
    delivery_fee: float
    min_order_value: Optional[float] = None
    discount: Optional[str] = None   # e.g. "20% off on first order"
    available: bool = True
    deep_link: str             # Placeholder URL / CTA link
    is_best_value: bool = False
    is_highest_rated: bool = False


class DeliveryComparisonResponse(BaseModel):
    dish_name: str
    restaurant_name: str
    platforms: List[DeliveryPlatformEntry]
    best_value: Optional[DeliveryPlatformEntry] = None
    highest_rated: Optional[DeliveryPlatformEntry] = None
    ai_recommendation: str = Field(
        description="One-line AI suggestion on where to order from"
    )
    latency_ms: float


# ── Cook at Home — Recipe Generator ───────────────────────────────────────────

class CookAtHomeRequest(BaseModel):
    dish_name: str = Field(..., min_length=2)
    cuisine: Optional[str] = None
    servings: int = Field(default=2, ge=1, le=12)
    dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="e.g. ['vegan', 'gluten-free', 'nut-free']"
    )
    difficulty_preference: str = Field(
        default="any",
        description="'easy' | 'medium' | 'hard' | 'any'"
    )


class RecipeIngredient(BaseModel):
    name: str
    quantity: str         # e.g. "200", "1/2", "a pinch"
    unit: str             # e.g. "grams", "cups", "tbsp", ""
    notes: Optional[str] = None  # e.g. "finely chopped", "room temperature"


class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None
    tip: Optional[str] = None    # Chef tip for this step


class CookAtHomeResponse(BaseModel):
    dish_name: str
    cuisine: str
    difficulty: str         # "easy" | "medium" | "hard"
    servings: int
    prep_time_minutes: int
    cook_time_minutes: int
    total_time_minutes: int
    calories_per_serving: Optional[int] = None
    ingredients: List[RecipeIngredient]
    steps: List[RecipeStep]
    storage_instructions: Optional[str] = None
    nutritional_highlights: List[str] = Field(default_factory=list)
    chef_tip: Optional[str] = None
    latency_ms: float


# ── Enriched Query Response (optional craving enrichment) ─────────────────────

class EnrichedQueryResponse(BaseModel):
    """Extends QueryResponse with optional craving analysis."""
    results: List[DishResult]
    total_found: int
    query_summary: str
    latency_ms: float
    model_used: str
    craving_profile: Optional[CravingProfile] = None

