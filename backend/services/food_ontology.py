"""
FoodOntology — Semantic Food Knowledge Graph
============================================
Maps food concepts, expands queries into richer semantic space,
groups cuisines into semantic families, and computes concept overlap
between a query and a dish's concept profile.

Used by the SemanticReranker to produce accurate, intent-aware rankings
without relying on real ML embeddings.
"""
from __future__ import annotations
from typing import List, Set, Dict


# ── CUISINE FAMILY CLUSTERS ─────────────────────────────────────────────────
# Cuisines within the same cluster share similar ingredients, textures,
# and flavor philosophies. A query for one cuisine should boost the others.
CUISINE_FAMILIES: Dict[str, List[str]] = {
    "asian_noodle_soup": ["Japanese", "Korean", "Vietnamese", "Chinese", "Thai", "Malaysian", "Taiwanese"],
    "south_asian_curry": ["Indian", "Pakistani", "Sri Lankan", "Bangladeshi", "Nepali"],
    "latin_street":      ["Mexican", "Colombian", "Peruvian", "Brazilian", "Argentine", "Venezuelan"],
    "mediterranean":     ["Italian", "Greek", "Turkish", "Lebanese", "Spanish", "Moroccan", "Mediterranean"],
    "middle_eastern":    ["Middle Eastern", "Persian", "Lebanese", "Israeli", "Egyptian", "Turkish"],
    "east_asian_rice":   ["Chinese", "Japanese", "Korean", "Vietnamese", "Filipino", "Cambodian"],
    "european_bakery":   ["French", "German", "Austrian", "Belgian", "Swiss", "British"],
    "american_comfort":  ["American", "Southern", "Cajun", "BBQ"],
    "african_stew":      ["Ethiopian", "Nigerian", "Ghanaian", "Moroccan", "South African"],
    "southeast_asian":   ["Thai", "Malaysian", "Indonesian", "Filipino", "Singaporean", "Vietnamese"],
}


# ── FOOD CONCEPT SYNONYM MAP ────────────────────────────────────────────────
# Maps a query term → set of related food concepts used in embedding text
QUERY_CONCEPT_MAP: Dict[str, List[str]] = {
    # Noodle dishes
    "ramen":       ["ramen", "noodle", "broth", "soup", "Japanese", "pork", "umami", "warm", "bowl"],
    "pho":         ["pho", "noodle", "broth", "soup", "Vietnamese", "beef", "anise", "warm", "bowl"],
    "udon":        ["udon", "noodle", "thick", "Japanese", "soup", "broth", "wheat"],
    "pad thai":    ["noodles", "rice noodle", "Thai", "tamarind", "peanut", "stir-fry", "savory"],
    "laksa":       ["laksa", "noodle", "coconut", "spicy", "Malaysian", "soup", "broth"],
    "lo mein":     ["noodles", "Chinese", "stir-fry", "savory", "wheat"],
    "soba":        ["noodles", "Japanese", "buckwheat", "dipping", "cold"],

    # Rice dishes
    "biryani":     ["biryani", "rice", "aromatic", "spiced", "Indian", "Pakistani", "saffron", "layered"],
    "fried rice":  ["rice", "fried", "wok", "Asian", "egg", "savory", "stir-fry"],
    "risotto":     ["rice", "creamy", "Italian", "arborio", "parmesan", "rich"],
    "paella":      ["rice", "Spanish", "seafood", "saffron", "Valencia", "savory"],

    # Soups and stews
    "soup":        ["soup", "broth", "warm", "comforting", "liquid", "bowl", "hearty"],
    "stew":        ["stew", "thick", "slow-cooked", "comforting", "hearty", "braised"],
    "curry":       ["curry", "sauce", "spiced", "gravy", "comforting", "warm", "rice"],
    "ramen soup":  ["ramen", "noodle", "broth", "Japanese", "warm"],
    "miso soup":   ["miso", "Japanese", "tofu", "light", "warm", "umami"],

    # Pizza and pasta
    "pizza":       ["pizza", "Italian", "crust", "tomato", "cheese", "baked", "mozzarella"],
    "pasta":       ["pasta", "Italian", "sauce", "wheat", "noodle", "savory"],
    "spaghetti":   ["spaghetti", "pasta", "Italian", "sauce", "wheat"],
    "lasagna":     ["lasagna", "pasta", "Italian", "layered", "cheese", "baked"],
    "carbonara":   ["pasta", "Italian", "creamy", "egg", "pork", "cheese", "Roman"],

    # Sandwiches and wraps
    "burger":      ["burger", "beef", "bun", "American", "patty", "cheese", "sauce", "fries"],
    "sandwich":    ["sandwich", "bread", "filling", "savory", "portable"],
    "taco":        ["taco", "tortilla", "Mexican", "salsa", "meat", "street food"],
    "wrap":        ["wrap", "tortilla", "filling", "portable", "savory"],
    "shawarma":    ["shawarma", "meat", "Middle Eastern", "pita", "garlic", "wrap"],
    "banh mi":     ["banh mi", "Vietnamese", "baguette", "pork", "pickled", "cilantro"],
    "falafel":     ["falafel", "chickpea", "Mediterranean", "fried", "vegetarian", "pita", "tahini"],

    # Grilled / BBQ
    "bbq":         ["barbecue", "grilled", "smoky", "charred", "meat", "sauce", "American"],
    "kebab":       ["kebab", "grilled", "meat", "skewer", "Middle Eastern", "spiced"],
    "steak":       ["steak", "beef", "grilled", "juicy", "American", "cut"],

    # Street food
    "street food":  ["street food", "casual", "crispy", "fried", "portable", "snack"],
    "samosa":       ["samosa", "Indian", "fried", "pastry", "potato", "crispy", "snack"],
    "dumplings":    ["dumplings", "steamed", "Chinese", "filled", "savory"],
    "spring rolls": ["spring rolls", "fried", "Asian", "crispy", "vegetable"],
    "dim sum":      ["dim sum", "Chinese", "steamed", "dumplings", "bite-sized"],
    "tempura":      ["tempura", "Japanese", "fried", "battered", "light", "crispy"],
    "karaage":      ["karaage", "Japanese", "fried chicken", "crispy", "juicy"],

    # Desserts
    "dessert":      ["sweet", "dessert", "sugar", "rich", "indulgent", "bakery"],
    "tiramisu":     ["tiramisu", "Italian", "coffee", "mascarpone", "layered", "creamy", "dessert"],
    "cheesecake":   ["cheesecake", "cream cheese", "sweet", "creamy", "dessert", "bakery"],
    "gelato":       ["gelato", "Italian", "ice cream", "cold", "sweet", "creamy", "frozen"],
    "mousse":       ["mousse", "chocolate", "airy", "sweet", "dessert", "French", "creamy"],
    "macaron":      ["macaron", "French", "almond", "sweet", "bakery", "delicate", "pastel"],
    "lava cake":    ["lava cake", "chocolate", "warm", "molten", "sweet", "dessert"],
    "crème brûlée": ["crème brûlée", "French", "custard", "creamy", "caramelized", "dessert", "vanilla"],
    "baklava":      ["baklava", "Turkish", "pastry", "honey", "pistachio", "sweet", "flaky"],
    "mochi":        ["mochi", "Japanese", "rice", "chewy", "sweet", "dessert"],

    # Flavor profiles
    "spicy":        ["spicy", "chili", "hot", "fiery", "heat", "pepper", "sriracha", "jalapeño"],
    "creamy":       ["creamy", "rich", "smooth", "butter", "cream", "velvety"],
    "sweet":        ["sweet", "sugar", "honey", "caramel", "dessert"],
    "sour":         ["sour", "tangy", "lime", "lemon", "vinegar", "acidic"],
    "umami":        ["umami", "savory", "soy", "miso", "mushroom", "broth", "depth"],
    "smoky":        ["smoky", "grilled", "charred", "BBQ", "wood-fired"],
    "tangy":        ["tangy", "acidic", "pickled", "citrus", "fermented"],
    "bitter":       ["bitter", "coffee", "dark chocolate", "greens", "espresso"],

    # Cooking styles
    "fried":        ["fried", "crispy", "deep-fried", "crunchy", "golden", "oil"],
    "grilled":      ["grilled", "charred", "flame", "smoky", "BBQ", "marks"],
    "steamed":      ["steamed", "light", "healthy", "gentle", "moist"],
    "baked":        ["baked", "oven", "roasted", "golden", "crust"],
    "raw":          ["raw", "fresh", "sushi", "sashimi", "cold", "uncooked"],
    "braised":      ["braised", "slow-cooked", "tender", "fall-off-bone", "rich sauce"],

    # Dietary
    "vegan":        ["vegan", "plant-based", "no dairy", "no meat", "vegetables", "tofu"],
    "vegetarian":   ["vegetarian", "veg", "no meat", "plant", "cheese", "dairy"],
    "healthy":      ["healthy", "light", "fresh", "salad", "low-calorie", "nutritious"],
    "gluten-free":  ["gluten-free", "rice", "corn", "quinoa", "no wheat"],

    # Meal types
    "breakfast":    ["breakfast", "morning", "egg", "toast", "pancake", "coffee"],
    "brunch":       ["brunch", "egg", "avocado", "toast", "morning", "leisurely"],
    "snack":        ["snack", "light", "bite", "small", "appetizer", "quick"],
    "comfort food": ["comfort", "warm", "hearty", "filling", "cozy", "nostalgic", "indulgent"],

    # Beverages
    "coffee":       ["coffee", "espresso", "caffeine", "latte", "beverage", "aromatic"],
    "matcha":       ["matcha", "green tea", "Japanese", "beverage", "earthy", "sweet"],
    "smoothie":     ["smoothie", "blended", "fruit", "healthy", "fresh", "beverage"],
    "lassi":        ["lassi", "Indian", "yogurt", "mango", "sweet", "beverage", "creamy"],
    "bubble tea":   ["bubble tea", "taiwanese", "milk tea", "pearls", "sweet", "beverage"],
}


# ── INGREDIENT CATEGORY MAP ──────────────────────────────────────────────────
INGREDIENT_CONCEPT_MAP: Dict[str, List[str]] = {
    "noodle":      ["ramen", "pho", "udon", "pasta", "spaghetti", "soba", "pad thai", "lo mein"],
    "rice":        ["biryani", "fried rice", "risotto", "paella", "sushi", "congee"],
    "bread":       ["pizza", "sandwich", "burger", "naan", "pita", "baguette", "focaccia"],
    "chicken":     ["chicken tikka", "katsu", "karaage", "wings", "shawarma", "quesadilla"],
    "beef":        ["burger", "steak", "bulgogi", "birria", "pho", "kebab", "stew"],
    "pork":        ["ramen", "tonkotsu", "banh mi", "char siu", "carnitas", "ribs"],
    "seafood":     ["sushi", "sashimi", "prawn", "shrimp", "crab", "lobster", "paella", "tempura"],
    "tofu":        ["mapo tofu", "miso soup", "agedashi", "vegan", "vegetarian", "kimchi stew"],
    "cheese":      ["pizza", "pasta", "burger", "quesadilla", "cheesecake", "risotto", "grilled cheese"],
    "chocolate":   ["mousse", "lava cake", "brownie", "tiramisu", "dark chocolate", "dessert"],
    "mango":       ["lassi", "smoothie", "Thai mango", "dessert", "tropical"],
    "avocado":     ["guacamole", "salad", "toast", "California roll", "vegan"],
    "egg":         ["ramen", "carbonara", "omelette", "fried rice", "bibimbap", "breakfast"],
    "coconut":     ["Thai curry", "laksa", "Malaysian", "tropical", "coconut milk"],
    "spice":       ["curry", "Indian", "biryani", "harissa", "masala", "zaatar"],
}


class FoodOntology:
    """
    A food semantic knowledge graph for query expansion and concept matching.
    """

    def expand_query(self, query: str) -> str:
        """
        Expand a user query into a richer semantic string by appending
        related food concepts from the ontology.

        Example:
            "spicy ramen" → "spicy ramen noodle broth soup Japanese pork umami warm bowl chili hot fiery"
        """
        q_lower = query.lower().strip()
        concepts: Set[str] = set(q_lower.split())

        for term, expansions in QUERY_CONCEPT_MAP.items():
            if term in q_lower:
                concepts.update(expansions)

        for ingredient, related_dishes in INGREDIENT_CONCEPT_MAP.items():
            if ingredient in q_lower:
                concepts.update(related_dishes)

        return " ".join(sorted(concepts))

    def get_query_concepts(self, query: str) -> Set[str]:
        """Return the full set of semantic concepts for a query."""
        q_lower = query.lower().strip()
        concepts: Set[str] = set(q_lower.split())

        for term, expansions in QUERY_CONCEPT_MAP.items():
            if term in q_lower:
                concepts.update(e.lower() for e in expansions)

        for ingredient, related_dishes in INGREDIENT_CONCEPT_MAP.items():
            if ingredient in q_lower:
                concepts.update(d.lower() for d in related_dishes)

        return concepts

    def get_cuisine_family(self, cuisine: str) -> str:
        """Return the family name for a cuisine, or 'other'."""
        for family, members in CUISINE_FAMILIES.items():
            if cuisine in members:
                return family
        return "other"

    def cuisines_are_related(self, c1: str, c2: str) -> bool:
        """Return True if two cuisines belong to the same semantic family."""
        return self.get_cuisine_family(c1) == self.get_cuisine_family(c2) and self.get_cuisine_family(c1) != "other"

    def compute_concept_overlap(self, query_concepts: Set[str], dish_concepts: Set[str]) -> float:
        """
        Compute Jaccard-inspired concept overlap between query and dish concept sets.
        Returns a float in [0, 1].
        """
        if not query_concepts or not dish_concepts:
            return 0.0

        # Normalize both sets to lowercase tokens
        q = {c.lower() for token in query_concepts for c in token.split()}
        d = {c.lower() for token in dish_concepts for c in token.split()}

        intersection = q & d
        if not intersection:
            return 0.0

        # Weighted Jaccard: intersection / union, with a bonus for high-value matches
        union = q | d
        jaccard = len(intersection) / len(union)

        # Bonus: if more than 30% of query terms match, boost score
        query_coverage = len(intersection) / max(len(q), 1)
        return min(jaccard * 0.6 + query_coverage * 0.4, 1.0)

    def get_dish_concepts(self, dish: dict) -> Set[str]:
        """
        Extract all semantic concepts from a dish metadata dict.
        Reads semantic_tags, flavor_profile, dietary_tags, cuisine, name, aliases.
        """
        concepts: Set[str] = set()

        concepts.add(dish.get("cuisine", "").lower())
        concepts.add(dish.get("name", "").lower())

        for field in ["semantic_tags", "flavor_profile", "dietary_tags", "texture_profile", "cultural_tags"]:
            for item in dish.get(field, []):
                concepts.update(item.lower().split())

        for alias in dish.get("aliases", []):
            concepts.update(alias.lower().split())

        for tag in dish.get("tags", []):
            concepts.update(tag.lower().split())

        concepts.update(dish.get("description", "").lower().split())

        return concepts


# Singleton
food_ontology = FoodOntology()
