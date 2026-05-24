"""
FoodIngestionPipeline — Scalable Global Food Knowledge Indexer
==============================================================
Architecture:
  Global Food Catalog (JSON files)
    ↓
  Auto-Metadata Enrichment   (FoodOntology)
    ↓
  Embedding Text Construction (dense semantic string per dish)
    ↓
  Embedding Generation        (Bedrock Titan OR food-semantic vectors)
    ↓
  Incremental FAISS Indexing  (only unindexed dishes get embedded)
    ↓
  Save → Persist to disk

Key design principles:
  - Catalog-driven: dishes live in JSON files, not in Python code
  - Incremental: only new/changed dishes are re-embedded (delta indexing)
  - Auto-enriched: every raw dish gets flavor_profile, semantic_tags,
    meal_type, dietary_tags, and embedding_text auto-generated
  - Scalable: supports 10k+ dishes with FAISS IndexFlatIP (<500k items)
    or upgrade to IndexIVFFlat for millions
  - Runtime ingestible: POST /api/admin/ingest can add new dishes
    without any server restart
"""
from __future__ import annotations

import os
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Set

from backend.db.faiss_store import faiss_store
from backend.services.embedding_service import embedding_service
from backend.services.food_ontology import food_ontology, QUERY_CONCEPT_MAP, INGREDIENT_CONCEPT_MAP
from backend.utils.logger import app_logger


# ── CATALOG DIRECTORY ────────────────────────────────────────────────────────
CATALOG_DIR = os.path.join("backend", "data", "food_knowledge")
INDEX_REGISTRY_PATH = os.path.join("data", "faiss_index", "indexed_ids.json")


# ── AUTO-ENRICHMENT RULES ────────────────────────────────────────────────────
# Maps tokens in name/description/ingredients → semantic tags
_SEMANTIC_TRIGGERS: List[tuple] = [
    # Category tags
    (["ramen", "pho", "laksa", "udon", "soba", "noodle", "pad thai", "lo mein",
      "spaghetti", "pasta", "fettuccine", "carbonara", "yakisoba", "bun bo"],
     ["noodles", "noodle dish"]),

    (["soup", "broth", "bisque", "chowder", "stew", "potage", "tom yum", "miso soup",
      "hot pot", "jjigae", "consomé", "pho", "pozole", "bun bo hue", "laksa"],
     ["soup", "warm dish", "broth-based"]),

    (["rice", "biryani", "risotto", "pilaf", "paella", "fried rice", "congee",
      "nasi", "arroz", "jollof", "bibimbap", "koshari", "com tam"],
     ["rice dish"]),

    (["pizza", "margherita", "pepperoni", "calzone", "flatbread pizza"],
     ["pizza", "Italian baked"]),

    (["burger", "patty", "cheeseburger", "smash burger", "sliders"],
     ["burger", "sandwich"]),

    (["sushi", "maki", "nigiri", "sashimi", "temaki", "california roll", "dragon roll"],
     ["sushi", "Japanese seafood", "raw fish"]),

    (["dumpling", "gyoza", "wonton", "dim sum", "xiaolongbao", "momo", "empanada",
      "pierogi", "har gow", "siu mai", "ravioli"],
     ["dumplings", "filled pastry"]),

    (["taco", "burrito", "quesadilla", "shawarma", "banh mi", "wrap", "gyro",
      "falafel wrap", "tortilla"],
     ["wrap", "street food"]),

    (["curry", "masala", "korma", "tikka", "rendang", "green curry", "red curry",
      "massaman", "vindaloo", "dal", "sabzi", "saag"],
     ["curry", "sauce-based"]),

    (["grilled", "bbq", "barbecue", "charcoal", "charred", "kebab", "satay",
      "yakitori", "skewer", "tandoor", "churrasco"],
     ["grilled", "BBQ"]),

    (["fried", "crispy", "deep-fried", "tempura", "katsu", "karaage", "schnitzel",
      "battered", "fritter", "croquette", "pakora", "samosa"],
     ["fried", "crispy"]),

    (["salad", "slaw", "ceviche", "poke", "tartare", "crudo"],
     ["fresh", "light", "raw"]),

    (["dessert", "sweet", "chocolate", "cake", "cookie", "tiramisu", "cheesecake",
      "mousse", "gelato", "ice cream", "macaron", "baklava", "mochi", "halwa",
      "gulab jamun", "pudding", "brownie", "churros", "crème brûlée", "tart",
      "brigadeiro", "panna cotta"],
     ["dessert", "sweet"]),

    (["coffee", "espresso", "latte", "cold brew", "americano", "cappuccino"],
     ["beverage", "coffee"]),

    (["tea", "matcha", "chai", "bubble tea", "boba", "milk tea"],
     ["beverage", "tea"]),

    (["smoothie", "juice", "lassi", "shake", "drink"],
     ["beverage"]),

    (["breakfast", "morning", "brunch"],
     ["breakfast", "morning meal"]),

    (["snack", "street food", "bite", "chaat", "takoyaki", "samosa", "elote", "suya"],
     ["snack", "street food"]),

    (["vegan", "plant-based", "no meat", "no dairy"],
     ["vegan", "plant-based"]),

    (["vegetarian", "veg ", "paneer", "tofu", "falafel"],
     ["vegetarian"]),

    (["healthy", "light", "lean", "low-cal", "fresh"],
     ["healthy", "light"]),

    (["comfort food", "hearty", "filling", "cozy", "mac and cheese", "mashed"],
     ["comfort food", "hearty"]),
]

_FLAVOR_TRIGGERS: Dict[str, List[str]] = {
    "spicy":    ["spicy", "chili", "jalapeño", "sriracha", "gochujang", "vindaloo",
                 "arrabiata", "bird's eye", "Sichuan", "chilli", "harissa", "sambal",
                 "scotch bonnet", "cayenne", "peri-peri", "berbere"],
    "creamy":   ["cream", "butter", "coconut milk", "béchamel", "mascarpone",
                 "cream cheese", "silky", "velvety", "rich", "luscious", "velvet"],
    "sweet":    ["sugar", "honey", "palm sugar", "caramel", "sweet", "mango",
                 "condensed milk", "syrup", "dessert", "fruity"],
    "savory":   ["savory", "soy sauce", "fish sauce", "oyster sauce", "umami",
                 "broth", "stock", "miso", "Worcestershire"],
    "umami":    ["umami", "miso", "soy", "mushroom", "parmesan", "fish sauce",
                 "anchovy", "truffle", "fermented", "dashi"],
    "tangy":    ["lime", "lemon", "tamarind", "vinegar", "pickled", "sour",
                 "acidic", "tangy", "kimchi", "amchur", "citrus"],
    "smoky":    ["smoked", "smoky", "charcoal", "wood-fired", "charred", "BBQ",
                 "hickory", "mesquite"],
    "aromatic": ["lemongrass", "galangal", "star anise", "cinnamon", "cardamom",
                 "saffron", "rose water", "herb", "fragrant", "spiced"],
    "mild":     ["mild", "gentle", "delicate", "subtle", "light broth"],
    "rich":     ["rich", "indulgent", "decadent", "heavy cream", "fatty", "full-bodied"],
    "fresh":    ["fresh", "raw", "herb", "mint", "cilantro", "basil", "parsley", "crisp"],
    "bitter":   ["dark chocolate", "espresso", "coffee", "bitter", "arugula"],
    "nutty":    ["peanut", "sesame", "pistachio", "almond", "walnut", "hazelnut",
                 "tahini", "cashew", "pine nut"],
}

_DIETARY_TRIGGERS: Dict[str, List[str]] = {
    "vegan":         ["vegan", "plant-based", "no dairy", "no meat", "no animal"],
    "vegetarian":    ["vegetarian", "paneer", "tofu", "falafel", "legume", "bean",
                      "lentil", "chickpea", "cheese", "egg", "dairy"],
    "non-vegetarian":["chicken", "beef", "pork", "lamb", "mutton", "shrimp", "prawn",
                      "fish", "seafood", "duck", "turkey", "octopus", "clam",
                      "crab", "lobster", "anchovy", "tuna", "salmon"],
    "gluten-free":   ["rice noodle", "rice flour", "gluten-free", "teff", "corn tortilla",
                      "gluten free"],
    "halal":         ["halal", "beef", "lamb", "chicken", "no pork"],
}

_MEAL_TYPE_TRIGGERS: Dict[str, List[str]] = {
    "breakfast": ["breakfast", "morning", "brunch", "pancake", "waffle", "dosa",
                  "idli", "toast", "egg", "croissant", "shakshuka", "nasi lemak"],
    "lunch":     ["lunch", "bowl", "salad", "sandwich", "wrap", "rice box"],
    "dinner":    ["dinner", "supper", "feast", "roast", "slow-cooked"],
    "dessert":   ["dessert", "sweet", "cake", "pudding", "gelato", "macaron",
                  "tiramisu", "mochi", "baklava", "gulab jamun", "churros", "brownie"],
    "snack":     ["snack", "bite", "appetizer", "starter", "street food", "samosa",
                  "takoyaki", "suya", "elote"],
    "beverage":  ["coffee", "tea", "latte", "matcha", "bubble tea", "lassi",
                  "smoothie", "chai", "juice", "cold brew", "drink", "beverage"],
    "starter":   ["starter", "appetizer", "salad", "soup", "bruschetta"],
    "brunch":    ["brunch", "waffle", "eggs benedict", "avocado toast"],
}


def _detect_list_contains(text: str, triggers: List[str]) -> bool:
    t = text.lower()
    return any(tr in t for tr in triggers)


def _auto_enrich(dish: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automatically generate missing metadata fields from raw dish data.
    Fields generated: flavor_profile, semantic_tags, dietary_tags,
                      meal_type, embedding_text.
    """
    # Build a combined text corpus for trigger matching
    corpus = " ".join([
        dish.get("name", ""),
        " ".join(dish.get("aliases", [])),
        dish.get("description", ""),
        " ".join(dish.get("ingredients", [])),
        dish.get("cuisine", ""),
    ]).lower()

    # ── Flavor profile ─────────────────────────────────────────────────
    if not dish.get("flavor_profile"):
        flavors = []
        for flavor, triggers in _FLAVOR_TRIGGERS.items():
            if _detect_list_contains(corpus, triggers):
                flavors.append(flavor)
        dish["flavor_profile"] = flavors if flavors else ["savory"]

    # ── Semantic tags ──────────────────────────────────────────────────
    if not dish.get("semantic_tags"):
        tags = []
        for triggers, tag_list in _SEMANTIC_TRIGGERS:
            if _detect_list_contains(corpus, triggers):
                tags.extend(tag_list)
        # Always add cuisine as a tag
        cuisine = dish.get("cuisine", "")
        if cuisine:
            tags.append(cuisine.lower())
        dish["semantic_tags"] = list(set(tags))

    # ── Dietary tags ──────────────────────────────────────────────────
    if not dish.get("dietary_tags"):
        dtags = []
        for label, triggers in _DIETARY_TRIGGERS.items():
            if _detect_list_contains(corpus, triggers):
                dtags.append(label)
        if not dtags:
            dtags = ["non-vegetarian"] if not dish.get("is_veg", True) else ["vegetarian"]
        dish["dietary_tags"] = dtags

    # ── Meal type ──────────────────────────────────────────────────────
    if not dish.get("meal_type"):
        for meal, triggers in _MEAL_TYPE_TRIGGERS.items():
            if _detect_list_contains(corpus, triggers):
                dish["meal_type"] = meal
                break
        else:
            dish["meal_type"] = "lunch"

    # ── Tags (short UI display tags) ──────────────────────────────────
    if not dish.get("tags"):
        ui_tags = []
        ui_tags.append(dish.get("cuisine", "").lower())
        ui_tags.extend(dish.get("flavor_profile", [])[:2])
        ui_tags.extend(dish.get("semantic_tags", [])[:3])
        if dish.get("is_veg"):
            ui_tags.append("vegetarian")
        dish["tags"] = list(set(t for t in ui_tags if t))

    # ── Spice level ────────────────────────────────────────────────────
    # Ensure spice_level is an integer (0-5)
    sl = dish.get("spice_level")
    if isinstance(sl, str):
        sl_str = sl.lower()
        if "none" in sl_str: dish["spice_level"] = 0
        elif "mild" in sl_str: dish["spice_level"] = 1
        elif "medium" in sl_str: dish["spice_level"] = 3
        elif "hot" in sl_str or "fiery" in sl_str: dish["spice_level"] = 5
        else: dish["spice_level"] = 2

    if not isinstance(dish.get("spice_level"), int):
        spicy_corpus = corpus
        if any(w in spicy_corpus for w in ["vindaloo", "very spicy", "scotch bonnet", "fiery", "numbing"]):
            dish["spice_level"] = 5
        elif any(w in spicy_corpus for w in ["spicy", "chili", "sriracha", "gochujang", "jalapeño", "harissa", "berbere"]):
            dish["spice_level"] = 3
        elif any(w in spicy_corpus for w in ["mild spice", "mildly"]):
            dish["spice_level"] = 1
        else:
            dish["spice_level"] = 0

    # ── Popularity score ──────────────────────────────────────────────
    if not dish.get("popularity_score"):
        r = dish.get("rating", 4.0)
        rc = dish.get("review_count", 100)
        dish["popularity_score"] = round((r / 5.0) * 70 + (min(rc, 500) / 500.0) * 30, 1)

    # ── Cinematic Prompt Generation ───────────────────────────────────
    if not dish.get("cinematic_prompt") or True: # Force regenerate prompts during this re-index
        dish_name = dish.get("name", "dish")
        cuisine = dish.get("cuisine", "global")
        flavors = ", ".join(dish.get("flavor_profile", []))
        
        prompt = (f"Cinematic luxury Pinterest-style food photography of {dish_name}, "
                  f"{cuisine} cuisine, flavors of {flavors}, glossy textures, soft steam, "
                  f"warm ambient restaurant lighting, shallow depth of field, premium editorial food styling, "
                  f"realistic ingredients, ultra detailed, appetizing composition, modern food magazine aesthetic.")
        dish["cinematic_prompt"] = prompt

    # ── Image URL points to local caching proxy ───────────────────────
    dish_id = dish.get("id", "")
    if dish_id:
        dish["image_url"] = f"/api/images/{dish_id}"

    # ── Embedding text (the key for semantic retrieval) ───────────────
    if not dish.get("embedding_text"):
        parts = [
            dish["name"],
            " ".join(dish.get("aliases", [])),
            dish.get("cuisine", ""),
            dish.get("country", ""),
            dish.get("description", ""),
            " ".join(dish.get("ingredients", [])),
            " ".join(dish.get("flavor_profile", [])),
            " ".join(dish.get("semantic_tags", [])),
            " ".join(dish.get("dietary_tags", [])),
            " ".join(dish.get("tags", [])),
        ]
        dish["embedding_text"] = " ".join(p for p in parts if p)

    return dish


def _dish_fingerprint(dish: Dict[str, Any]) -> str:
    """
    Compute a stable hash of the dish's content.
    Used to detect if a dish has changed since last indexing.
    """
    key_fields = {
        "id": dish.get("id", ""),
        "name": dish.get("name", ""),
        "description": dish.get("description", ""),
        "embedding_text": dish.get("embedding_text", ""),
    }
    content = json.dumps(key_fields, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class FoodIngestionPipeline:
    """
    Scalable pipeline for ingesting, enriching, embedding,
    and indexing global food knowledge into FAISS.
    """

    def __init__(self):
        self._indexed_registry: Dict[str, str] = {}  # id → fingerprint
        self._load_registry()

    def _load_registry(self):
        """Load the registry of already-indexed dish IDs and their fingerprints."""
        if os.path.exists(INDEX_REGISTRY_PATH):
            try:
                with open(INDEX_REGISTRY_PATH, "r") as f:
                    self._indexed_registry = json.load(f)
                app_logger.info(f"Loaded index registry: {len(self._indexed_registry)} tracked dishes.")
            except Exception as e:
                app_logger.warning(f"Could not load index registry: {e}")
                self._indexed_registry = {}
        else:
            self._indexed_registry = {}

    def _save_registry(self):
        """Persist the registry of indexed dish IDs."""
        os.makedirs(os.path.dirname(INDEX_REGISTRY_PATH), exist_ok=True)
        try:
            with open(INDEX_REGISTRY_PATH, "w") as f:
                json.dump(self._indexed_registry, f, indent=2)
        except Exception as e:
            app_logger.error(f"Failed to save index registry: {e}")

    def load_catalog(self, catalog_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load dishes from one or all JSON catalog files in CATALOG_DIR.
        Each file must be a JSON object with a "dishes" array.
        """
        if catalog_path:
            paths = [catalog_path]
        else:
            paths = [
                os.path.join(CATALOG_DIR, f)
                for f in os.listdir(CATALOG_DIR)
                if f.endswith(".json")
            ]

        all_dishes = []
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                dishes = data.get("dishes", []) if isinstance(data, dict) else data
                all_dishes.extend(dishes)
                app_logger.info(f"Loaded {len(dishes)} dishes from {os.path.basename(path)}")
            except Exception as e:
                app_logger.error(f"Failed to load catalog {path}: {e}")

        app_logger.info(f"Total dishes loaded from catalog: {len(all_dishes)}")
        return all_dishes

    def enrich(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Auto-enrich all dishes with missing metadata fields."""
        enriched = []
        for dish in dishes:
            try:
                enriched.append(_auto_enrich(dict(dish)))
            except Exception as e:
                app_logger.error(f"Failed enriching dish '{dish.get('name', '?')}': {e}")
        return enriched

    def get_new_dishes(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter dishes to only those that are new or changed since last indexing.
        Delta indexing — avoids re-embedding the entire catalog on every startup.
        """
        new_dishes = []
        for dish in dishes:
            dish_id = dish.get("id", "")
            if not dish_id:
                new_dishes.append(dish)
                continue

            fp = _dish_fingerprint(dish)
            if dish_id not in self._indexed_registry or self._indexed_registry[dish_id] != fp:
                new_dishes.append(dish)

        app_logger.info(
            f"Delta check: {len(new_dishes)} new/changed dishes out of {len(dishes)} total."
        )
        return new_dishes

    def embed_and_index(self, dishes: List[Dict[str, Any]], batch_size: int = 50) -> int:
        """
        Generate embeddings for all dishes and add them to FAISS in batches.
        Updates the registry after successful indexing.
        Returns count of successfully indexed dishes.
        """
        if not dishes:
            app_logger.info("No new dishes to embed and index.")
            return 0

        indexed_count = 0
        total_batches = (len(dishes) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            batch = dishes[batch_num * batch_size:(batch_num + 1) * batch_size]
            embeddings = []
            metadata_list = []

            for dish in batch:
                embedding_text = dish.get("embedding_text", dish.get("name", "food"))
                try:
                    emb = embedding_service.get_text_embedding(embedding_text)
                    embeddings.append(emb)
                    metadata_list.append(dish)
                except Exception as e:
                    app_logger.error(f"Embedding failed for '{dish.get('name')}': {e}")
                    continue

            if embeddings:
                try:
                    faiss_store.add_items_batch(embeddings, metadata_list)
                    # Update registry for successfully indexed items
                    for dish in metadata_list:
                        dish_id = dish.get("id", "")
                        if dish_id:
                            self._indexed_registry[dish_id] = _dish_fingerprint(dish)
                    indexed_count += len(metadata_list)
                    app_logger.info(
                        f"Batch {batch_num + 1}/{total_batches}: indexed {len(metadata_list)} dishes. "
                        f"FAISS total: {faiss_store.index.ntotal}"
                    )
                except Exception as e:
                    app_logger.error(f"Batch insert failed: {e}")

        self._save_registry()
        return indexed_count

    def run(self, force_reindex: bool = False, catalog_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Full pipeline run:
          1. Load catalog
          2. Enrich dishes
          3. Filter to new/changed only (unless force_reindex=True)
          4. Embed + index
          5. Return stats

        Args:
            force_reindex: If True, clears FAISS and re-embeds everything.
            catalog_path:  Optional path to a specific catalog JSON to ingest.

        Returns dict with stats: total_in_catalog, newly_indexed, faiss_total
        """
        t0 = time.time()
        app_logger.info(f"Food ingestion pipeline starting (force_reindex={force_reindex})...")

        # Step 1: Load
        dishes = self.load_catalog(catalog_path)

        # Step 2: Enrich
        dishes = self.enrich(dishes)

        # Step 3: Force re-index resets everything
        if force_reindex:
            app_logger.info("Force re-index: clearing FAISS index and registry...")
            faiss_store.clear()
            self._indexed_registry = {}

        # Step 4: Delta filter
        new_dishes = self.get_new_dishes(dishes)

        # Step 5: Embed + index
        newly_indexed = self.embed_and_index(new_dishes)

        elapsed = round(time.time() - t0, 2)
        stats = {
            "total_in_catalog": len(dishes),
            "newly_indexed": newly_indexed,
            "faiss_total": faiss_store.index.ntotal if faiss_store.index else 0,
            "elapsed_seconds": elapsed,
        }
        app_logger.info(f"Pipeline complete in {elapsed}s: {stats}")
        return stats

    def ingest_raw(self, raw_dishes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest a list of raw dish dicts directly (e.g. from a POST request).
        Auto-enriches them, then embeds and indexes only new/changed ones.
        """
        enriched = self.enrich(raw_dishes)
        new_dishes = self.get_new_dishes(enriched)
        newly_indexed = self.embed_and_index(new_dishes)
        return {
            "submitted": len(raw_dishes),
            "newly_indexed": newly_indexed,
            "faiss_total": faiss_store.index.ntotal if faiss_store.index else 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return current index statistics."""
        return {
            "faiss_total": faiss_store.index.ntotal if faiss_store.index else 0,
            "tracked_in_registry": len(self._indexed_registry),
            "catalog_dir": CATALOG_DIR,
            "embedding_mode": "bedrock" if not embedding_service.use_fallback else "food-semantic-local",
        }


# Singleton
food_pipeline = FoodIngestionPipeline()
