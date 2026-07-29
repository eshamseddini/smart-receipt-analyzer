from app.schemas.receipt_schema import ExtractedReceiptData, ValidationResult

SUPPORTED_CURRENCIES = {"EUR", "USD", "GBP"}


def validate_extracted_data(data: ExtractedReceiptData) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not data.merchant_name:
        errors.append("Merchant name is missing.")

    if not data.purchase_date:
        warnings.append("Purchase date is missing.")

    if data.total_amount is None:
        errors.append("Total amount is missing.")
    elif data.total_amount < 0:
        errors.append("Total amount cannot be negative.")

    if not data.currency:
        errors.append("Currency is missing.")
    elif data.currency not in SUPPORTED_CURRENCIES:
        errors.append(f"Unsupported currency: {data.currency}.")

    if not data.items:
        warnings.append("No receipt items were extracted.")

    validate_items_total(data, warnings)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_items_total(data: ExtractedReceiptData, warnings: list[str]) -> None:
    if data.total_amount is None or data.total_amount < 0 or not data.items:
        return

    items_total = round(
        sum(item.total_price or 0 for item in data.items),
        2,
    )

    expected_total = data.total_amount

    if data.discount_amount:
        expected_total = round(data.total_amount + data.discount_amount, 2)

    difference = round(abs(items_total - expected_total), 2)

    if difference <= 0.05:
        return

    warnings.append(
        f"Items total ({items_total}) does not match expected total ({expected_total}). "
        f"Difference: {difference}."
    )
