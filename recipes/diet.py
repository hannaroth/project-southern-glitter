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

MEAT_CATEGORIES = ("beef", "chicken", "lamb", "pork", "seafood", "goat")

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


MEAT_FISH_KEYWORDS = [
    "chicken", "beef", "pork", "lamb", "mutton", "veal", "venison", "goat", "duck", "goose",
    "turkey", "bacon", "ham", "gammon", "sausage", "chorizo", "salami", "pepperoni",
    "prosciutto", "pancetta", "mince", "minced", "mincemeat", "meat", "liver", "kidney",
    "oxtail", "lard", "suet", "dripping", "gelatin", "gelatine", "fish", "salmon", "tuna",
    "cod", "haddock", "hake", "mackerel", "sardine", "anchovy", "anchovie", "prawn", "shrimp",
    "crab", "lobster", "mussel", "clam", "oyster", "scallop", "squid", "octopus", "calamari",
    "worcestershire sauce", "stock", "broth", "bouillon",
    "black pudding", "blood pudding", "dashi", "bonito", "katsuobushi", "caviar", "roe",
    "trout", "sea bass", "bass", "halibut", "herring", "eel", "tilapia", "snapper",
    "swordfish", "monkfish", "mahi mahi", "kipper", "cockle", "whelk", "langoustine",
    "crevette", "surimi", "fishcake", "cuttlefish", "escargot", "snail", "steak", "ribeye",
    "sirloin", "tenderloin", "ribs", "short ribs", "brisket", "rabbit", "pheasant", "quail",
    "pigeon", "bresaola", "mortadella", "hot dog", "frankfurter", "lardon", "guanciale",
    "nduja", "pastrami", "spam", "meatball", "jerky", "wings", "drumstick", "poultry",
    "bone marrow", "marrow bone", "foie gras", "tripe", "tongue", "offal", "sweetbread",
    "haggis", "pate", "pâté", "tallow", "schmaltz", "crackling", "oxo", "bovril", "gravy",
    "nam pla", "shrimp paste", "curry paste", "caesar dressing", "xo sauce",
]
# Exact meat-free phrases removed before the keyword check. Anything left over is still
# checked, so "Chicken and vegetable stock" stays meat. Never exempt a bare word like "vegetable".
MEAT_FREE_PHRASES = [
    "vegetable stock cube", "vegetable stock", "vegetable broth", "vegetable bouillon",
    "veggie stock", "vegan stock", "veggie sausage", "vegetarian sausage", "vegan sausage",
    "vegetarian mince", "vegan mince", "meat-free mince", "plant-based mince",
    "vegetable suet", "vegetarian suet", "vegetarian gelatine", "vegan gelatine",
    "vegetarian worcestershire sauce", "vegan fish sauce", "vegan curry paste",
    "vegetarian curry paste",
]
# Phrases removed before the meat check, so they cannot trigger a keyword.
MEAT_SAFE_PHRASES = ["kidney bean", "kidney beans", "butternut", "coconut"]
EGG_HONEY_KEYWORDS = [
    "egg", "egg yolk", "egg white", "honey", "mayonnaise", "mayo", "ghee",
]


def _compile(words):
    # Whole words, with an optional plural "s"/"es".
    alt = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<![a-z])(?:{alt})(?:e?s)?(?![a-z])")


_GLUTEN_RE = _compile(GLUTEN_KEYWORDS)
_DAIRY_RE = _compile(DAIRY_KEYWORDS)
_NUT_RE = _compile(NUT_KEYWORDS)
_MEAT_RE = _compile(MEAT_FISH_KEYWORDS)
_EGG_HONEY_RE = _compile(EGG_HONEY_KEYWORDS)
_MEAT_SAFE_RE = re.compile("|".join(re.escape(p) for p in sorted(MEAT_SAFE_PHRASES, key=len, reverse=True)))
_MEAT_FREE_RE = re.compile(
    r"(?<![a-z])(?:" + "|".join(re.escape(p) for p in sorted(MEAT_FREE_PHRASES, key=len, reverse=True))
    + r")(?:e?s)?(?![a-z])"
)
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


def _has_meat(names):
    for n in names:
        text = " ".join((n or "").lower().split())
        text = _MEAT_FREE_RE.sub(" ", text)
        if _MEAT_RE.search(_MEAT_SAFE_RE.sub(" ", text)):
            return True
    return False


def _has_egg_or_honey(names):
    return any(_EGG_HONEY_RE.search((n or "").lower()) for n in names)


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
    dairy = _any(_DAIRY_RE, names, ("dairy-free", "dairy free", "non-dairy"))
    # Conservative: a wrong "vegetarian" tag is worse than a missing one.
    vegetarian = category in ("vegetarian", "vegan") or (
        bool(names) and category not in MEAT_CATEGORIES and not _has_meat(names)
    )
    vegan = category == "vegan" or (vegetarian and not dairy and not _has_egg_or_honey(names))
    if vegetarian:
        tags.append(TAG_VEGETARIAN)
    if vegan:
        tags.append(TAG_VEGAN)
    if _any(_GLUTEN_RE, names, ("gluten-free", "gluten free")):
        tags.append(TAG_GLUTEN)
    if dairy:
        tags.append(TAG_DAIRY)
    if _any(_NUT_RE, names, ("nut-free", "nut free"), keep=_NUT_ONLY_RESTORE):
        tags.append(TAG_NUTS)
    return tags
