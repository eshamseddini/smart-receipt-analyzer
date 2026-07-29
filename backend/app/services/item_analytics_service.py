import re


def categorize_item(item_name: str) -> str:
    normalized_name = normalize_item_name(item_name)

    # 1. Specific phrases first
    phrase_rules = [
        ("fruit", ["salade de fruits", "kiwi", "myrtille", "mangue", "citron vert"]),
        ("vegetable_herb", ["laitue", "poireaux", "rutabaga", "carotte", "iceberg"]),
        ("prepared_food", ["pizza", "sandwich", "quiche", "lasagne", "burger", "wrap", "veloute"]),
        ("snack_sweet", ["petit beurre", "nutella", "m&m", "mms", "chocolat", "biscuit"]),
        ("dairy", ["cr.uht", "uht", "lait", "yaourt", "fromage", "creme", "beurre"]),
        (
            "carbohydrate",
            ["spaghetti", "pates", "riz", "pain", "baguette", "frite", "frites", "pdt"],
        ),
        ("beverage", ["the", "cafe", "nescafe", "nesc", "jus", "soda", "eau"]),
        ("household", ["sac kraft", "papier", "sopalin", "mouchoir", "savon", "lessive"]),
        ("stationery", ["roller", "recharge", "effac"]),
    ]

    for category, phrases in phrase_rules:
        if any(phrase in normalized_name for phrase in phrases):
            return category

    # 2. Safer word-based matching
    word_rules = {
        "protein": [
            "poulet",
            "chicken",
            "dinde",
            "turkey",
            "boeuf",
            "steak",
            "thon",
            "saumon",
            "jambon",
            "oeuf",
            "tofu",
        ],
        "vegetable_herb": [
            "salade",
            "tomate",
            "concombre",
            "brocoli",
            "courgette",
            "poivron",
            "oignon",
            "aneth",
            "persil",
            "basilic",
            "menthe",
        ],
        "fruit": [
            "pomme",
            "banane",
            "orange",
            "fraise",
            "raisin",
            "citron",
        ],
        "snack_sweet": [
            "cookie",
            "bonbon",
            "gateau",
            "cereales",
            "muesli",
        ],
    }

    words = set(re.findall(r"[a-z0-9]+", normalized_name))

    for category, keywords in word_rules.items():
        if any(keyword in words for keyword in keywords):
            return category

    return "other"


def normalize_item_name(name: str) -> str:
    return (
        name.lower()
        .replace("œ", "oe")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
        .replace("'", " ")
    )
