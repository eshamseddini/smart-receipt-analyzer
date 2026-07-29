import re
from datetime import datetime

from app.schemas.receipt_schema import ExtractedReceiptData
from app.services.item_categorization_service import categorize_item


SUPPORTED_MERCHANTS = {
    "LIDL",
    "LECLERC",
    "SUPER U",
    "ACTION",
    "ALDI",
    "CARREFOUR",
    "INTERMARCHE",
    "FRANPRIX"
}

# Merchants without a dedicated, hand-tuned parser yet. They share a
# best-effort generic parser (name + trailing price) instead of a fallback
# that silently tries every merchant's parser and risks producing wrong data.
GENERIC_PARSER_MERCHANTS = {"ALDI", "CARREFOUR", "INTERMARCHE", "FRANPRIX"}


def extract_structured_data(
    extracted_text: str,
    document_type: str
) -> ExtractedReceiptData:
    """
    Extract structured receipt data from OCR text.

    Only supported merchants are accepted.
    Unsupported merchants are rejected instead of producing unreliable data.
    """

    merchant_name = extract_merchant_name(extracted_text)

    if merchant_name not in SUPPORTED_MERCHANTS:
        raise ValueError(
            "Unsupported merchant. This document cannot be processed automatically."
        )

    items = extract_items(
        text=extracted_text,
        merchant_name=merchant_name,
    )

    if not items:
        raise ValueError(
            "No valid items were extracted. This document needs manual review."
        )

    total_amount = extract_total_amount(extracted_text)

    return ExtractedReceiptData(
        merchant_name=merchant_name,
        purchase_date=extract_purchase_date(extracted_text),
        total_amount=total_amount,
        discount_amount=extract_discount_amount_from_text(extracted_text),
        currency=extract_currency(extracted_text),
        category_totals=calculate_category_totals_from_items(items),
        items=items,
    )


# -------------------------------------------------------------------
# Merchant
# -------------------------------------------------------------------

def extract_merchant_name(text: str) -> str | None:
    lower_text = normalize_ocr_text(text.lower())

    merchant_patterns = [
        ("LIDL", ["lidl"]),
        ("LECLERC", ["e.leclerc", "e leclerc", "eleclerc", "leclerc"]),
        ("SUPER U", ["super u", "magasin u", "commercants autrement", "commercantes autrement", "carte u"]),
        ("ACTION", ["//action", " action", "allee de guerledan"]),
        ("CARREFOUR", ["carrefour"]),
        ("INTERMARCHE", ["intermarche"]),
        ("FRANPRIX", ["franprix"]),
    ]

    for merchant, keywords in merchant_patterns:
        if any(keyword in lower_text for keyword in keywords):
            return merchant

    return None


# -------------------------------------------------------------------
# Date / Total / Currency
# -------------------------------------------------------------------

def extract_purchase_date(text: str) -> str | None:
    normalized_text = normalize_ocr_text(text)

    patterns = [
        r"\b(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{4})\b",
        r"\b(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2})\b",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, normalized_text)

        for match in matches:
            day = int(match[0])
            month = int(match[1])
            year = int(match[2])

            if year < 100:
                year += 2000

            try:
                parsed_date = datetime(year, month, day)
                return parsed_date.date().isoformat()
            except ValueError:
                continue

    return None


def extract_total_amount(text: str) -> float | None:
    normalized_text = normalize_ocr_text(text.lower())

    priority_patterns = [
        r"total\s+\d+\s+articles?\s+(\d+[,.]\d{2})",
        r"total\s*\[\d+\]\s*articles?\s+(\d+[,.]\d{2})",
        r"total\s+\d+\s+(\d+[,.]\d{2})",
        r"(?:a payer|à payer)\s+(\d+[,.]\d{2})",
        r"cb\s+sans\s+contact\s+(\d+[,.]\d{2})",
        r"montant\s*=\s*(\d+[,.]\d{2})",
        r"carte\s+(\d+[,.]\d{2})",
    ]

    for pattern in priority_patterns:
        match = re.search(pattern, normalized_text)

        if match:
            return parse_amount(match.group(1))

    candidate_lines = []

    ignored_total_contexts = [
        "sous - total",
        "sous-total",
        "total tva",
        "tva ht ttc",
        "mont.tva",
        "total ht",
        "cumul disponible",
        "solde",
        "bon achat",
        "transaction",
        "telephone",
        "tel.",
        "tel :",
        "tel:",
        "siret",
        "capital",
    ]

    for line in get_clean_lines(normalized_text):
        lower_line = line.lower()

        if any(ignored in lower_line for ignored in ignored_total_contexts):
            continue

        candidate_lines.append(line)

    amounts: list[str] = []

    for line in candidate_lines:
        amounts.extend(re.findall(r"\b\d+[,.]\d{2}\b", line))

    parsed_amounts = [
        amount
        for amount in (parse_amount(value) for value in amounts)
        if amount is not None
    ]

    if not parsed_amounts:
        return None

    return max(parsed_amounts)


def extract_currency(text: str) -> str:
    upper_text = text.upper()

    if "EUR" in upper_text or "€" in upper_text:
        return "EUR"

    if "USD" in upper_text or "$" in upper_text:
        return "USD"

    if "GBP" in upper_text or "£" in upper_text:
        return "GBP"

    return "EUR"


# -------------------------------------------------------------------
# Items extraction
# -------------------------------------------------------------------

def extract_items(
    text: str,
    merchant_name: str
) -> list[dict]:
    normalized_text = normalize_ocr_text(text)
    lines = get_clean_lines(normalized_text)

    items: list[dict] = []

    ignored_keywords = [
        "ticket",
        "article p.u",
        "article p.u.eur",
        "ttc tva",
        "reduction",
        "lidl plus",
    ]

    for index, line in enumerate(lines):
        lower_line = normalize_ocr_text(line.lower()).strip()

        if is_quantity_detail_line(line):
            continue

        if is_section_header(line):
            continue

        if should_stop_item_extraction(lower_line):
            break

        if any(keyword in lower_line for keyword in ignored_keywords):
            continue

        if is_tax_line(line):
            continue

        if is_discount_line(line):
            continue

        item = parse_item_line_by_merchant(
            line=line,
            lines=lines,
            index=index,
            merchant_name=merchant_name,
        )

        if not item:
            continue

        item["category"] = categorize_item(item["name"])
        items.append(item)

    return items


def parse_item_line_by_merchant(
    line: str,
    lines: list[str],
    index: int,
    merchant_name: str | None,
) -> dict | None:
    """
    No generic fallback.

    If the merchant is not supported, we return None instead of trying
    all parsers and risking false items.
    """

    if merchant_name == "LIDL":
        return parse_lidl_item_line(line)

    if merchant_name == "SUPER U":
        return parse_super_u_item_line(line, lines, index)

    if merchant_name == "LECLERC":
        return parse_leclerc_item_line(line)

    if merchant_name == "ACTION":
        return parse_action_item_line(line)

    if merchant_name in GENERIC_PARSER_MERCHANTS:
        return parse_generic_item_line(line)

    return None


# -------------------------------------------------------------------
# Merchant parsers
# -------------------------------------------------------------------

def parse_action_item_line(line: str) -> dict | None:
    """
    Action format examples:
    milka tablette choco 300g choco 1 3,39 eur
    hair booster shot set 3x60ml 2 4,98 eur
    accelerate protein pancakes 150g 1 195 eur
    """

    normalized_line = normalize_action_line(line)

    pattern = re.compile(
        r"^(?P<name>.+?)\s+"
        r"(?P<quantity>\d+(?:[,.]\d+)?)\s+"
        r"(?P<total_price>[0-9a-zA-Z,.]+)"
        r"(?:\s*(?:eur|€)\s*[a-zA-Z]*)?\s*$",
        re.IGNORECASE,
    )

    match = pattern.search(normalized_line)

    if not match:
        return None

    name = clean_item_name(match.group("name"))
    quantity = parse_quantity(match.group("quantity")) or 1.0
    total_price = parse_noisy_amount(match.group("total_price"))

    if not name or total_price is None:
        return None

    if should_ignore_product_name(name):
        return None

    unit_price = round(total_price / quantity, 2) if quantity else total_price

    return {
        "name": name,
        "unit_price": unit_price,
        "quantity": quantity,
        "total_price": total_price,
    }


def parse_lidl_item_line(line: str) -> dict | None:
    """
    Lidl format:
    Article P.U.EUR Qté EUR

    Examples:
    Citron 750g 1,85 1 1,85 AT
    Fromage blanc nature 1,79 1 1,79 AT
    Papier toilette 2 pl 1,27 1 1,27 B
    """

    normalized_line = normalize_lidl_line(line)

    pattern = re.compile(
        r"^(?P<name>.+?)\s+"
        r"(?P<unit_price>\d+[,.]\d{2})\s+"
        r"(?P<quantity>\d+(?:[,.]\d+)?)\s+"
        r"(?P<total_price>\d+[,.]\d{2})"
        r"(?:\s+[A-Z]{1,2})?$",
        re.IGNORECASE,
    )

    match = pattern.search(normalized_line)

    if not match:
        return None

    name = clean_item_name(match.group("name"))
    unit_price = parse_amount(match.group("unit_price"))
    quantity = parse_quantity(match.group("quantity")) or 1.0
    total_price = parse_amount(match.group("total_price"))

    if not name or unit_price is None or total_price is None:
        return None

    if should_ignore_product_name(name):
        return None

    unit_price, total_price = fix_item_prices(
        unit_price=unit_price,
        quantity=quantity,
        total_price=total_price,
    )

    return {
        "name": name,
        "unit_price": unit_price,
        "quantity": quantity,
        "total_price": total_price,
    }


def parse_super_u_item_line(
    line: str,
    lines: list[str],
    index: int
) -> dict | None:
    """
    Super U format examples:
    CROUTONS ROND.FRIT.NAT.U 2X90G 1,12 € 11
    EQUILIDEJ CROUS.CHOC.BJORG500G 4,00 € Il
    M&M'S MINIS POCH.360G FAM.PACK 4,99 € Ill
    """

    product_pattern = re.compile(
        r"^(?P<name>.+?)\s+"
        r"(?P<total_price>\d+[,.]\d{2})\s*(?:eur|€)?\s*"
        r"(?P<tax_code>[0-9ilIL]{1,3})?$",
        re.IGNORECASE,
    )

    match = product_pattern.search(line)

    if not match:
        return None

    name = clean_item_name(match.group("name"))
    total_price = parse_amount(match.group("total_price"))

    if not name or total_price is None:
        return None

    if should_ignore_product_name(name):
        return None

    quantity = 1.0
    unit_price = total_price

    if index + 1 < len(lines):
        next_line = normalize_ocr_text(lines[index + 1].lower())

        quantity_match = re.search(
            r"^(?P<quantity>\d+(?:[,.]\d+)?)\s*x+\s*"
            r"(?P<unit_price>\d+[,.]\d{2})\s*(?:eur)?$",
            next_line,
        )

        if quantity_match:
            quantity = parse_quantity(quantity_match.group("quantity")) or 1.0
            unit_price = parse_amount(quantity_match.group("unit_price")) or total_price

    unit_price, total_price = fix_item_prices(
        unit_price=unit_price,
        quantity=quantity,
        total_price=total_price,
    )

    return {
        "name": name,
        "unit_price": unit_price,
        "quantity": quantity,
        "total_price": total_price,
    }


def parse_leclerc_item_line(line: str) -> dict | None:
    """
    Leclerc invoice format:
    PRODUCT NAME (barcode) quantity unit_price VAT total_price

    Example:
    SALADE DE FRUITS HIVER (0205766000000) 1 464 5%50 4.90
    SHAKER KIWI MANGUE MYRTILLE (0208582000000) 1 3.69) 5%50 3.89)
    CITRON VERT CAT1 FILET 500G (3564706579484) 1 236 5%50 249
    """

    normalized_line = normalize_ocr_text(line)
    normalized_line = re.sub(r"\s+", " ", normalized_line).strip()

    pattern = re.compile(
        r"^(?P<name>.+?)\s+"
        r"(?:\(\d{8,}\)\s+)?"
        r"(?P<quantity>\d+(?:[,.]\d+)?)\s+"
        r"(?P<unit_price>\d+[,.]?\d{2})\)?\s+"
        r"(?P<tva>\d+%\d{2})\s+"
        r"(?P<total_price>\d+[,.]?\d{2})\)?\|?$",
        re.IGNORECASE,
    )

    match = pattern.search(normalized_line)

    if not match:
        return None

    name = clean_item_name(match.group("name"))
    quantity = parse_quantity(match.group("quantity")) or 1.0
    unit_price = parse_noisy_amount(match.group("unit_price"))
    total_price = parse_noisy_amount(match.group("total_price"))

    if not name or unit_price is None or total_price is None:
        return None

    if should_ignore_product_name(name):
        return None

    unit_price, total_price = fix_item_prices(
        unit_price=unit_price,
        quantity=quantity,
        total_price=total_price,
    )

    return {
        "name": name,
        "unit_price": unit_price,
        "quantity": quantity,
        "total_price": total_price,
    }


def parse_generic_item_line(line: str) -> dict | None:
    """
    Best-effort parser shared by merchants without a hand-tuned format yet
    (see GENERIC_PARSER_MERCHANTS). Assumes the common French receipt layout:

    <product name> <total_price>€

    Examples (Carrefour, noisy OCR):
    HEGIANO RE a 2.98€
    x6 OEUFS POULES ELE 1.81€
    x6X30G CHIPS LISSE 1,90€

    No quantity/unit price column is assumed — quantity defaults to 1 and
    unit_price equals total_price, since the format varies too much between
    unsupported merchants to parse reliably without real samples.
    """

    normalized_line = normalize_ocr_text(line)

    pattern = re.compile(
        r"^(?P<name>.+?)\s+"
        r"(?P<total_price>\d+[,.]\d{2})\s*(?:eur|€)\b",
        re.IGNORECASE,
    )

    match = pattern.search(normalized_line)

    if not match:
        return None

    name = clean_item_name(match.group("name"))
    total_price = parse_amount(match.group("total_price"))

    if not name or total_price is None:
        return None

    if should_ignore_product_name(name):
        return None

    return {
        "name": name,
        "unit_price": total_price,
        "quantity": 1.0,
        "total_price": total_price,
    }


# -------------------------------------------------------------------
# Item filters / helpers
# -------------------------------------------------------------------

def is_quantity_detail_line(line: str) -> bool:
    """
    Ignore lines like:
    1 x 1,12 EUR
    1 xX 1,05 EUR
    """

    normalized_line = normalize_ocr_text(line.lower()).strip()

    return bool(
        re.match(
            r"^\d+(?:[,.]\d+)?\s*x+\s*\d+[,.]\d{2}\s*(?:eur)?$",
            normalized_line,
        )
    )


def is_section_header(line: str) -> bool:
    normalized_line = normalize_ocr_text(line.lower()).strip()

    section_headers = [
        "epicerie",
        "fraiche decoupe",
        "fruits et legumes",
        "papet rdc",
        "aides a la cuisine",
        "biscuits sucres",
        "cereales et poudres chocolat",
        "chocolats snacking",
        "fruits",
        "laits et derives",
        "legumes",
        "potages",
        "sacherie",
        "surgele sale",
        "surgele sucre",
    ]

    return (
        normalized_line in section_headers
        or normalized_line.startswith(">>")
        or normalized_line.startswith("***")
    )


def should_stop_item_extraction(lower_line: str) -> bool:
    normalized_line = normalize_ocr_text(lower_line).strip()

    stop_prefixes = [
        "nombre de lignes",
        "nombre de lignes d'article",
        "total ",
        "total [",
        "sous - total",
        "sous-total",
        "cb sans contact",
        "carte bancaire",
        "bon achat carte",
        "vos avantages",
        "echange",
        "echanges",
        "siret",
        "code magasin",
        "no carte",
        "votre solde",
        "ticket a conserver",
        "methode de paiement",
        "numero de la transaction",
        "carte client",
        "taux tva",
    ]

    stop_contains = [
        "a payer",
        "total eligible",
        "total eligibles",
        "tva ht ttc",
        "taux mont",
        "avec lidl plus",
    ]

    return (
        any(normalized_line.startswith(prefix) for prefix in stop_prefixes)
        or any(keyword in normalized_line for keyword in stop_contains)
    )


def should_ignore_product_name(name: str) -> bool:
    lower_name = normalize_ocr_text(name.lower()).strip()

    ignored = [
        "total",
        "sous total",
        "total tva",
        "dont articles",
        "cb sans contact",
        "tva ht ttc",
        "votre solde",
        "code magasin",
        "no carte",
        "siret",
        "date heure",
        "telephone",
        "tel.",
        "magasin",
        "france",
        "tva",
        "vente",
        "article quantite prix",
        "designation quantite prix",
        "allee de guerledan",
        "methode de paiement",
        "numero de la transaction",
        "carte client",
        "facture",
        "folio",
    ]

    if any(keyword in lower_name for keyword in ignored):
        return True

    if is_quantity_detail_line(name):
        return True

    if is_section_header(name):
        return True

    if len(name.strip()) < 3:
        return True

    return False


def is_tax_line(line: str) -> bool:
    return bool(
        re.match(
            r"^[A-Z]\s+\d+[,.]\d+%\s+\d+[,.]\d{2}\s+\d+[,.]\d{2}\s+\d+[,.]\d{2}",
            line.strip(),
        )
    )


def is_discount_line(line: str) -> bool:
    normalized_line = normalize_ocr_text(line).lower()

    discount_keywords = [
        "reduction",
        "prix en baisse",
        "total promotion",
        "vous avez economise",
        "coupons",
        "offert",
    ]

    return any(keyword in normalized_line for keyword in discount_keywords)


def clean_item_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"^[>\-\*\s]+", "", name)
    name = re.sub(r"\(\d{8,}\)", "", name)
    name = re.sub(r"\s+", " ", name)

    # Remove trailing price if OCR kept it inside the product name
    name = re.sub(r"\s+\d+[,.]\d{2}$", "", name)

    # Remove isolated trailing tax code
    name = re.sub(r"\s+[0-9]$", "", name)

    return name.strip(" -|")


# -------------------------------------------------------------------
# Calculations
# -------------------------------------------------------------------

def fix_item_prices(
    unit_price: float | None,
    quantity: float | None,
    total_price: float | None,
) -> tuple[float | None, float | None]:
    if unit_price is None or quantity is None or total_price is None:
        return unit_price, total_price

    expected_total = round(unit_price * quantity, 2)

    if expected_total == total_price:
        return unit_price, total_price

    if quantity == 1 and unit_price != total_price:
        unit_price = total_price
        return unit_price, total_price

    corrected_unit_price = round(total_price / quantity, 2)

    if corrected_unit_price > 0:
        unit_price = corrected_unit_price

    return unit_price, total_price


def calculate_raw_items_total(items: list[dict]) -> float:
    total = sum(
        item.get("total_price") or 0
        for item in items
    )

    return round(total, 2)


def calculate_category_totals_from_items(items: list[dict]) -> dict[str, float]:
    category_totals: dict[str, float] = {}

    for item in items:
        category = item.get("category") or "other"
        total_price = item.get("total_price") or 0

        category_totals[category] = round(
            category_totals.get(category, 0) + total_price,
            2,
        )

    return category_totals


# -------------------------------------------------------------------
# Generic helpers
# -------------------------------------------------------------------

def get_clean_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def contains_amount(text: str) -> bool:
    return bool(re.search(r"\d+[,.]\d{2}", text))


def parse_amount(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def parse_noisy_amount(value: str | None) -> float | None:
    if value is None:
        return None

    normalized_value = normalize_price_token(value)

    try:
        return float(normalized_value)
    except ValueError:
        return None


def normalize_price_token(value: str) -> str:
    value = value.strip().lower()

    value = (
        value
        .replace("€", "")
        .replace("eur", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    # OCR confusions
    value = value.replace("a", "4")
    value = value.replace("e", "")

    # Keep only digits and decimal point
    value = re.sub(r"[^0-9.]", "", value)

    # OCR often reads 4.64 as 464, 2.49 as 249, 1.95 as 195
    if re.fullmatch(r"\d{3}", value):
        return f"{value[0]}.{value[1:]}"

    if re.fullmatch(r"\d+\.\d{2}", value):
        return value

    return value


def normalize_action_line(line: str) -> str:
    return (
        line.strip()
        .replace("à", "a")
        .replace("À", "A")
        .replace("é", "e")
        .replace("É", "E")
        .replace("è", "e")
        .replace("È", "E")
        .replace("ê", "e")
        .replace("Ê", "E")
        .replace("ç", "c")
        .replace("Ç", "C")
        .replace("’", "'")
        .replace("€E", " eur E")
        .replace("€e", " eur e")
        .replace("€", " eur")
    )


def parse_quantity(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def normalize_ocr_text(text: str) -> str:
    return (
        text
        .replace("@", "0")
        .replace("€", " eur ")
        .replace("à", "a")
        .replace("À", "A")
        .replace("é", "e")
        .replace("É", "E")
        .replace("è", "e")
        .replace("È", "E")
        .replace("ê", "e")
        .replace("Ê", "E")
        .replace("ç", "c")
        .replace("Ç", "C")
        .replace("’", "'")
        .replace("Méthode", "Methode")
        .replace("méthode", "methode")
        .replace("Numéro", "Numero")
        .replace("numéro", "numero")
        .replace("Quantité", "Quantite")
        .replace("quantité", "quantite")
        .replace("montant\n", "montant ")
        .replace("a payer\n", "a payer ")
    )


def remove_trailing_quantity_from_name(name: str) -> str:
    words = name.split()

    if len(words) < 2:
        return name

    last_word = words[-1]

    # Remove only a standalone quantity at the end.
    # Do not remove values inside product sizes like 500g, 3x60ml, 4pcs.
    if re.fullmatch(r"\d+", last_word):
        return " ".join(words[:-1])

    return name


def remove_lidl_tax_code(line: str) -> str:
    """
    Lidl OCR often ends item lines with a tax/VAT code such as:
    Citron 750g 1,85 4
    Fromage blanc nature 1,79 4

    The final 4 is not the item price.
    """

    return re.sub(r"\s+[0-9]\s*$", "", line.strip())


def normalize_lidl_line(line: str) -> str:
    line = line.strip()

    line = (
        line
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
        .replace("’", "'")
    )

    line = re.sub(r"\s+", " ", line)

    # OCR sometimes reads 06,95 instead of 6,95
    line = re.sub(r"\b0(\d,[0-9]{2})\b", r"\1", line)

    # OCR sometimes adds spaces inside prices: -0, 56
    line = re.sub(r"(\d+),\s+(\d{2})", r"\1,\2", line)

    return line


def extract_discount_amount_from_text(text: str) -> float | None:
    normalized_text = normalize_ocr_text(text.lower())

    patterns = [
        r"total promotion\s+(\d+[,.]\d{2})",
        r"vous avez economise\s+(\d+[,.]\d{2})",
        r"reduction lidl plus\s+-?(\d+[,.]\d{2})",
        r"prix en baisse\s+-?(\d+[,.]\d{2})",
    ]

    discounts: list[float] = []

    for pattern in patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE)

        for match in matches:
            amount = parse_amount(match)

            if amount is not None:
                discounts.append(amount)

    if not discounts:
        return None

    if "total promotion" in normalized_text:
        total_promotion_match = re.search(
            r"total promotion\s+(\d+[,.]\d{2})",
            normalized_text,
            re.IGNORECASE,
        )

        if total_promotion_match:
            return parse_amount(total_promotion_match.group(1))

    return round(sum(discounts), 2)