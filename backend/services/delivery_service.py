"""
DeliveryService — Online Platform Price Comparison Layer
=========================================================
Generates realistic delivery platform comparisons per dish.

Real mode  : calls Claude via AWS Bedrock to generate contextually accurate
             platform pricing, ratings, and ETAs.
Fallback   : deterministic mock generator — realistic data seeded from base_price.

NOTE: Swiggy / Zomato do not provide public APIs.
      This layer uses LLM-generated mock data in dev mode with a standardised
      interface so real API integrations can be plugged in later.
"""
from __future__ import annotations

import json
import re
import random
from typing import Any, Dict, List, Optional

import boto3

from backend.config import get_settings
from backend.models.schemas import (
    DeliveryPlatformEntry,
    DeliveryComparisonResponse,
)
from backend.utils.logger import app_logger

settings = get_settings()

# ── Platform Config ─────────────────────────────────────────────────────────────
_PLATFORMS = [
    {
        "name":         "Swiggy",
        "markup":       1.08,          # 8 % platform markup
        "base_fee":     25.0,
        "min_order":    149.0,
        "url_template": "https://www.swiggy.com/search?query={dish}",
        "color":        "#FC8019",
    },
    {
        "name":         "Zomato",
        "markup":       1.10,
        "base_fee":     30.0,
        "min_order":    199.0,
        "url_template": "https://www.zomato.com/search?q={dish}",
        "color":        "#CB202D",
    },
    {
        "name":         "Uber Eats",
        "markup":       1.12,
        "base_fee":     35.0,
        "min_order":    None,
        "url_template": "https://www.ubereats.com/search?q={dish}",
        "color":        "#000000",
    },
]

_DISCOUNTS = [
    None,
    "20% off on first order",
    "Free delivery on orders above ₹299",
    "Flat ₹50 off using promo FOOD50",
    "Buy 1 Get 1 free on selected items",
    "30% off, up to ₹75",
]


class DeliveryService:
    def __init__(self):
        self.use_fallback = False
        is_placeholder = (
            settings.aws_access_key_id == "your_access_key_here"
            or not settings.aws_access_key_id
        )
        if is_placeholder:
            app_logger.info("DeliveryService: running in mock-generator mode (no AWS).")
            self.use_fallback = True
            self.bedrock_client = None
        else:
            try:
                self.bedrock_client = boto3.client(
                    "bedrock-runtime",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.bedrock_region,
                )
                app_logger.info("DeliveryService: AWS Bedrock client initialised.")
            except Exception as e:
                app_logger.error(f"DeliveryService: Bedrock init failed ({e}). Using mock.")
                self.use_fallback = True
                self.bedrock_client = None

    # ── Public API ──────────────────────────────────────────────────────────────

    def compare(
        self,
        dish_name: str,
        restaurant_name: str,
        base_price: float,
        location: Optional[str] = None,
    ) -> DeliveryComparisonResponse:
        """Return a full platform comparison for the given dish."""
        if self.use_fallback:
            return self._mock_compare(dish_name, restaurant_name, base_price)
        try:
            return self._llm_compare(dish_name, restaurant_name, base_price, location)
        except Exception as e:
            app_logger.warning(f"DeliveryService LLM failed ({e}), using mock.")
            return self._mock_compare(dish_name, restaurant_name, base_price)

    # ── LLM Generator ──────────────────────────────────────────────────────────

    def _llm_compare(
        self,
        dish_name: str,
        restaurant_name: str,
        base_price: float,
        location: Optional[str],
    ) -> DeliveryComparisonResponse:
        loc_hint = f" in {location}" if location else ""
        system_prompt = """You are a food delivery platform pricing analyst.
Given a dish and its base restaurant price, generate realistic delivery platform comparison data.
Return ONLY a valid JSON object in this exact schema:
{
  "platforms": [
    {
      "platform": "Swiggy",
      "price": <float>,
      "platform_rating": <float 3.5-5.0>,
      "delivery_time_minutes": <int 20-60>,
      "delivery_fee": <float>,
      "min_order_value": <float or null>,
      "discount": <string or null>,
      "available": true,
      "deep_link": "<url>"
    }
  ],
  "ai_recommendation": "<one sentence recommendation>"
}
Include Swiggy, Zomato, and Uber Eats. Make values realistic and varied."""

        user_content = (
            f"Dish: {dish_name}\n"
            f"Restaurant: {restaurant_name}{loc_hint}\n"
            f"Base price: ${base_price:.2f}"
        )
        messages = [{"role": "user", "content": [{"text": user_content}]}]
        response = self.bedrock_client.converse(
            modelId=settings.bedrock_llm_model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 600, "temperature": 0.4},
        )
        raw = response["output"]["message"]["content"][0]["text"].strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        data: Dict[str, Any] = json.loads(raw)
        return self._build_response(dish_name, restaurant_name, data["platforms"], data["ai_recommendation"])

    # ── Deterministic Mock Generator ───────────────────────────────────────────

    def _mock_compare(
        self,
        dish_name: str,
        restaurant_name: str,
        base_price: float,
    ) -> DeliveryComparisonResponse:
        # Use dish name as seed for stable (not random-on-every-call) output
        seed = sum(ord(c) for c in dish_name + restaurant_name)
        rng = random.Random(seed)

        platform_entries: List[Dict[str, Any]] = []
        for p in _PLATFORMS:
            price        = round(base_price * p["markup"] + rng.uniform(-1, 1.5), 2)
            rating       = round(rng.uniform(3.6, 4.9), 1)
            delivery_fee = round(p["base_fee"] + rng.uniform(-5, 10), 2)
            eta          = rng.randint(22, 55)
            discount     = rng.choice(_DISCOUNTS)
            deep_link    = p["url_template"].format(dish=dish_name.replace(" ", "+"))

            platform_entries.append({
                "platform":              p["name"],
                "price":                 price,
                "platform_rating":       rating,
                "delivery_time_minutes": eta,
                "delivery_fee":          delivery_fee,
                "min_order_value":       p["min_order"],
                "discount":              discount,
                "available":             True,
                "deep_link":             deep_link,
            })

        # Build AI recommendation text
        sorted_by_price  = sorted(platform_entries, key=lambda x: x["price"] + x["delivery_fee"])
        sorted_by_rating = sorted(platform_entries, key=lambda x: x["platform_rating"], reverse=True)
        bv = sorted_by_price[0]
        hr = sorted_by_rating[0]
        recommendation = (
            f"Order from **{bv['platform']}** for the best total price "
            f"(₹{bv['price']:.0f} + ₹{bv['delivery_fee']:.0f} delivery). "
            f"If rating matters most, **{hr['platform']}** scores highest at {hr['platform_rating']}⭐."
        )

        return self._build_response(dish_name, restaurant_name, platform_entries, recommendation)

    # ── Builder ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_response(
        dish_name: str,
        restaurant_name: str,
        raw_platforms: List[Dict[str, Any]],
        recommendation: str,
    ) -> DeliveryComparisonResponse:
        entries: List[DeliveryPlatformEntry] = []
        for p in raw_platforms:
            entries.append(DeliveryPlatformEntry(**{k: v for k, v in p.items()
                                                    if k in DeliveryPlatformEntry.model_fields}))

        if not entries:
            return DeliveryComparisonResponse(
                dish_name=dish_name,
                restaurant_name=restaurant_name,
                platforms=[],
                ai_recommendation="No platform data available.",
                latency_ms=0,
            )

        # Tag best value and highest rated
        best_value    = min(entries, key=lambda e: e.price + e.delivery_fee)
        highest_rated = max(entries, key=lambda e: e.platform_rating)
        best_value.is_best_value       = True
        highest_rated.is_highest_rated = True

        return DeliveryComparisonResponse(
            dish_name=dish_name,
            restaurant_name=restaurant_name,
            platforms=entries,
            best_value=best_value,
            highest_rated=highest_rated,
            ai_recommendation=recommendation,
            latency_ms=0,   # set by the route
        )


# Singleton
delivery_service = DeliveryService()
