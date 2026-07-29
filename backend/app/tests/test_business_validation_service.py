from app.schemas.receipt_schema import ExtractedReceiptData
from app.services.business_validation_service import validate_extracted_data


def test_donnees_valides():
    structured_data = ExtractedReceiptData(
        merchant_name="Test Merchant",
        purchase_date="2026-07-15",
        total_amount=100.0,
        currency="EUR",
        items=[
            {
                "name": "Item 1",
                "unit_price": 50.0,
                "quantity": 1,
                "total_price": 50.0,
                "category": "other",
            },
            {
                "name": "Item 2",
                "unit_price": 50.0,
                "quantity": 1,
                "total_price": 50.0,
                "category": "other",
            },
        ],
    )

    result = validate_extracted_data(structured_data)

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []


def test_total_amount_missing():
    structured_data = ExtractedReceiptData(
        merchant_name="Test Merchant",
        purchase_date="2026-07-15",
        total_amount=None,
        currency="EUR",
        items=[
            {
                "name": "Item 1",
                "unit_price": 50.0,
                "quantity": 1,
                "total_price": 50.0,
                "category": "other",
            }
        ],
    )

    result = validate_extracted_data(structured_data)

    assert result.is_valid is False
    assert "Total amount is missing." in result.errors


def test_items_vide():
    structured_data = ExtractedReceiptData(
        merchant_name="Test Merchant",
        purchase_date="2026-07-15",
        total_amount=100.0,
        currency="EUR",
        items=[],
    )

    result = validate_extracted_data(structured_data)

    assert result.is_valid is True
    assert result.errors == []
    assert "No receipt items were extracted." in result.warnings


def test_total_amount_negatif():
    structured_data = ExtractedReceiptData(
        merchant_name="Test Merchant",
        purchase_date="2026-07-15",
        total_amount=-50.0,
        currency="EUR",
        items=[
            {
                "name": "Item 1",
                "unit_price": -50.0,
                "quantity": 1,
                "total_price": -50.0,
                "category": "other",
            }
        ],
    )

    result = validate_extracted_data(structured_data)

    assert result.is_valid is False
    assert "Total amount cannot be negative." in result.errors


def test_currency_missing():
    structured_data = ExtractedReceiptData(
        merchant_name="Test Merchant",
        purchase_date="2026-07-15",
        total_amount=100.0,
        currency=None,
        items=[
            {
                "name": "Item 1",
                "unit_price": 100.0,
                "quantity": 1,
                "total_price": 100.0,
                "category": "other",
            }
        ],
    )

    result = validate_extracted_data(structured_data)

    assert result.is_valid is False
    assert "Currency is missing." in result.errors


def test_purchase_date_missing_is_warning_only():
    structured_data = ExtractedReceiptData(
        merchant_name="Test Merchant",
        purchase_date=None,
        total_amount=100.0,
        currency="EUR",
        items=[
            {
                "name": "Item 1",
                "unit_price": 100.0,
                "quantity": 1,
                "total_price": 100.0,
                "category": "other",
            }
        ],
    )

    result = validate_extracted_data(structured_data)

    assert result.is_valid is True
    assert result.errors == []
    assert "Purchase date is missing." in result.warnings
