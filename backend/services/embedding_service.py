"""
EmbeddingService — Semantic Food-Concept Embeddings
====================================================
Real mode  : calls AWS Bedrock Titan Multimodal for true dense embeddings.
Fallback   : uses a deterministic FOOD-SEMANTIC vector encoding that maps
             dish names, flavors, cuisines, and ingredients into a shared
             1024-dimensional concept space.

This replaces the previous hash-based random mock so that FAISS similarity
produces REAL semantic proximity even without AWS credentials.

How the semantic fallback works
--------------------------------
1. Build a vocabulary of ~200 food concept "axes" (dimensions).
2. Each dimension corresponds to a meaningful food concept:
   dim 0  → "noodle / pasta / noodle bowl"
   dim 1  → "soup / broth / liquid"
   dim 2  → "spicy / hot / chili / fiery"
   ...
3. For any input text, activate each dimension with a score ∈ [0, 1]
   based on how many trigger words for that concept appear in the text.
4. Add small Gaussian noise seeded by the text hash (±0.05) to break ties
   and give each item a unique fingerprint.
5. Pad to 1024 dims with near-zero noise for FAISS dimension compatibility.
6. L2-normalize → unit-length vector ready for FAISS IndexFlatIP cosine search.

Result: "ramen" and "pho" land very close together in vector space.
        "burger" and "tiramisu" land far from both.
"""
from __future__ import annotations

import base64
import json
import math
import hashlib
import numpy as np
from typing import Optional, List

import boto3
from botocore.exceptions import ClientError

from backend.config import get_settings
from backend.utils.logger import app_logger

settings = get_settings()


# ── FOOD CONCEPT AXES ────────────────────────────────────────────────────────
# Each axis is a list of trigger words. Presence of these words in the text
# activates that dimension. Axes are designed to cluster semantically similar
# foods in the same region of vector space.
#
# Format: (axis_name, [trigger_words], weight_per_hit)
FOOD_CONCEPT_AXES = [
    # ── NOODLE / PASTA ───────────────────────────────────────────────────────
    ("noodle",       ["noodle", "noodles", "ramen", "udon", "soba", "pad thai", "pho",
                      "pasta", "spaghetti", "fettuccine", "linguine", "lo mein",
                      "laksa", "mee", "vermicelli", "glass noodle", "rice noodle",
                      "cellophane", "chow mein", "yakisoba", "carbonara"], 1.0),

    # ── SOUP / BROTH ─────────────────────────────────────────────────────────
    ("soup",         ["soup", "broth", "bisque", "chowder", "bouillon", "stock",
                      "consomme", "stew", "potage", "hot pot", "fondue",
                      "laksa", "ramen", "pho", "miso soup", "tom yum"], 1.0),

    # ── RICE ─────────────────────────────────────────────────────────────────
    ("rice",         ["rice", "biryani", "risotto", "pilaf", "paella",
                      "fried rice", "congee", "porridge", "sushi rice",
                      "basmati", "jasmine", "arroz"], 1.0),

    # ── BREAD / DOUGH ────────────────────────────────────────────────────────
    ("bread",        ["bread", "bun", "roll", "naan", "pita", "roti", "tortilla",
                      "baguette", "focaccia", "brioche", "ciabatta", "pretzel",
                      "flatbread", "paratha", "dosa", "chapati", "wrap"], 1.0),

    # ── PIZZA ────────────────────────────────────────────────────────────────
    ("pizza",        ["pizza", "margherita", "pepperoni", "neapolitan",
                      "mozzarella", "tomato sauce", "crust", "pie",
                      "calzone", "wood-fired", "pan pizza"], 1.0),

    # ── BURGER / SANDWICH ────────────────────────────────────────────────────
    ("burger",       ["burger", "hamburger", "patty", "brioche bun",
                      "cheeseburger", "smash burger", "veggie burger",
                      "sliders", "beef patty", "sandwich"], 0.9),

    # ── TACO / WRAP ──────────────────────────────────────────────────────────
    ("taco",         ["taco", "burrito", "enchilada", "quesadilla", "fajita",
                      "shawarma", "gyro", "wrap", "banh mi", "falafel wrap",
                      "birria", "carnitas", "tortilla wrap"], 1.0),

    # ── DUMPLING / SMALL BITES ───────────────────────────────────────────────
    ("dumpling",     ["dumpling", "gyoza", "dim sum", "wonton", "har gow",
                      "siu mai", "momo", "pierogi", "empanada", "potsticker",
                      "xiaolongbao", "soup dumpling", "ravioli", "tortellini"], 1.0),

    # ── SUSHI / JAPANESE ─────────────────────────────────────────────────────
    ("sushi",        ["sushi", "sashimi", "maki", "nigiri", "temaki",
                      "california roll", "spicy tuna roll", "dragon roll",
                      "uramaki", "chirashi", "omakase"], 1.0),

    # ── CURRY ────────────────────────────────────────────────────────────────
    ("curry",        ["curry", "masala", "korma", "tikka masala", "butter chicken",
                      "green curry", "red curry", "panang", "rendang",
                      "vindaloo", "dal", "sambar", "sabzi", "saag"], 1.0),

    # ── BBQ / GRILLED ────────────────────────────────────────────────────────
    ("grilled",      ["grilled", "barbecue", "bbq", "charred", "smoky",
                      "kebab", "skewer", "satay", "tandoori", "churrasco",
                      "flame-grilled", "grill", "braai", "asado", "carne"], 1.0),

    # ── FRIED / CRISPY ───────────────────────────────────────────────────────
    ("fried",        ["fried", "crispy", "deep-fried", "crunchy", "tempura",
                      "karaage", "katsu", "schnitzel", "fritter", "battered",
                      "golden", "croquette", "pakora", "samosa", "falafel",
                      "buffalo wing", "spring roll", "popcorn chicken"], 1.0),

    # ── STEAMED / LIGHT ──────────────────────────────────────────────────────
    ("steamed",      ["steamed", "poached", "blanched", "gentle", "light",
                      "clean", "baozi", "bao bun"], 0.8),

    # ── SEAFOOD ──────────────────────────────────────────────────────────────
    ("seafood",      ["seafood", "fish", "prawn", "shrimp", "crab", "lobster",
                      "salmon", "tuna", "squid", "octopus", "clam", "mussel",
                      "scallop", "oyster", "sea bass", "cod", "halibut",
                      "anchovy", "sardine", "calamari"], 1.0),

    # ── CHICKEN ──────────────────────────────────────────────────────────────
    ("chicken",      ["chicken", "poultry", "hen", "breast", "thigh",
                      "wings", "drumstick", "tikka", "katsu", "karaage",
                      "rotisserie", "shawarma chicken", "fried chicken"], 1.0),

    # ── BEEF / LAMB / PORK ───────────────────────────────────────────────────
    ("red_meat",     ["beef", "lamb", "pork", "mutton", "veal", "steak",
                      "ribeye", "sirloin", "burger patty", "brisket", "ribs",
                      "pulled pork", "carnitas", "bulgogi", "chashu",
                      "char siu", "osso buco", "rendang", "kebab"], 1.0),

    # ── VEGETARIAN / VEGAN ───────────────────────────────────────────────────
    ("vegetarian",   ["vegetarian", "vegan", "plant-based", "meatless",
                      "veg", "veggie", "tofu", "tempeh", "seitan", "jackfruit",
                      "lentil", "legume", "bean", "chickpea", "falafel",
                      "paneer", "halloumi", "mushroom", "cauliflower"], 1.0),

    # ── DAIRY / CHEESE ───────────────────────────────────────────────────────
    ("dairy",        ["cheese", "cream", "butter", "milk", "parmesan",
                      "mozzarella", "ricotta", "brie", "cheddar", "mascarpone",
                      "yogurt", "curd", "paneer", "burrata", "feta",
                      "gouda", "gruyere", "camembert", "cream cheese"], 1.0),

    # ── SPICY / HOT ──────────────────────────────────────────────────────────
    ("spicy",        ["spicy", "hot", "fiery", "chili", "jalapeño", "habanero",
                      "sriracha", "gochujang", "sichuan", "numbing",
                      "vindaloo", "arrabiata", "peri-peri", "buffalo",
                      "harissa", "sambal", "chilli flakes", "cayenne",
                      "wasabi", "horseradish", "pepper", "heat"], 1.0),

    # ── SWEET / DESSERT ──────────────────────────────────────────────────────
    ("sweet",        ["sweet", "sugar", "dessert", "honey", "caramel",
                      "chocolate", "vanilla", "pastry", "cake", "cookie",
                      "brownie", "tart", "pudding", "mousse", "cheesecake",
                      "tiramisu", "gelato", "ice cream", "sorbet", "macaroon",
                      "macaron", "baklava", "halwa", "gulab jamun",
                      "crème brûlée", "mochi", "donut", "churro"], 1.0),

    # ── COFFEE / BEVERAGE ────────────────────────────────────────────────────
    ("coffee",       ["coffee", "espresso", "latte", "cappuccino", "americano",
                      "cold brew", "mocha", "affogato", "caffeine"], 0.9),

    # ── TEA / MATCHA ─────────────────────────────────────────────────────────
    ("tea",          ["tea", "matcha", "green tea", "chai", "milk tea",
                      "bubble tea", "boba", "oolong", "earl grey",
                      "jasmine", "chamomile"], 0.9),

    # ── BEVERAGE (GENERAL) ───────────────────────────────────────────────────
    ("beverage",     ["drink", "beverage", "juice", "smoothie", "shake",
                      "lassi", "lemonade", "cocktail", "mocktail",
                      "spritzer", "water", "soda"], 0.9),

    # ── CREAMY / RICH ────────────────────────────────────────────────────────
    ("creamy",       ["creamy", "rich", "velvety", "smooth", "silky",
                      "butter", "cream", "luxurious", "indulgent",
                      "full-bodied", "decadent", "luscious"], 1.0),

    # ── LIGHT / FRESH ────────────────────────────────────────────────────────
    ("light",        ["light", "fresh", "clean", "crisp", "raw",
                      "salad", "ceviche", "tartare", "crudo", "poke",
                      "garden", "healthy", "low-calorie", "lean"], 1.0),

    # ── UMAMI / SAVORY ───────────────────────────────────────────────────────
    ("umami",        ["umami", "savory", "soy sauce", "miso", "mushroom",
                      "worcestershire", "fish sauce", "anchovy", "parmesan",
                      "truffle", "fermented", "aged", "depth of flavor"], 1.0),

    # ── TANGY / ACIDIC ───────────────────────────────────────────────────────
    ("tangy",        ["tangy", "sour", "acidic", "citrus", "lemon", "lime",
                      "vinegar", "tamarind", "pickled", "fermented",
                      "kimchi", "kombucha", "sourdough"], 1.0),

    # ── AROMATIC / SPICED ────────────────────────────────────────────────────
    ("aromatic",     ["aromatic", "fragrant", "herb", "spiced", "saffron",
                      "cinnamon", "cardamom", "star anise", "cumin", "coriander",
                      "turmeric", "garam masala", "bay leaf", "clove",
                      "nutmeg", "basil", "thyme", "rosemary", "lemongrass",
                      "galangal", "kaffir lime", "za'atar"], 1.0),

    # ── COMFORT / HEARTY ─────────────────────────────────────────────────────
    ("comfort",      ["comfort food", "hearty", "filling", "cozy", "nostalgic",
                      "warming", "soul food", "home cooking", "stew",
                      "mac and cheese", "mashed potato", "pot pie"], 1.0),

    # ── STREET FOOD ──────────────────────────────────────────────────────────
    ("street_food",  ["street food", "street", "snack", "quick bite",
                      "food cart", "hawker", "market", "portable",
                      "hand-held", "on the go", "casual"], 1.0),

    # ── LUXURY / FINE DINING ─────────────────────────────────────────────────
    ("luxury",       ["luxury", "fine dining", "gourmet", "premium", "truffle",
                      "foie gras", "wagyu", "lobster", "caviar", "gold leaf",
                      "tasting menu", "michelin", "haute cuisine"], 1.0),

    # ── WARM / HOT TEMPERATURE ───────────────────────────────────────────────
    ("warm",         ["warm", "hot", "steaming", "piping hot", "fresh from oven",
                      "oven-baked", "sizzling", "bubbling"], 0.8),

    # ── COLD / CHILLED ───────────────────────────────────────────────────────
    ("cold",         ["cold", "chilled", "iced", "frozen", "sorbet",
                      "gelato", "ice cream", "refrigerated", "refreshing",
                      "cool", "ice cold"], 0.8),

    # ── CUISINE IDENTITY AXES ────────────────────────────────────────────────
    ("japanese",     ["japanese", "japan", "ramen", "sushi", "miso", "udon",
                      "tempura", "yakitori", "katsu", "matcha", "wagyu",
                      "tonkotsu", "teriyaki", "edamame", "onigiri"], 1.0),

    ("korean",       ["korean", "korea", "kimchi", "bulgogi", "bibimbap",
                      "gochujang", "tteok", "japchae", "doenjang",
                      "galbi", "sundubu", "banchan", "samgyeopsal"], 1.0),

    ("chinese",      ["chinese", "china", "dim sum", "mapo", "kung pao",
                      "peking duck", "char siu", "wonton", "sichuan",
                      "cantonese", "shanghai", "bao", "xiaolongbao",
                      "lo mein", "fried rice", "sweet and sour"], 1.0),

    ("thai",         ["thai", "thailand", "pad thai", "green curry", "red curry",
                      "massaman", "tom yum", "tom kha", "satay", "larb",
                      "mango sticky rice", "lemongrass", "galangal"], 1.0),

    ("vietnamese",   ["vietnamese", "vietnam", "pho", "banh mi", "goi cuon",
                      "bun bo hue", "com tam", "cao lau", "bun cha",
                      "fresh spring rolls", "fish sauce"], 1.0),

    ("indian",       ["indian", "india", "curry", "biryani", "tikka", "masala",
                      "naan", "dosa", "samosa", "dal", "paneer", "korma",
                      "vindaloo", "tandoor", "chaat", "lassi", "idli",
                      "paratha", "halwa", "chhole", "rajma"], 1.0),

    ("italian",      ["italian", "italy", "pasta", "pizza", "risotto",
                      "tiramisu", "gelato", "carbonara", "bolognese",
                      "ossobuco", "bruschetta", "pesto", "arancini",
                      "cannoli", "lasagna", "ravioli"], 1.0),

    ("french",       ["french", "france", "croissant", "baguette", "crème brûlée",
                      "coq au vin", "ratatouille", "bouillabaisse", "soufflé",
                      "macaron", "beurre blanc", "confit", "mousse",
                      "pot-au-feu", "brie", "fondue", "quiche"], 1.0),

    ("mexican",      ["mexican", "mexico", "taco", "burrito", "quesadilla",
                      "enchilada", "guacamole", "salsa", "mole", "tamale",
                      "pozole", "birria", "chiles rellenos", "horchata",
                      "carnitas", "ceviche mexicano", "churro"], 1.0),

    ("american",     ["american", "america", "burger", "hot dog", "bbq",
                      "mac and cheese", "buffalo wings", "southern fried",
                      "clam chowder", "lobster roll", "philly cheesesteak",
                      "pancakes", "waffles", "apple pie", "brownie"], 1.0),

    ("mediterranean",["mediterranean", "greek", "turkish", "falafel",
                      "hummus", "shawarma", "tzatziki", "pita", "tabouleh",
                      "baklava", "moussaka", "dolma", "baba ghanoush",
                      "halloumi", "souvlaki", "spanakopita"], 1.0),

    ("middle_eastern",["middle eastern", "lebanese", "persian", "arabic",
                       "kebab", "kofta", "mansaf", "shakshuka", "za'atar",
                       "harissa", "tahini", "ful medames", "kibbeh"], 1.0),

    ("malaysian_southeast_asian", ["malaysian", "singapore", "indonesian",
                                   "laksa", "nasi lemak", "satay", "rendang",
                                   "mee goreng", "char kway teow",
                                   "bak kut teh", "hainanese chicken rice"], 1.0),

    ("latin_american", ["latin", "peruvian", "colombian", "argentine",
                        "ceviche", "lomo saltado", "arepas", "empanadas",
                        "churrasco", "feijoada", "coxinha", "dulce de leche",
                        "chimichurri", "plantain"], 1.0),

    ("african",       ["ethiopian", "nigerian", "moroccan", "african",
                       "injera", "wat", "jollof rice", "egusi",
                       "tagine", "couscous", "harissa", "berbere",
                       "suya", "fufu", "akara"], 1.0),
]


def _build_concept_index() -> dict:
    """
    Pre-compute a lookup: word → list of (axis_index, weight) for fast activation.
    """
    index: dict = {}
    for ax_idx, (ax_name, triggers, weight) in enumerate(FOOD_CONCEPT_AXES):
        for word in triggers:
            word_lower = word.lower()
            for token in word_lower.split():
                if token not in index:
                    index[token] = []
                index[token].append((ax_idx, weight))
    return index


_CONCEPT_INDEX = _build_concept_index()
_N_AXES = len(FOOD_CONCEPT_AXES)   # ~45 meaningful axes


def _food_semantic_vector(text: str, dim: int = 1024) -> np.ndarray:
    """
    Convert food-related text into a deterministic semantic unit vector.

    Steps:
      1. Tokenise input text.
      2. For each token, look up concept axis activations.
      3. Accumulate scores per axis.
      4. Place axis scores into the first _N_AXES dimensions.
      5. Fill remaining dims with tiny deterministic Gaussian noise (seeded by text hash).
      6. L2-normalise to unit length.
    """
    tokens = text.lower().split()

    # Axis activation vector
    axis_scores = np.zeros(_N_AXES, dtype=np.float32)
    for token in tokens:
        clean = token.strip(".,!?\"'()[]{}:;")
        if clean in _CONCEPT_INDEX:
            for ax_idx, weight in _CONCEPT_INDEX[clean]:
                axis_scores[ax_idx] += weight

    # Normalise axis scores to [0, 1] range per axis
    max_val = axis_scores.max()
    if max_val > 0:
        axis_scores = axis_scores / max_val

    # Deterministic background noise seeded by SHA-256 of the text
    text_hash = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(text_hash)

    # Build full vector: meaningful axes + noise padding
    full_vec = np.zeros(dim, dtype=np.float32)
    full_vec[:_N_AXES] = axis_scores * 4.0   # scale up so these dominate
    full_vec[_N_AXES:] = rng.standard_normal(dim - _N_AXES) * 0.05  # tiny noise

    # L2 normalise
    norm = np.linalg.norm(full_vec)
    if norm > 0:
        full_vec = full_vec / norm
    return full_vec


class EmbeddingService:
    def __init__(self):
        self.model_id = settings.bedrock_embedding_model_id
        self.use_fallback = False
        self.embedding_dim = 1024

        is_placeholder = (
            settings.aws_access_key_id == "your_access_key_here"
            or not settings.aws_access_key_id
            or not settings.aws_secret_access_key
        )

        if is_placeholder:
            app_logger.warning(
                "AWS Bedrock credentials not configured for embeddings. "
                "Using food-semantic deterministic embeddings."
            )
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
                app_logger.info("AWS Bedrock Runtime client initialized for embeddings.")
            except Exception as e:
                app_logger.error(f"Failed to initialize Bedrock client: {e}. Using semantic mock.")
                self.use_fallback = True
                self.bedrock_client = None

    def _generate_semantic_embedding(self, text: str) -> List[float]:
        """Generate a food-semantic deterministic embedding (no AWS required)."""
        return _food_semantic_vector(text, self.embedding_dim).tolist()

    # kept for API compatibility — now delegates to semantic version
    def _generate_mock_embedding(self, seed_text: Optional[str] = None) -> List[float]:
        return self._generate_semantic_embedding(seed_text or "food dish meal")

    def get_text_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text."""
        if self.use_fallback:
            return self._generate_semantic_embedding(text)

        body = json.dumps({
            "inputText": text,
            "embeddingConfig": {"outputEmbeddingLength": self.embedding_dim}
        })
        try:
            response = self.bedrock_client.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("embedding")
        except ClientError as e:
            app_logger.error(f"Bedrock Titan client error: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")
        except Exception as e:
            app_logger.error(f"Unexpected error in embedding: {e}")
            return self._generate_semantic_embedding(text)

    def get_image_embedding(self, image_bytes: bytes) -> List[float]:
        """Generate vector embedding for image using Amazon Titan Multimodal."""
        if self.use_fallback:
            return self._generate_semantic_embedding("food dish image visual")

        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        body = json.dumps({
            "inputImage": base64_image,
            "embeddingConfig": {"outputEmbeddingLength": self.embedding_dim}
        })
        try:
            response = self.bedrock_client.invoke_model(
                body=body, modelId=self.model_id,
                accept="application/json", contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("embedding")
        except ClientError as e:
            app_logger.error(f"Bedrock Titan image error: {e}")
            raise RuntimeError(f"Image embedding failed: {e}")
        except Exception as e:
            app_logger.error(f"Unexpected error in image embedding: {e}")
            return self._generate_semantic_embedding("food dish image visual")

    def get_multimodal_embedding(
        self,
        text: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> List[float]:
        """Generate combined multimodal embedding using text and/or image."""
        if not text and not image_bytes:
            raise ValueError("Must provide either text or image_bytes")

        if self.use_fallback:
            return self._generate_semantic_embedding(text or "food dish image visual")

        request_body = {}
        if text:
            request_body["inputText"] = text
        if image_bytes:
            request_body["inputImage"] = base64.b64encode(image_bytes).decode("utf-8")
        request_body["embeddingConfig"] = {"outputEmbeddingLength": self.embedding_dim}

        body = json.dumps(request_body)
        try:
            response = self.bedrock_client.invoke_model(
                body=body, modelId=self.model_id,
                accept="application/json", contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("embedding")
        except ClientError as e:
            app_logger.error(f"Bedrock multimodal error: {e}")
            raise RuntimeError(f"Multimodal embedding failed: {e}")
        except Exception as e:
            app_logger.error(f"Unexpected error in multimodal embedding: {e}")
            return self._generate_semantic_embedding(text or "food dish image visual")


# Singleton instance
embedding_service = EmbeddingService()
