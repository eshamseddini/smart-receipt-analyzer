import re
import unicodedata

CATEGORY_RULES: list[tuple[str, list[str]]] = [
    (
        "pet_food",
        [
            "pinky snack",
            "pour chien",
            "mr goodlad",
            "mr. goodlad",
            "bacon boeuf",
        ],
    ),
    (
        "protein",
        [
            "protein pancakes",
            "proteine bites",
            "gummies proteines",
            "barre proteinee",
            "proteine",
            "proteinee",
            "protein",
        ],
    ),
    (
        "meat",
        [
            "viande boeuf",
            "boeuf hache",
            "boeuf hachee",
            "steak",
            "poulet",
            "dinde",
            "jambon",
            "saumon",
            "thon",
        ],
    ),
    (
        "dairy",
        [
            "fromage blanc",
            "cheddar",
            "cheddar rape",
            "lait",
            "yaourt",
            "yogurt",
            "fromage",
            "fromages",
            "creme",
            "beurre doux",
        ],
    ),
    (
        "fruit",
        [
            "citron",
            "kiwi",
            "myrtille",
            "mangue",
            "salade de fruits",
            "fruits hiver",
            "barquette 4 fruits",
        ],
    ),
    (
        "vegetable_herb",
        [
            "champignon",
            "poivron",
            "poivrons",
            "laitue",
            "iceberg",
            "poireaux",
            "rutabaga",
            "carotte",
            "tomate",
            "concombre",
            "brocoli",
            "courgette",
            "oignon",
            "aneth",
            "persil",
            "basilic",
            "menthe",
        ],
    ),
    (
        "carbohydrate",
        [
            "tortillas",
            "tortilla",
            "frites",
            "spaghetti",
            "pates",
            "riz",
            "pain",
            "baguette",
            "pdt",
            "pomme de terre",
            "croutons",
        ],
    ),
    (
        "household",
        [
            "papier toilette",
            "liquide vaisselle",
            "sac de transport",
            "sacs a laniere",
            "sachets congelateur",
            "sac kraft",
            "sac caisse",
            "dumil",
        ],
    ),
    (
        "cosmetics",
        [
            "scrub",
            "body scrub",
            "blush",
            "pinceau",
            "baume",
            "gommage",
            "levres",
            "masque visage",
            "hair booster",
            "gel douche",
            "soin du corps",
            "chev miel",
            "bbume",
            "huile",
        ],
    ),
    (
        "health",
        [
            "patch chauffant",
            "thermofect",
            "douleurs",
            "innovit",
            "biotiques",
            "gommes peau",
        ],
    ),
    (
        "snack_sweet",
        [
            "petit beurre",
            "m&m",
            "m m",
            "minis poch",
            "nutella",
            "milka",
            "twix",
            "haribo",
            "popcorn",
            "croky",
            "baileys creams",
            "flipz",
            "pain d epices",
            "chocolat",
            "choco",
            "biscuit",
            "biscuits",
            "cookie",
            "cookies",
            "muesli",
            "cereales",
            "equilidej",
            "ben j",
            "b&j",
            "pot choc",
            "pancakes",
            "gommes",
        ],
    ),
    (
        "prepared_food",
        [
            "pad thai",
            "noodle bowl",
            "sauce algerienne",
            "pizza",
            "sandwich",
            "quiche",
            "lasagne",
            "burger",
            "wrap",
            "veloute",
            "potage",
            "soupe",
        ],
    ),
    (
        "beverage",
        [
            "the",
            "cafe",
            "nescafe",
            "nesc",
            "jus",
            "soda",
            "eau",
        ],
    ),
    (
        "stationery",
        [
            "roller",
            "effac",
            "recharge",
            "recharges",
        ],
    ),
]


def categorize_item(item_name: str) -> str:
    normalized_name = normalize_item_name(item_name)

    for category, phrases in CATEGORY_RULES:
        if any(phrase in normalized_name for phrase in phrases):
            return category

    return "other"


def normalize_item_name(name: str) -> str:
    normalized = name.lower()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))

    normalized = normalized.replace("œ", "oe")
    normalized = normalized.replace("'", " ")
    normalized = normalized.replace(".", " ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("&", " & ")

    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()
