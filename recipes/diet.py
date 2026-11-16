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
    "nam pla", "shrimp paste", "curry paste", "caesar dressing", "xo sauce", "rendang",
]
# Phrases removed before the meat check, so they cannot trigger a keyword.
MEAT_SAFE_PHRASES = ["kidney bean", "kidney beans", "butternut", "coconut"]
EGG_HONEY_KEYWORDS = [
    "egg", "egg yolk", "egg white", "honey", "mayonnaise", "mayo", "ghee",
]


# Allowlist for the ingredient path: an ingredient counts as known vegetarian only if it is one of
# these exact phrases, or EVERY word of it is in VEGETARIAN_WORDS. An unknown word means the recipe
# is not tagged (a missing tag is fine, a wrong one is not). Generic or ambiguous words (stock, broth,
# cube, gravy, sauce, paste, curry, jus, fat, suet, gelatine, jelly, marshmallow, pudding, mince,
# sausage, burger, bacon, ham, meat, bone, marrow, roe, fish, dressing, bisque, ...) must never be in
# VEGETARIAN_WORDS; they may only appear inside an exact phrase below. Plain "marrow" is a vegetable
# but ambiguous (bone marrow), so it is deliberately not listed.
VEGETARIAN_PHRASES = {
    "vegetable stock", "vegetable stock cube", "vegetable broth", "vegetable bouillon",
    "veggie stock", "vegan stock", "veggie sausage", "vegetarian sausage", "vegan sausage",
    "vegetarian mince", "vegan mince", "meat free mince", "plant based mince", "vegetable suet",
    "vegetarian suet", "soy sauce", "soya sauce", "light soy sauce", "dark soy sauce",
    "tomato puree", "tomato paste", "tomato ketchup", "tomato sauce", "baking powder",
    "bicarbonate of soda", "cream of tartar", "golden syrup", "maple syrup", "peanut butter",
    "almond butter", "cocoa butter", "coconut milk", "coconut cream", "coconut oil", "almond milk",
    "soy milk", "soya milk", "oat milk", "rice milk", "cashew milk", "puff pastry",
    "shortcrust pastry", "filo pastry", "phyllo pastry", "icing sugar", "caster sugar",
    "brown sugar", "kidney bean", "red wine vinegar", "white wine vinegar", "rice wine vinegar",
    "rice vinegar", "sherry vinegar", "balsamic vinegar", "apple cider vinegar", "cider vinegar",
    "vanilla paste", "vanilla bean paste", "salt and pepper", "sea salt", "water chestnut",
    "cranberry sauce", "sweet chilli sauce", "chilli sauce", "hot sauce", "tahini paste",
    "sesame paste", "miso paste", "almond paste", "bean paste", "rice paper", "spring roll wrapper",
    "mixed spice", "mixed peel", "mixed herbs", "mixed nuts", "mixed seeds", "mixed vegetables",
}
VEGAN_OK_PHRASES = {
    "coconut milk", "coconut cream", "peanut butter", "almond butter", "cocoa butter", "almond milk",
    "soy milk", "soya milk", "oat milk", "rice milk", "cashew milk", "vegetable stock",
    "vegetable stock cube", "vegetable broth", "vegetable bouillon", "veggie stock", "vegan stock",
    "veggie sausage", "vegetarian sausage", "vegan sausage", "vegetarian mince", "vegan mince",
    "meat free mince", "plant based mince", "vegetable suet", "vegetarian suet", "filo pastry",
    "phyllo pastry",
}
# Extra words that stop the "vegan" tag (the dairy/egg/honey keyword lists apply as well).
NOT_VEGAN_WORDS = {
    "milk", "butter", "cream", "cheese", "cheddar", "mozzarella", "parmesan", "parmigiano",
    "reggiano", "feta", "ricotta", "mascarpone", "gruyere", "halloumi", "paneer", "gouda", "brie",
    "camembert", "stilton", "emmental", "edam", "cottage", "yogurt", "yoghurt", "kefir", "custard",
    "ghee", "whey", "casein", "egg", "yolk", "honey", "mayonnaise", "mayo", "buttermilk",
    "pastry", "puff", "shortcrust", "biscuit", "digestive", "marzipan", "naan", "brioche",
    "meringue", "cake", "sponge", "ladyfinger", "ice",
}
NOT_VEGAN_PHRASES = ("milk chocolate", "white chocolate", "chocolate chip cookie")
VEGETARIAN_WORDS = set("""
 vegetable veggie vegetarian vegan plant based
 tomato cherry plum sun dried passata ketchup onion shallot garlic clove leek chive chives
 spring scallion potato yam sweet carrot parsnip turnip swede beetroot beet radish celeriac celery
 fennel cabbage savoy kale cavolo nero lettuce rocket arugula watercress spinach chard
 broccoli tenderstem cauliflower courgette zucchini aubergine eggplant pepper capsicum chilli chili
 jalapeno habanero cucumber gherkin pickle pickled caper olive artichoke asparagus pea mangetout
 sugar snap bean broad runner green french edamame sweetcorn corn maize squash butternut pumpkin
 mushroom shiitake portobello chestnut button oyster cep porcini truffle ginger galangal
 lemongrass turmeric horseradish okra avocado
 apple pear peach apricot nectarine cherry plum damson berry strawberry raspberry blueberry
 blackberry cranberry gooseberry redcurrant blackcurrant currant grape raisin sultana fig date
 prune banana mango pineapple papaya kiwi melon watermelon orange lemon lime grapefruit
 clementine tangerine satsuma mandarin pomegranate rhubarb coconut tamarind peel zest juice
 jam marmalade compote
 basil parsley coriander cilantro mint dill thyme rosemary sage oregano marjoram tarragon bay
 laurel lovage chervil sorrel herb herbes provence leaf leaves stalk sprig bunch
 cumin cinnamon nutmeg mace clove cardamom paprika cayenne saffron fenugreek mustard fennel
 caraway aniseed anise star allspice juniper sumac zaatar garam masala curry powder coriander
 seed sesame poppy pepper peppercorn salt spice vanilla extract essence
 rice basmati jasmine arborio risotto paella wild brown wholegrain wholemeal wheat bulgur couscous
 quinoa barley oat oats oatmeal porridge millet polenta cornmeal semolina cornflour cornstarch
 starch flour plain self raising strong bread rye spelt gram chickpea besan tapioca arrowroot
 lentil split red puy chickpea hummus houmous black eyed borlotti cannellini haricot kidney
 butter flageolet pinto mung soya soy tofu tempeh seitan
 almond walnut pecan cashew pistachio hazelnut macadamia peanut pine nut brazil pinenut
 flaxseed linseed sunflower pumpkin chia hemp
 oil olive sunflower vegetable rapeseed canola groundnut sesame walnut vinegar balsamic
 cider malt
 sugar caster icing granulated demerara muscovado treacle syrup molasses agave stevia
 yeast baking soda bicarbonate tartar
 milk butter cream cheese cheddar mozzarella parmesan parmigiano reggiano feta ricotta
 mascarpone gruyere halloumi paneer gouda brie camembert stilton emmental edam cottage yogurt
 yoghurt kefir buttermilk custard ghee margarine
 egg yolk white honey chocolate cocoa cacao carob
 pasta spaghetti penne fusilli farfalle linguine fettuccine tagliatelle rigatelle rigatoni
 macaroni lasagne lasagna orzo vermicelli noodle gnocchi ravioli tortellini udon soba ramen
 rice paper wrapper tortilla wrap pitta pita naan chapati roti baguette ciabatta focaccia sourdough
 brioche bun roll bagel crumpet muffin toast breadcrumb panko crouton pastry dough sheet
 water ice sparkling mineral boiling hot cold warm
 fresh dried ground chopped sliced diced grated shredded crushed minced finely roughly torn
 frozen tinned canned jarred tin can packet large small medium big mini baby thin thick thinly
 red green yellow white black brown golden orange purple pink dark light double single
 unsalted salted extra virgin whole free range ripe sweet hot mild smoked toasted roasted raw
 cooked boiled steamed mixed organic good quality seedless skinless pitted stoned peeled
 unsweetened sweetened low fat full skimmed semi skimmed natural greek style set
 long short thin fine coarse sea table kosher rock flaked flake desiccated
 cup tablespoon teaspoon pinch handful splash dash to taste of and or with for
 bicarbonate soda powder
 sprout sprouts beansprout bean shoot bamboo lotus root water chestnut kohlrabi
 chicory endive radicchio frisee mizuna pak choi bok choy choi pakchoi tatsoi
 tahini miso wasabi nori kimchi
 ketchup mayonnaise mayo
 sultana
""".split())
VEGETARIAN_WORDS -= {
    "stock", "broth", "bouillon", "cube", "gravy", "sauce", "paste", "curry", "jus", "fat",
    "dripping", "suet", "gelatine", "gelatin", "jelly", "marshmallow", "pudding", "mince",
    "sausage", "burger", "bacon", "ham", "meat", "bone", "marrow", "roe", "fish", "dressing",
    "bisque", "consomme", "rennet", "isinglass", "collagen", "cochineal", "carmine",
    "worcestershire", "marmite", "vegemite", "maggi", "flavoured", "style", "bits", "crackers",
    "can", "tin", "sheet", "set", "good",
}
VEGETARIAN_WORDS -= {
    "of", "and", "or", "with", "for", "to", "taste", "cup", "wild", "kidney", "oyster", "paper",
    "wrapper", "wrap", "ice",
}
VEGETARIAN_PHRASES |= {
    "wild rice", "red kidney bean", "wild garlic", "artichoke heart", "cavolo nero", "bean sprout", "pak choi",
    "bok choy", "sun dried tomato", "sundried tomato", "greek yogurt", "greek yoghurt",
}



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


def _normalise(name):
    """Lowercase, punctuation (hyphens, slashes, commas, &, brackets) to spaces, one space between words."""
    text = (name or "").lower()
    text = re.sub(r"[-/,&()\[\]]", " ", text)
    return " ".join(text.split())


def _singular_forms(word):
    # Same idea as the keyword matcher's optional "s"/"es", plus "berries" -> "berry".
    forms = [word]
    if word.endswith("ies") and len(word) > 4:
        forms.append(word[:-3] + "y")
    if word.endswith("es") and len(word) > 3:
        forms.append(word[:-2])
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        forms.append(word[:-1])
    return forms


def _in_set(word, allowed):
    return any(f in allowed for f in _singular_forms(word))


def _is_known_phrase(text, phrases):
    words = text.split()
    if not words:
        return False
    return any(" ".join(words[:-1] + [last]).strip() in phrases for last in _singular_forms(words[-1]))


def _is_known_vegetarian(name):
    """Allowlist: an exact known phrase, or every single word on the known-vegetarian word list."""
    text = _normalise(name)
    if _is_known_phrase(text, VEGETARIAN_PHRASES):
        return True
    words = text.split()
    return bool(words) and all(_in_set(w, VEGETARIAN_WORDS) for w in words)


def _has_meat(names):
    """Extra veto: any ingredient with a meat/fish keyword, unless it is exactly a known phrase."""
    for n in names:
        text = _normalise(n)
        if _is_known_phrase(text, VEGETARIAN_PHRASES):
            continue
        if _MEAT_RE.search(_MEAT_SAFE_RE.sub(" ", text)):
            return True
    return False


def _all_known_vegetarian(names):
    return all(_is_known_vegetarian(n) for n in names)


def _vegan_ok(name):
    text = _normalise(name)
    if _is_known_phrase(text, VEGAN_OK_PHRASES):
        return True
    if any(p in text for p in NOT_VEGAN_PHRASES):
        return False
    return not any(_in_set(w, NOT_VEGAN_WORDS) for w in text.split())


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
    # Allowlist: every ingredient must be known vegetarian; the meat/fish keywords are an extra veto.
    from_ingredients = (
        bool(names) and category not in MEAT_CATEGORIES
        and not _has_meat(names) and _all_known_vegetarian(names)
    )
    vegetarian = category in ("vegetarian", "vegan") or from_ingredients
    vegan = category == "vegan" or (
        from_ingredients and not dairy and not _has_egg_or_honey(names)
        and all(_vegan_ok(n) for n in names)
    )
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
