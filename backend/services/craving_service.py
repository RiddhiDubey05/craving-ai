"""
CravingService — Mood & Craving Analyzer
=========================================
Accepts a free-text user query and extracts a structured CravingProfile.

Real mode  : calls Claude via AWS Bedrock (structured JSON extraction prompt)
Fallback   : keyword-based rule engine — works 100% offline with zero AWS config
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import boto3

from backend.config import get_settings
from backend.models.schemas import CravingProfile
from backend.utils.logger import app_logger

settings = get_settings()

# ── Keyword Rule Tables ─────────────────────────────────────────────────────────

_CRAVING_RULES = {
    "comfort":     ["comforting", "comfort", "hearty", "soul", "warm", "homey", "cozy", "rich"],
    "healthy":     ["healthy", "light", "lean", "salad", "green", "detox", "clean", "fresh", "nutritious", "protein"],
    "indulgent":   ["cheesy", "creamy", "decadent", "indulgent", "fried", "loaded", "rich", "sinful", "cheat"],
    "refreshing":  ["cold", "cool", "drink", "juice", "smoothie", "ice", "summer", "chilled", "lemonade"],
    "adventurous": ["exotic", "new", "try", "adventure", "different", "fusion", "street"],
    "sweet":       ["sweet", "dessert", "cake", "chocolate", "candy", "pastry", "sugar"],
    "spicy":       ["spicy", "hot", "chilli", "pepper", "fiery", "burning"],
}

_MOOD_RULES = {
    "stressed":      ["stressful", "stressed", "tired", "exhausted", "hard day", "rough"],
    "celebratory":   ["celebrate", "party", "special", "birthday", "anniversary", "treat"],
    "late_night":    ["late night", "midnight", "2am", "night craving", "late"],
    "light":         ["light", "not too heavy", "easy", "digestible", "quick"],
    "romantic":      ["date", "romantic", "valentine", "anniversary", "partner", "couple"],
    "energetic":     ["energy", "boost", "workout", "gym", "pre-workout", "post-workout"],
}

_CUISINE_KEYWORDS: Dict[str, List[str]] = {
    "Indian":        ["indian", "curry", "masala", "biryani", "naan", "dal", "paneer", "tikka", "samosa"],
    "Italian":       ["italian", "pizza", "pasta", "risotto", "parmesan", "tiramisu", "calzone"],
    "Chinese":       ["chinese", "noodles", "fried rice", "dim sum", "dumpling", "wonton", "stir fry"],
    "Japanese":      ["japanese", "sushi", "ramen", "sashimi", "tempura", "miso", "teriyaki", "udon"],
    "American":      ["american", "burger", "hot dog", "bbq", "wings", "fries", "mac and cheese"],
    "Mediterranean": ["mediterranean", "falafel", "hummus", "shawarma", "kebab", "gyro", "pita"],
    "Thai":          ["thai", "pad thai", "green curry", "satay", "tom yum"],
    "Mexican":       ["mexican", "taco", "burrito", "enchilada", "guacamole", "nachos"],
}

_DIETARY_KEYWORDS = {
    "vegetarian":  ["vegetarian", "veg", "no meat", "meatless", "plant"],
    "vegan":       ["vegan", "dairy-free", "plant-based", "no animal"],
    "high-protein":["protein", "gym", "muscle", "high protein", "chicken breast", "egg white"],
    "gluten-free": ["gluten", "gluten-free", "celiac"],
    "low-carb":    ["low carb", "keto", "no rice", "no bread"],
    "sugar-free":  ["sugar-free", "diabetic", "no sugar"],
}

_BUDGET_KEYWORDS = {
    "budget":   ["cheap", "budget", "affordable", "inexpensive", "economical", "value"],
    "premium":  ["premium", "luxury", "fine dining", "expensive", "splurge", "fancy"],
}

_SPICE_KEYWORDS = {
    0: ["mild", "no spice", "bland", "not spicy"],
    1: ["little spicy", "slightly spicy", "mild spice"],
    2: ["medium", "moderate spice"],
    3: ["spicy", "spiced"],
    4: ["very spicy", "extra spicy", "fiery"],
    5: ["extremely spicy", "ghost pepper", "insanely hot"],
}

_OCCASION_KEYWORDS = {
    "date_night":    ["date", "romantic", "valentine"],
    "quick_lunch":   ["quick", "fast", "lunch", "office"],
    "family_dinner": ["family", "kids", "children", "dinner party"],
    "late_night":    ["late night", "midnight", "night craving"],
    "breakfast":     ["breakfast", "morning", "brunch"],
    "party":         ["party", "birthday", "celebration", "gathering"],
}

_TEMP_KEYWORDS = {
    "hot":  ["hot", "warm", "steaming", "piping hot", "comforting warm"],
    "cold": ["cold", "chilled", "ice", "frozen", "cool", "refreshing", "summer"],
}


class CravingService:
    def __init__(self):
        self.use_fallback = False
        is_placeholder = (
            settings.aws_access_key_id == "your_access_key_here"
            or not settings.aws_access_key_id
        )
        if is_placeholder:
            app_logger.info("CravingService: running in keyword rule-engine mode (no AWS).")
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
                app_logger.info("CravingService: AWS Bedrock client initialised.")
            except Exception as e:
                app_logger.error(f"CravingService: Bedrock init failed ({e}). Using fallback.")
                self.use_fallback = True
                self.bedrock_client = None

    # ── Public API ──────────────────────────────────────────────────────────────

    def analyze(self, query: str) -> CravingProfile:
        """Return a structured CravingProfile for the given free-text query."""
        if self.use_fallback:
            return self._rule_based_analyze(query)
        try:
            return self._llm_analyze(query)
        except Exception as e:
            app_logger.warning(f"CravingService LLM failed ({e}), using fallback.")
            return self._rule_based_analyze(query)

    # ── LLM Extraction ──────────────────────────────────────────────────────────

    def _llm_analyze(self, query: str) -> CravingProfile:
        system_prompt = """You are a food craving analyst. Given a user food query, extract and return a
structured JSON object with these exact fields:
{
  "craving_type": "<one of: comfort|healthy|indulgent|refreshing|adventurous|sweet|spicy>",
  "mood": "<one of: stressed|celebratory|late_night|light|romantic|energetic|neutral>",
  "inferred_cuisines": ["<cuisine1>", "<cuisine2>"],
  "dietary_signals": ["<e.g. vegetarian|high-protein|gluten-free>"],
  "budget_hint": "<one of: budget|moderate|premium>",
  "spice_preference": <integer 0-5>,
  "occasion": "<one of: dinner|quick_lunch|date_night|family_meal|breakfast|party|any>",
  "temperature_preference": "<one of: hot|cold|any>",
  "confidence": <float 0.0-1.0>,
  "suggested_query": "<refined search query string>"
}
Return ONLY the JSON object, no other text."""

        messages = [{"role": "user", "content": [{"text": f"Food query: \"{query}\""}]}]
        response = self.bedrock_client.converse(
            modelId=settings.bedrock_llm_model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.2},
        )
        raw = response["output"]["message"]["content"][0]["text"].strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        data: Dict[str, Any] = json.loads(raw)
        return CravingProfile(**data)

    # ── Keyword Rule Engine Fallback ────────────────────────────────────────────

    def _rule_based_analyze(self, query: str) -> CravingProfile:
        q = query.lower()

        craving_type = self._match_first(q, _CRAVING_RULES, default="comfort")
        mood         = self._match_first(q, _MOOD_RULES,    default="neutral")
        inferred_cuisines = self._match_all(q, _CUISINE_KEYWORDS)
        dietary_signals   = self._match_all(q, _DIETARY_KEYWORDS)
        budget_hint  = self._match_first(q, _BUDGET_KEYWORDS, default="moderate")
        occasion     = self._match_first(q, _OCCASION_KEYWORDS, default="any")
        temp_pref    = self._match_first(q, _TEMP_KEYWORDS, default="any")

        # Spice inference
        spice = 2
        for level in sorted(_SPICE_KEYWORDS.keys(), reverse=True):
            if any(kw in q for kw in _SPICE_KEYWORDS[level]):
                spice = level
                break

        # Confidence: higher when more signals found
        signals_found = (
            (craving_type != "comfort") +
            (mood != "neutral") +
            bool(inferred_cuisines) +
            bool(dietary_signals) +
            (budget_hint != "moderate")
        )
        confidence = min(0.6 + signals_found * 0.08, 0.97)

        # Build a cleaner suggested query
        parts = [craving_type, "food"]
        if inferred_cuisines:
            parts.insert(0, inferred_cuisines[0])
        if dietary_signals:
            parts.append(dietary_signals[0])
        suggested_query = " ".join(parts)

        return CravingProfile(
            craving_type=craving_type,
            mood=mood,
            inferred_cuisines=inferred_cuisines or [],
            dietary_signals=dietary_signals,
            budget_hint=budget_hint,
            spice_preference=spice,
            occasion=occasion,
            temperature_preference=temp_pref,
            confidence=round(confidence, 2),
            suggested_query=suggested_query,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _match_first(query: str, rules: Dict[str, List[str]], default: str) -> str:
        for label, keywords in rules.items():
            if any(kw in query for kw in keywords):
                return label
        return default

    @staticmethod
    def _match_all(query: str, rules: Dict[str, List[str]]) -> List[str]:
        matches = []
        for label, keywords in rules.items():
            if any(kw in query for kw in keywords):
                matches.append(label)
        return matches


# Singleton
craving_service = CravingService()
