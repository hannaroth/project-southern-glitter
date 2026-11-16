"""Best-effort diet tags and course for a recipe. Always show the allergy note next to them."""

import re

ALLERGY_NOTE = "Check the ingredients yourself for allergies."

COURSE_STARTER = "starter"
COURSE_MAIN = "main"
COURSE_DESSERT = "dessert"

TAG_VEGETARIAN = "vegetarian"
TAG_VEGAN = "vegan"
TAG_GLUTEN = "contains_gluten"
TAG_DAIRY = "contains_dairy"
TAG_NUTS = "contains_nuts"

# Phrases removed before matching, so they cannot trigger a keyword.
SAFE_PHRASES = [
    "coconut milk",
    "coconut cream",
    "coconut oil",
    "coconut butter",
    "almond milk",
    "soy milk",
    "soya milk",
    "oat milk",
    "rice milk",
    "cashew milk",
    "peanut butter",  # handled as a nut below via "peanut"; keep phrase out of dairy
    "cocoa butter",
    "butternut",
    "nutmeg",
    "water chestnut",
    "buttercup",
]
# "peanut butter" must still count as nuts, so it is restored for the nuts check only.
_NUT_ONLY_RESTORE = ("peanut butter",)

GLUTEN_KEYWORDS = [
    "flour", "bread", "breadcrumb", "panko", "pasta", "spaghetti", "noodle", "macaroni",
    "lasagne", "lasagna", "linguine", "penne", "fettuccine", "tagliatelle", "couscous",
    "bulgur", "barley", "rye", "wheat", "semolina", "seitan", "pastry", "pie crust",
    "pizza dough", "tortilla", "pitta", "pita", "naan", "baguette", "croissant", "biscuit",
    "cracker", "digestive", "ladyfinger", "sponge", "filo", "phyllo", "puff pastry",
    "soy sauce", "beer", "ale", "stout", "oat", "crouton", "dumpling", "gnocchi",
    "cake", "bun", "roll", "wrap", "batter", "stuffing", "malt",
]
DAIRY_KEYWORDS = [
    "milk", "cream", "butter", "cheese", "cheddar", "mozzarella", "parmesan", "feta",
    "ricotta", "mascarpone", "gruyere", "halloumi", "paneer", "yogurt", "yoghurt",
    "ghee", "custard", "creme fraiche", "crème fraîche", "whey", "casein", "gouda",
    "brie", "camembert", "stilton", "cottage cheese", "ice cream", "condensed milk",
    "evaporated milk", "buttermilk", "sour cream", "labneh", "kefir",
]
NUT_KEYWORDS = [
    "almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut", "macadamia",
    "peanut", "pine nut", "pinenut", "brazil nut", "chestnut", "praline", "marzipan",
    "nutella", "nut",
]


def _compile(words):
    # Whole words, with an optional plural "s"/"es".
    alt = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<![a-z])(?:{alt})(?:e?s)?(?![a-z])")


_GLUTEN_RE = _compile(GLUTEN_KEYWORDS)
_DAIRY_RE = _compile(DAIRY_KEYWORDS)
_NUT_RE = _compile(NUT_KEYWORDS)
_SAFE_RE = re.compile("|".join(re.escape(p) for p in sorted(SAFE_PHRASES, key=len, reverse=True)))


def _clean(name, keep=()):
    text = (name or "").lower()
    return _SAFE_RE.sub(lambda m: m.group(0) if m.group(0) in keep else " ", text)


def _any(regex, names, free_markers, keep=()):
    # An ingredient labelled "gluten-free ..." etc. never triggers that tag.
    return any(
        not any(m in n.lower() for m in free_markers) and regex.search(_clean(n, keep))
        for n in names
    )


def course_for_category(category):
    category = (category or "").strip().lower()
    if category in ("starter", "side"):
        return COURSE_STARTER
    if category == "dessert":
        return COURSE_DESSERT
    return COURSE_MAIN


def ingredient_names(ingredients):
    return [i.get("name", "") if isinstance(i, dict) else str(i) for i in ingredients or []]


def derive_diet_tags(category, ingredients):
    """Return the diet tag list for a category and a list of {"name", "measure"} dicts (or names)."""
    category = (category or "").strip().lower()
    names = ingredient_names(ingredients)
    tags = []
    if category in ("vegetarian", "vegan"):
        tags.append(TAG_VEGETARIAN)
    if category == "vegan":
        tags.append(TAG_VEGAN)
    if _any(_GLUTEN_RE, names, ("gluten-free", "gluten free")):
        tags.append(TAG_GLUTEN)
    if _any(_DAIRY_RE, names, ("dairy-free", "dairy free", "non-dairy")):
        tags.append(TAG_DAIRY)
    if _any(_NUT_RE, names, ("nut-free", "nut free"), keep=_NUT_ONLY_RESTORE):
        tags.append(TAG_NUTS)
    return tags
