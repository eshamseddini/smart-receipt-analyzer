from collections import defaultdict
from datetime import date, datetime, timezone

from app.models.receipt import Receipt


def get_merchant_spending(receipts: list[Receipt]) -> list[dict]:
    merchant_data: dict[str, dict] = {}

    for receipt in receipts:
        data = receipt.structured_data or {}

        merchant_name = data.get("merchant_name") or receipt.document_type or "Unknown"
        total_amount = data.get("total_amount") or 0

        if merchant_name not in merchant_data:
            merchant_data[merchant_name] = {
                "merchant_name": merchant_name,
                "total_spent": 0,
                "receipt_count": 0,
            }

        merchant_data[merchant_name]["total_spent"] += total_amount
        merchant_data[merchant_name]["receipt_count"] += 1

    result = list(merchant_data.values())

    for item in result:
        item["total_spent"] = round(item["total_spent"], 2)

    return sorted(result, key=lambda item: item["total_spent"], reverse=True)


def get_monthly_spending(receipts: list[Receipt]) -> list[dict]:
    monthly_data: dict[str, dict] = {}

    for receipt in receipts:
        data = receipt.structured_data or {}
        total_amount = data.get("total_amount") or 0

        month = extract_month(data, receipt)

        if month not in monthly_data:
            monthly_data[month] = {
                "month": month,
                "total_spent": 0,
                "receipt_count": 0,
            }

        monthly_data[month]["total_spent"] += total_amount
        monthly_data[month]["receipt_count"] += 1

    result = list(monthly_data.values())

    for item in result:
        item["total_spent"] = round(item["total_spent"], 2)

    return sorted(result, key=lambda item: item["month"])


def get_top_products(receipts: list[Receipt], limit: int = 10) -> list[dict]:
    product_data: dict[str, dict] = {}

    for receipt in receipts:
        data = receipt.structured_data or {}
        items = data.get("items") or []

        for item in items:
            product_name = item.get("name") or "Unknown product"
            total_price = item.get("total_price") or 0
            quantity = item.get("quantity") or 1

            normalized_name = product_name.strip().lower()

            if normalized_name not in product_data:
                product_data[normalized_name] = {
                    "product_name": product_name,
                    "total_spent": 0,
                    "quantity": 0,
                }

            product_data[normalized_name]["total_spent"] += total_price
            product_data[normalized_name]["quantity"] += quantity

    result = list(product_data.values())

    for item in result:
        item["total_spent"] = round(item["total_spent"], 2)
        item["quantity"] = round(item["quantity"], 2)

    return sorted(result, key=lambda item: item["total_spent"], reverse=True)[:limit]


def get_category_spending(receipts: list[Receipt]) -> list[dict]:
    category_data: defaultdict[str, float] = defaultdict(float)

    for receipt in receipts:
        data = receipt.structured_data or {}
        items = data.get("items") or []

        for item in items:
            category = item.get("category") or "other"
            total_price = item.get("total_price") or 0

            category_data[category] += total_price

    result = [
        {
            "category": category,
            "total_spent": round(total_spent, 2),
        }
        for category, total_spent in category_data.items()
    ]

    return sorted(result, key=lambda item: item["total_spent"], reverse=True)


def extract_month(data: dict, receipt: Receipt) -> str:
    purchase_date = data.get("purchase_date")

    if purchase_date:
        try:
            parsed_date = datetime.fromisoformat(purchase_date)
            return parsed_date.strftime("%Y-%m")
        except ValueError:
            pass

    return receipt.created_at.strftime("%Y-%m")


def build_analytics_insights(
    receipts: list[Receipt],
    period: str = "all",
    date_from: str | None = None,
    date_to: str | None = None,
    merchant: str | None = None,
    category: str | None = None,
) -> dict:
    filtered_receipts = filter_receipts(
        receipts=receipts,
        period=period,
        date_from=date_from,
        date_to=date_to,
        merchant=merchant,
    )

    merchant_spending = build_merchant_spending(filtered_receipts)
    monthly_spending = build_monthly_spending(filtered_receipts)
    category_spending = build_category_spending(filtered_receipts, category)
    top_products = build_top_products(filtered_receipts, category, limit=15)

    total_spent = round(sum(item["total_spent"] for item in merchant_spending), 2)

    receipt_count = sum(item["receipt_count"] for item in merchant_spending)

    average_basket = round(total_spent / receipt_count, 2) if receipt_count else 0

    top_merchant = merchant_spending[0]["merchant_name"] if merchant_spending else None

    top_category = category_spending[0]["category"] if category_spending else None

    return {
        "kpis": {
            "total_spent": total_spent,
            "receipt_count": receipt_count,
            "average_basket": average_basket,
            "top_merchant": top_merchant,
            "top_category": top_category,
        },
        "monthly_spending": monthly_spending,
        "merchant_spending": merchant_spending,
        "category_spending": category_spending,
        "top_products": top_products,
        "data_quality": build_data_quality(
            receipts=filtered_receipts,
            merchant_spending=merchant_spending,
            category_spending=category_spending,
            top_products=top_products,
        ),
        "filter_options": build_filter_options(receipts),
    }


def filter_receipts(
    receipts: list[Receipt],
    period: str,
    date_from: str | None,
    date_to: str | None,
    merchant: str | None,
) -> list[Receipt]:
    today = datetime.now(timezone.utc).date()

    start_date: date | None = None
    end_date: date | None = None

    if period == "today":
        start_date = today
        end_date = today

    elif period == "this_month":
        start_date = today.replace(day=1)
        end_date = today

    elif period == "custom":
        if date_from:
            start_date = datetime.fromisoformat(date_from).date()

        if date_to:
            end_date = datetime.fromisoformat(date_to).date()

    filtered: list[Receipt] = []

    for receipt in receipts:
        data = receipt.structured_data or {}
        receipt_date = get_receipt_date(data, receipt)

        if start_date and receipt_date < start_date:
            continue

        if end_date and receipt_date > end_date:
            continue

        if merchant:
            receipt_merchant = data.get("merchant_name") or "Unknown"

            if receipt_merchant.lower() != merchant.lower():
                continue

        filtered.append(receipt)

    return filtered


def get_receipt_date(data: dict, receipt: Receipt) -> date:
    purchase_date = data.get("purchase_date")

    if purchase_date:
        try:
            return datetime.fromisoformat(purchase_date).date()
        except ValueError:
            pass

    return receipt.created_at.date()


def build_merchant_spending(receipts: list[Receipt]) -> list[dict]:
    merchant_data: dict[str, dict] = {}

    for receipt in receipts:
        data = receipt.structured_data or {}

        merchant_name = data.get("merchant_name") or "Unknown"
        total_amount = data.get("total_amount") or 0

        if merchant_name not in merchant_data:
            merchant_data[merchant_name] = {
                "merchant_name": merchant_name,
                "total_spent": 0,
                "receipt_count": 0,
            }

        merchant_data[merchant_name]["total_spent"] += total_amount
        merchant_data[merchant_name]["receipt_count"] += 1

    result = list(merchant_data.values())

    for item in result:
        item["total_spent"] = round(item["total_spent"], 2)

    return sorted(result, key=lambda item: item["total_spent"], reverse=True)


def build_monthly_spending(receipts: list[Receipt]) -> list[dict]:
    monthly_data: dict[str, dict] = {}

    for receipt in receipts:
        data = receipt.structured_data or {}
        total_amount = data.get("total_amount") or 0

        receipt_date = get_receipt_date(data, receipt)
        month = receipt_date.strftime("%Y-%m")

        if month not in monthly_data:
            monthly_data[month] = {
                "month": month,
                "total_spent": 0,
                "receipt_count": 0,
            }

        monthly_data[month]["total_spent"] += total_amount
        monthly_data[month]["receipt_count"] += 1

    result = list(monthly_data.values())

    for item in result:
        item["total_spent"] = round(item["total_spent"], 2)

    return sorted(result, key=lambda item: item["month"])


def build_category_spending(
    receipts: list[Receipt],
    selected_category: str | None = None,
) -> list[dict]:
    category_data: defaultdict[str, float] = defaultdict(float)

    for receipt in receipts:
        data = receipt.structured_data or {}
        items = data.get("items") or []

        for item in items:
            item_category = item.get("category") or "other"

            if selected_category and item_category != selected_category:
                continue

            total_price = item.get("total_price") or 0
            category_data[item_category] += total_price

    result = [
        {
            "category": item_category,
            "total_spent": round(total_spent, 2),
        }
        for item_category, total_spent in category_data.items()
    ]

    return sorted(result, key=lambda item: item["total_spent"], reverse=True)


def build_top_products(
    receipts: list[Receipt],
    selected_category: str | None = None,
    limit: int = 15,
) -> list[dict]:
    product_data: dict[str, dict] = {}

    for receipt in receipts:
        data = receipt.structured_data or {}
        items = data.get("items") or []

        for item in items:
            item_category = item.get("category") or "other"

            if selected_category and item_category != selected_category:
                continue

            product_name = item.get("name") or "Unknown product"
            total_price = item.get("total_price") or 0
            quantity = item.get("quantity") or 1

            normalized_name = product_name.strip().lower()

            if normalized_name not in product_data:
                product_data[normalized_name] = {
                    "product_name": product_name,
                    "category": item_category,
                    "total_spent": 0,
                    "quantity": 0,
                }

            product_data[normalized_name]["total_spent"] += total_price
            product_data[normalized_name]["quantity"] += quantity

    result = list(product_data.values())

    for item in result:
        item["total_spent"] = round(item["total_spent"], 2)
        item["quantity"] = round(item["quantity"], 2)

    return sorted(result, key=lambda item: item["total_spent"], reverse=True)[:limit]


def build_data_quality(
    receipts: list[Receipt],
    merchant_spending: list[dict],
    category_spending: list[dict],
    top_products: list[dict],
) -> dict:
    receipt_count = len(receipts)
    product_line_count = sum(
        len((receipt.structured_data or {}).get("items") or []) for receipt in receipts
    )

    category_count = len(category_spending)
    merchant_count = len(merchant_spending)

    if receipt_count == 0:
        score = 0
    else:
        score = 55

        if product_line_count > 0:
            score += 15

        if category_count > 0:
            score += 10

        if merchant_count > 0:
            score += 10

        if top_products:
            score += 10

        score = min(score, 100)

    if score >= 90:
        label = "Excellent"
    elif score >= 75:
        label = "Good"
    elif score >= 60:
        label = "Needs review"
    else:
        label = "Poor"

    return {
        "score": score,
        "label": label,
        "receipt_count": receipt_count,
        "product_line_count": product_line_count,
        "category_count": category_count,
        "merchant_count": merchant_count,
    }


def build_filter_options(receipts: list[Receipt]) -> dict:
    merchants: set[str] = set()
    categories: set[str] = set()

    for receipt in receipts:
        data = receipt.structured_data or {}

        merchant_name = data.get("merchant_name")
        if merchant_name:
            merchants.add(merchant_name)

        items = data.get("items") or []
        for item in items:
            category = item.get("category") or "other"
            categories.add(category)

    return {
        "merchants": sorted(merchants),
        "categories": sorted(categories),
    }
