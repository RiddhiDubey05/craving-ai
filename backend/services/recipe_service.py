"""
RecipeService — Cook-at-Home Recipe Generator
==============================================
Generates full home-cooking recipes for any dish.

Real mode  : calls Claude (AWS Bedrock) for creative, context-aware recipes
             returned as structured JSON.
Fallback   : template-based generator — produces realistic recipes offline
             using a curated bank of recipe patterns per cuisine.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

import boto3

from backend.config import get_settings
from backend.models.schemas import (
    CookAtHomeResponse,
    RecipeIngredient,
    RecipeStep,
)
from backend.utils.logger import app_logger

settings = get_settings()

# ── Template Recipe Bank ────────────────────────────────────────────────────────
# Used when AWS Bedrock is unavailable.

_TEMPLATE_RECIPES: Dict[str, Dict[str, Any]] = {
    "default": {
        "difficulty": "medium",
        "prep_time_minutes": 20,
        "cook_time_minutes": 30,
        "calories_per_serving": 450,
        "nutritional_highlights": ["balanced macros", "source of protein"],
        "storage_instructions": "Store in an airtight container in the fridge for up to 3 days.",
        "chef_tip": "Taste and adjust seasoning at every stage for the best results.",
        "ingredients": [
            {"name": "Main protein or vegetable", "quantity": "300", "unit": "grams",   "notes": "cut into bite-sized pieces"},
            {"name": "Onion",                     "quantity": "2",   "unit": "medium",  "notes": "finely chopped"},
            {"name": "Garlic",                    "quantity": "4",   "unit": "cloves",  "notes": "minced"},
            {"name": "Ginger",                    "quantity": "1",   "unit": "inch",    "notes": "grated"},
            {"name": "Tomatoes",                  "quantity": "3",   "unit": "medium",  "notes": "pureed"},
            {"name": "Cooking oil",               "quantity": "3",   "unit": "tbsp",    "notes": None},
            {"name": "Salt",                      "quantity": "1",   "unit": "tsp",     "notes": "to taste"},
            {"name": "Mixed spices",              "quantity": "2",   "unit": "tsp",     "notes": "adjust to taste"},
            {"name": "Fresh coriander",           "quantity": "2",   "unit": "tbsp",    "notes": "for garnish"},
            {"name": "Lemon juice",               "quantity": "1",   "unit": "tbsp",    "notes": "fresh squeezed"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Prepare all ingredients: chop, dice, and measure before starting.",                        "duration_minutes": 10, "tip": "Mise en place — preparation is the secret to stress-free cooking."},
            {"step_number": 2, "instruction": "Heat oil in a heavy-bottomed pan over medium-high heat.",                                   "duration_minutes": 2,  "tip": "The pan is ready when a drop of water sizzles immediately."},
            {"step_number": 3, "instruction": "Sauté onions until golden brown, about 8–10 minutes.",                                     "duration_minutes": 10, "tip": "Don't rush this step — caramelised onions build the base flavour."},
            {"step_number": 4, "instruction": "Add garlic and ginger. Cook for 2 minutes until fragrant.",                                 "duration_minutes": 2,  "tip": None},
            {"step_number": 5, "instruction": "Add tomatoes and cook until oil separates from the masala, about 8 minutes.",               "duration_minutes": 8,  "tip": "Oil separation is your signal that the base is fully cooked."},
            {"step_number": 6, "instruction": "Add spices and mix well. Toast for 1 minute to bloom the aromatics.",                       "duration_minutes": 1,  "tip": "Blooming spices in oil unlocks their full flavour."},
            {"step_number": 7, "instruction": "Add the main ingredient. Coat well with the masala and cook on medium heat.",                "duration_minutes": 15, "tip": None},
            {"step_number": 8, "instruction": "Add water or stock as needed. Simmer until the sauce reaches desired consistency.",          "duration_minutes": 10, "tip": "For a richer sauce, substitute water with coconut milk or cream."},
            {"step_number": 9, "instruction": "Finish with lemon juice and fresh coriander. Taste and adjust salt.",                       "duration_minutes": 1,  "tip": "Fresh herbs added at the end preserve their colour and aroma."},
            {"step_number": 10,"instruction": "Serve hot with your choice of bread, rice, or salad.",                                      "duration_minutes": 0,  "tip": None},
        ],
    },
    "Indian": {
        "difficulty": "medium",
        "prep_time_minutes": 25,
        "cook_time_minutes": 35,
        "calories_per_serving": 520,
        "nutritional_highlights": ["high protein", "rich in antioxidants", "anti-inflammatory spices"],
        "storage_instructions": "Keeps well refrigerated for 3–4 days. Tastes even better the next day.",
        "chef_tip": "Always fry your spices in oil for 30–60 seconds before adding liquids to maximise flavour.",
        "ingredients": [
            {"name": "Protein (chicken/paneer)",  "quantity": "400", "unit": "grams",   "notes": "cut into cubes"},
            {"name": "Onions",                    "quantity": "2",   "unit": "large",   "notes": "thinly sliced"},
            {"name": "Garlic paste",              "quantity": "1",   "unit": "tbsp",    "notes": None},
            {"name": "Ginger paste",              "quantity": "1",   "unit": "tbsp",    "notes": None},
            {"name": "Tomatoes",                  "quantity": "3",   "unit": "medium",  "notes": "pureed"},
            {"name": "Greek yoghurt",             "quantity": "4",   "unit": "tbsp",    "notes": "whisked"},
            {"name": "Heavy cream",               "quantity": "3",   "unit": "tbsp",    "notes": "optional"},
            {"name": "Garam masala",              "quantity": "1",   "unit": "tsp",     "notes": None},
            {"name": "Cumin seeds",               "quantity": "1",   "unit": "tsp",     "notes": None},
            {"name": "Turmeric",                  "quantity": "1/2", "unit": "tsp",     "notes": None},
            {"name": "Red chilli powder",         "quantity": "1",   "unit": "tsp",     "notes": "adjust to taste"},
            {"name": "Coriander powder",          "quantity": "2",   "unit": "tsp",     "notes": None},
            {"name": "Kasuri methi",              "quantity": "1",   "unit": "tsp",     "notes": "crushed"},
            {"name": "Butter or ghee",            "quantity": "2",   "unit": "tbsp",    "notes": None},
            {"name": "Fresh coriander",           "quantity": "3",   "unit": "tbsp",    "notes": "chopped, for garnish"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Marinate the protein in yoghurt, half the spices, and salt for at least 30 minutes (overnight is better).",  "duration_minutes": 5,  "tip": "Yoghurt tenderises protein and helps spices penetrate deeper."},
            {"step_number": 2, "instruction": "Heat butter/ghee in a heavy pan. Add cumin seeds and let them splutter for 30 seconds.",                      "duration_minutes": 2,  "tip": None},
            {"step_number": 3, "instruction": "Add sliced onions. Cook on medium-high heat for 12–15 minutes until deep golden.",                            "duration_minutes": 15, "tip": "Patient caramelisation is the soul of North Indian cooking."},
            {"step_number": 4, "instruction": "Add garlic and ginger paste. Sauté for 2 minutes.",                                                           "duration_minutes": 2,  "tip": None},
            {"step_number": 5, "instruction": "Add tomato puree. Cook on medium heat for 10 minutes until oil floats on top.",                               "duration_minutes": 10, "tip": "Do not add water — the tomatoes will release their own liquid."},
            {"step_number": 6, "instruction": "Add remaining dry spices. Stir and cook for 1–2 minutes.",                                                    "duration_minutes": 2,  "tip": "If the mix looks too dry, splash 2 tbsp of water to prevent burning."},
            {"step_number": 7, "instruction": "Add marinated protein. Mix well and cook on high heat for 5 minutes to seal.",                                "duration_minutes": 5,  "tip": None},
            {"step_number": 8, "instruction": "Reduce heat, cover and simmer for 15 minutes. Stir occasionally.",                                            "duration_minutes": 15, "tip": "Low and slow is the key to tender, flavourful results."},
            {"step_number": 9, "instruction": "Stir in cream (if using) and crushed kasuri methi. Simmer for 3 more minutes.",                               "duration_minutes": 3,  "tip": "Kasuri methi (dried fenugreek) is the secret ingredient in restaurant-style curries."},
            {"step_number": 10,"instruction": "Garnish with fresh coriander. Serve with naan, roti, or basmati rice.",                                       "duration_minutes": 0,  "tip": None},
        ],
    },
    "Italian": {
        "difficulty": "easy",
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "calories_per_serving": 480,
        "nutritional_highlights": ["good carbohydrate source", "lycopene from tomatoes"],
        "storage_instructions": "Refrigerate sauce separately from pasta. Combine when serving.",
        "chef_tip": "Use the starchy pasta water to emulsify the sauce — never rinse cooked pasta.",
        "ingredients": [
            {"name": "Pasta (spaghetti or penne)", "quantity": "200", "unit": "grams",  "notes": "dried"},
            {"name": "Olive oil (extra virgin)",   "quantity": "3",   "unit": "tbsp",   "notes": None},
            {"name": "Garlic",                     "quantity": "4",   "unit": "cloves", "notes": "thinly sliced"},
            {"name": "Canned plum tomatoes",       "quantity": "400", "unit": "grams",  "notes": "crushed by hand"},
            {"name": "Fresh basil",                "quantity": "10",  "unit": "leaves", "notes": None},
            {"name": "Parmesan cheese",            "quantity": "50",  "unit": "grams",  "notes": "freshly grated"},
            {"name": "Red chilli flakes",          "quantity": "1/2", "unit": "tsp",    "notes": "optional"},
            {"name": "Salt & black pepper",        "quantity": "1",   "unit": "tsp",    "notes": "to taste"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Bring a large pot of heavily salted water to a rolling boil.",                              "duration_minutes": 8,  "tip": "The water should taste like the sea. Salt is absorbed into the pasta during cooking."},
            {"step_number": 2, "instruction": "Cook pasta 2 minutes less than package says. Reserve 1 cup of pasta water before draining.", "duration_minutes": 8,  "tip": "Slightly undercooking pasta is intentional — it finishes in the sauce."},
            {"step_number": 3, "instruction": "While pasta cooks, heat olive oil over medium-low. Add garlic slices.",                     "duration_minutes": 3,  "tip": "Use medium-low heat — golden garlic is sweet; burnt garlic is bitter."},
            {"step_number": 4, "instruction": "Add chilli flakes and toast for 30 seconds, then add crushed tomatoes.",                   "duration_minutes": 1,  "tip": None},
            {"step_number": 5, "instruction": "Simmer the sauce on medium for 10 minutes. Season with salt and pepper.",                   "duration_minutes": 10, "tip": "Add a pinch of sugar if the tomatoes taste too acidic."},
            {"step_number": 6, "instruction": "Add drained pasta to the sauce. Toss vigorously, adding pasta water splash by splash.",    "duration_minutes": 2,  "tip": "The starchy water helps the sauce cling perfectly to each strand."},
            {"step_number": 7, "instruction": "Plate and finish with torn fresh basil and generous parmesan. Serve immediately.",          "duration_minutes": 1,  "tip": "Never add parmesan while the pan is still on very high heat — it will clump."},
        ],
    },
    "Japanese": {
        "difficulty": "hard",
        "prep_time_minutes": 30,
        "cook_time_minutes": 180,
        "calories_per_serving": 580,
        "nutritional_highlights": ["high collagen from bone broth", "complete protein", "probiotic miso"],
        "storage_instructions": "Store broth and toppings separately. Reheat broth gently — do not boil miso.",
        "chef_tip": "The best ramen broth is simmered for at least 6 hours. For a weeknight version, use quality store-bought chicken stock.",
        "ingredients": [
            {"name": "Ramen noodles",             "quantity": "200", "unit": "grams",   "notes": "fresh or dried"},
            {"name": "Chicken/pork bones",        "quantity": "500", "unit": "grams",   "notes": "for broth"},
            {"name": "White miso paste",          "quantity": "3",   "unit": "tbsp",    "notes": None},
            {"name": "Soy sauce",                 "quantity": "2",   "unit": "tbsp",    "notes": None},
            {"name": "Mirin",                     "quantity": "1",   "unit": "tbsp",    "notes": None},
            {"name": "Sesame oil",                "quantity": "1",   "unit": "tsp",     "notes": None},
            {"name": "Soft-boiled eggs",          "quantity": "2",   "unit": "",        "notes": "marinated in soy & mirin"},
            {"name": "Chashu pork or chicken",    "quantity": "150", "unit": "grams",   "notes": "braised, sliced"},
            {"name": "Nori sheets",               "quantity": "4",   "unit": "",        "notes": None},
            {"name": "Green onions",              "quantity": "3",   "unit": "stalks",  "notes": "finely sliced"},
            {"name": "Bean sprouts",              "quantity": "100", "unit": "grams",   "notes": "blanched"},
            {"name": "Bamboo shoots",             "quantity": "50",  "unit": "grams",   "notes": "canned, drained"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Blanch bones in boiling water for 5 min. Drain and rinse under cold water to remove impurities.", "duration_minutes": 10, "tip": "This step gives your broth a clear, clean appearance."},
            {"step_number": 2, "instruction": "Simmer blanched bones in fresh water for 3–6 hours over low heat. Skim foam regularly.",           "duration_minutes": 180,"tip": "Never let the broth boil vigorously — a gentle simmer keeps it clear."},
            {"step_number": 3, "instruction": "For soft-boiled eggs: boil 6.5 min, ice bath 5 min, peel and marinate in soy/mirin/water (1:1:4).", "duration_minutes": 15, "tip": "Marinate eggs for at least 4 hours — overnight gives a beautiful dark colour."},
            {"step_number": 4, "instruction": "Strain the finished broth. Season with soy sauce and mirin.",                                       "duration_minutes": 5,  "tip": None},
            {"step_number": 5, "instruction": "Whisk miso paste into a ladleful of warm broth until dissolved, then add back to pot.",             "duration_minutes": 2,  "tip": "Never boil miso — heat destroys beneficial probiotics and dulls the flavour."},
            {"step_number": 6, "instruction": "Cook ramen noodles per package instructions. Drain well.",                                          "duration_minutes": 3,  "tip": "Shake off excess water — you don't want to dilute the precious broth."},
            {"step_number": 7, "instruction": "Assemble: noodles in bowl, ladle hot broth over. Arrange toppings: egg, chashu, nori, onions.",     "duration_minutes": 3,  "tip": "Warm your bowls with hot water before serving so the ramen stays hot longer."},
        ],
    },
    "American": {
        "difficulty": "easy",
        "prep_time_minutes": 15,
        "cook_time_minutes": 10,
        "calories_per_serving": 650,
        "nutritional_highlights": ["high protein", "rich in iron"],
        "storage_instructions": "Best eaten fresh. Store uncooked patties covered in fridge for up to 24 hours.",
        "chef_tip": "Do NOT press the patty while cooking. That squeezes out all the precious juices.",
        "ingredients": [
            {"name": "Ground beef (80/20 fat ratio)", "quantity": "250", "unit": "grams",  "notes": "per serving"},
            {"name": "Burger buns",                   "quantity": "2",   "unit": "",       "notes": "brioche preferred"},
            {"name": "American cheese slices",        "quantity": "2",   "unit": "",       "notes": None},
            {"name": "Lettuce leaves",                "quantity": "4",   "unit": "",       "notes": "iceberg or romaine"},
            {"name": "Tomato",                        "quantity": "1",   "unit": "medium", "notes": "thickly sliced"},
            {"name": "Red onion",                     "quantity": "1/2", "unit": "medium", "notes": "thinly sliced"},
            {"name": "Pickles",                       "quantity": "6",   "unit": "slices", "notes": None},
            {"name": "Mayonnaise",                    "quantity": "2",   "unit": "tbsp",   "notes": None},
            {"name": "Ketchup",                       "quantity": "2",   "unit": "tbsp",   "notes": None},
            {"name": "Mustard",                       "quantity": "1",   "unit": "tsp",    "notes": None},
            {"name": "Salt & black pepper",           "quantity": "1",   "unit": "tsp",    "notes": "to taste"},
            {"name": "Butter",                        "quantity": "1",   "unit": "tbsp",   "notes": "for toasting buns"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Season ground beef with salt and pepper. Form into patties slightly wider than the bun (they shrink).", "duration_minutes": 5, "tip": "Make a small indent in the centre of each patty to prevent doming while cooking."},
            {"step_number": 2, "instruction": "Heat cast-iron skillet or grill to very high heat (until smoking slightly).",                           "duration_minutes": 3, "tip": "A screaming hot surface creates the Maillard crust that makes burgers irresistible."},
            {"step_number": 3, "instruction": "Cook patties 3 min per side without moving. Add cheese in the last minute and cover to melt.",          "duration_minutes": 6, "tip": "Do NOT press the patty. Ever. This is the golden rule of burger-making."},
            {"step_number": 4, "instruction": "Toast buns cut-side down in butter until golden.",                                                      "duration_minutes": 2, "tip": "A toasted bun won't go soggy from the burger juices."},
            {"step_number": 5, "instruction": "Mix mayo, ketchup, and mustard for the special sauce. Spread on bun.",                                  "duration_minutes": 1, "tip": None},
            {"step_number": 6, "instruction": "Layer: bottom bun, sauce, lettuce, tomato, patty, onion, pickles, top bun. Serve immediately.",        "duration_minutes": 1, "tip": "Always put lettuce under the patty — it insulates the bun from juice."},
        ],
    },
}


class RecipeService:
    def __init__(self):
        self.use_fallback = False
        is_placeholder = (
            settings.aws_access_key_id == "your_access_key_here"
            or not settings.aws_access_key_id
        )
        if is_placeholder:
            app_logger.info("RecipeService: running in template-generator mode (no AWS).")
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
                app_logger.info("RecipeService: AWS Bedrock client initialised.")
            except Exception as e:
                app_logger.error(f"RecipeService: Bedrock init failed ({e}). Using templates.")
                self.use_fallback = True
                self.bedrock_client = None

    # ── Public API ──────────────────────────────────────────────────────────────

    def generate(
        self,
        dish_name: str,
        cuisine: Optional[str],
        servings: int,
        dietary_restrictions: List[str],
        difficulty_preference: str,
    ) -> CookAtHomeResponse:
        t0 = time.time()
        if self.use_fallback:
            result = self._template_generate(dish_name, cuisine, servings, dietary_restrictions)
        else:
            try:
                result = self._llm_generate(dish_name, cuisine, servings, dietary_restrictions, difficulty_preference)
            except Exception as e:
                app_logger.warning(f"RecipeService LLM failed ({e}), using template.")
                result = self._template_generate(dish_name, cuisine, servings, dietary_restrictions)
        result.latency_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ── LLM Generator ──────────────────────────────────────────────────────────

    def _llm_generate(
        self,
        dish_name: str,
        cuisine: Optional[str],
        servings: int,
        dietary_restrictions: List[str],
        difficulty_preference: str,
    ) -> CookAtHomeResponse:
        restrictions_str = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
        system_prompt = f"""You are a world-class chef creating a detailed home-cooking recipe.
Return ONLY a valid JSON object with this exact schema:
{{
  "dish_name": "<string>",
  "cuisine": "<string>",
  "difficulty": "<easy|medium|hard>",
  "servings": {servings},
  "prep_time_minutes": <int>,
  "cook_time_minutes": <int>,
  "total_time_minutes": <int>,
  "calories_per_serving": <int or null>,
  "ingredients": [
    {{"name": "<string>", "quantity": "<string>", "unit": "<string>", "notes": "<string or null>"}}
  ],
  "steps": [
    {{"step_number": <int>, "instruction": "<string>", "duration_minutes": <int or null>, "tip": "<string or null>"}}
  ],
  "storage_instructions": "<string or null>",
  "nutritional_highlights": ["<string>"],
  "chef_tip": "<string>"
}}
dietary restrictions: {restrictions_str}
difficulty preference: {difficulty_preference}
servings: {servings}"""

        user_content = f"Create a detailed home recipe for: {dish_name}" + (f" ({cuisine} cuisine)" if cuisine else "")
        messages = [{"role": "user", "content": [{"text": user_content}]}]
        response = self.bedrock_client.converse(
            modelId=settings.bedrock_llm_model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 2000, "temperature": 0.5},
        )
        raw = response["output"]["message"]["content"][0]["text"].strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        data: Dict[str, Any] = json.loads(raw)
        return self._build_response(data)

    # ── Template Generator ──────────────────────────────────────────────────────

    def _template_generate(
        self,
        dish_name: str,
        cuisine: Optional[str],
        servings: int,
        dietary_restrictions: List[str],
    ) -> CookAtHomeResponse:
        # Select best matching template
        template = _TEMPLATE_RECIPES.get(cuisine or "default", _TEMPLATE_RECIPES["default"])

        # Scale ingredient quantities to servings (base = 2)
        scale = servings / 2
        ingredients = []
        for ing in template["ingredients"]:
            qty = ing["quantity"]
            try:
                qty = str(round(float(qty) * scale, 1))
            except (ValueError, TypeError):
                pass   # Non-numeric quantities like "1/2" are left as-is
            ingredients.append(RecipeIngredient(
                name=ing["name"],
                quantity=qty,
                unit=ing["unit"],
                notes=ing.get("notes"),
            ))

        steps = [RecipeStep(**s) for s in template["steps"]]
        total = template["prep_time_minutes"] + template["cook_time_minutes"]

        # Apply vegan substitution hint
        highlights = list(template["nutritional_highlights"])
        if "vegan" in dietary_restrictions:
            highlights.append("vegan-adaptable — swap dairy for coconut milk/cream")

        return CookAtHomeResponse(
            dish_name=dish_name,
            cuisine=cuisine or "International",
            difficulty=template["difficulty"],
            servings=servings,
            prep_time_minutes=template["prep_time_minutes"],
            cook_time_minutes=template["cook_time_minutes"],
            total_time_minutes=total,
            calories_per_serving=template.get("calories_per_serving"),
            ingredients=ingredients,
            steps=steps,
            storage_instructions=template.get("storage_instructions"),
            nutritional_highlights=highlights,
            chef_tip=template.get("chef_tip"),
            latency_ms=0,   # set by caller
        )

    @staticmethod
    def _build_response(data: Dict[str, Any]) -> CookAtHomeResponse:
        ingredients = [RecipeIngredient(**i) for i in data.get("ingredients", [])]
        steps       = [RecipeStep(**s)       for s in data.get("steps", [])]
        return CookAtHomeResponse(
            dish_name=data.get("dish_name", ""),
            cuisine=data.get("cuisine", "International"),
            difficulty=data.get("difficulty", "medium"),
            servings=data.get("servings", 2),
            prep_time_minutes=data.get("prep_time_minutes", 0),
            cook_time_minutes=data.get("cook_time_minutes", 0),
            total_time_minutes=data.get("total_time_minutes", 0),
            calories_per_serving=data.get("calories_per_serving"),
            ingredients=ingredients,
            steps=steps,
            storage_instructions=data.get("storage_instructions"),
            nutritional_highlights=data.get("nutritional_highlights", []),
            chef_tip=data.get("chef_tip"),
            latency_ms=0,
        )


# Singleton
recipe_service = RecipeService()
