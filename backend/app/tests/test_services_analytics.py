from datetime import datetime, timezone

from app.services.analytics_service import (
    build_category_spending,
    build_data_quality,
    build_filter_options,
    build_merchant_spending,
    build_monthly_spending,
    build_top_products,
)


class FakeReceipt:
    def __init__(self, structured_data: dict, created_at: datetime | None = None):
        self.structured_data = structured_data
        self.created_at = created_at or datetime(2026, 7, 15, tzinfo=timezone.utc)


def test_build_merchant_spending_groups_by_merchant():
    receipts = [
        FakeReceipt(
            {
                "merchant_name": "LIDL",
                "total_amount": 20.0,
                "items": [],
            }
        ),
        FakeReceipt(
            {
                "merchant_name": "LIDL",
                "total_amount": 10.0,
                "items": [],
            }
        ),
        FakeReceipt(
            {
                "merchant_name": "ACTION",
                "total_amount": 15.0,
                "items": [],
            }
        ),
    ]

    result = build_merchant_spending(receipts)

    assert result[0]["merchant_name"] == "LIDL"
    assert result[0]["total_spent"] == 30.0
    assert result[0]["receipt_count"] == 2

    assert result[1]["merchant_name"] == "ACTION"
    assert result[1]["total_spent"] == 15.0
    assert result[1]["receipt_count"] == 1


def test_build_monthly_spending_groups_by_month():
    receipts = [
        FakeReceipt(
            {
                "purchase_date": "2026-07-10",
                "total_amount": 20.0,
                "items": [],
            }
        ),
        FakeReceipt(
            {
                "purchase_date": "2026-07-12",
                "total_amount": 15.0,
                "items": [],
            }
        ),
        FakeReceipt(
            {
                "purchase_date": "2026-08-01",
                "total_amount": 30.0,
                "items": [],
            }
        ),
    ]

    result = build_monthly_spending(receipts)

    assert result == [
        {
            "month": "2026-07",
            "total_spent": 35.0,
            "receipt_count": 2,
        },
        {
            "month": "2026-08",
            "total_spent": 30.0,
            "receipt_count": 1,
        },
    ]


def test_build_category_spending_groups_product_lines():
    receipts = [
        FakeReceipt(
            {
                "items": [
                    {"name": "Milk", "category": "dairy", "total_price": 2.5},
                    {"name": "Cheese", "category": "dairy", "total_price": 3.5},
                    {"name": "Apple", "category": "fruit", "total_price": 4.0},
                ]
            }
        )
    ]

    result = build_category_spending(receipts)

    assert result[0]["category"] == "dairy"
    assert result[0]["total_spent"] == 6.0

    assert result[1]["category"] == "fruit"
    assert result[1]["total_spent"] == 4.0


def test_build_category_spending_can_filter_selected_category():
    receipts = [
        FakeReceipt(
            {
                "items": [
                    {"name": "Milk", "category": "dairy", "total_price": 2.5},
                    {"name": "Apple", "category": "fruit", "total_price": 4.0},
                ]
            }
        )
    ]

    result = build_category_spending(receipts, selected_category="fruit")

    assert result == [
        {
            "category": "fruit",
            "total_spent": 4.0,
        }
    ]


def test_build_top_products_groups_same_product_name():
    receipts = [
        FakeReceipt(
            {
                "items": [
                    {
                        "name": "Milk",
                        "category": "dairy",
                        "quantity": 1,
                        "total_price": 2.5,
                    },
                    {
                        "name": "milk",
                        "category": "dairy",
                        "quantity": 2,
                        "total_price": 5.0,
                    },
                    {
                        "name": "Apple",
                        "category": "fruit",
                        "quantity": 1,
                        "total_price": 4.0,
                    },
                ]
            }
        )
    ]

    result = build_top_products(receipts)

    assert result[0]["product_name"] == "Milk"
    assert result[0]["category"] == "dairy"
    assert result[0]["quantity"] == 3
    assert result[0]["total_spent"] == 7.5


def test_build_filter_options_returns_unique_sorted_values():
    receipts = [
        FakeReceipt(
            {
                "merchant_name": "LIDL",
                "items": [
                    {"category": "dairy"},
                    {"category": "fruit"},
                ],
            }
        ),
        FakeReceipt(
            {
                "merchant_name": "ACTION",
                "items": [
                    {"category": "household"},
                    {"category": "dairy"},
                ],
            }
        ),
    ]

    result = build_filter_options(receipts)

    assert result == {
        "merchants": ["ACTION", "LIDL"],
        "categories": ["dairy", "fruit", "household"],
    }


def test_build_data_quality_returns_score_and_counts():
    receipts = [
        FakeReceipt(
            {
                "items": [
                    {"name": "Milk", "category": "dairy", "total_price": 2.5},
                    {"name": "Apple", "category": "fruit", "total_price": 4.0},
                ]
            }
        )
    ]

    merchant_spending = [
        {
            "merchant_name": "LIDL",
            "total_spent": 6.5,
            "receipt_count": 1,
        }
    ]

    category_spending = [
        {
            "category": "dairy",
            "total_spent": 2.5,
        },
        {
            "category": "fruit",
            "total_spent": 4.0,
        },
    ]

    top_products = [
        {
            "product_name": "Apple",
            "category": "fruit",
            "total_spent": 4.0,
            "quantity": 1,
        }
    ]

    result = build_data_quality(
        receipts=receipts,
        merchant_spending=merchant_spending,
        category_spending=category_spending,
        top_products=top_products,
    )

    assert result["score"] == 100
    assert result["label"] == "Excellent"
    assert result["receipt_count"] == 1
    assert result["product_line_count"] == 2
    assert result["category_count"] == 2
    assert result["merchant_count"] == 1
