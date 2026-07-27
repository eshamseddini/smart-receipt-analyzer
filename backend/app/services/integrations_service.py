import logging

import httpx

from app.core.config import settings
from app.schemas.receipt_schema import ExtractedReceiptData, ValidationResult

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT_SECONDS = 5.0


async def send_receipt_processed_webhook(
    receipt_id: int,
    document_type: str,
    structured_data: ExtractedReceiptData,
    validation_result: ValidationResult,
) -> None:
    """
    Notify an external automation tool (n8n, Make, ...) that a receipt has
    been processed, so it can trigger notifications, spreadsheet syncing,
    or data-quality alerts.

    Failures are logged and swallowed: a broken or unreachable webhook must
    never break the upload flow for the user.
    """
    if not settings.WEBHOOK_ENABLED or not settings.WEBHOOK_URL:
        return

    payload = {
        "event": "receipt.processed",
        "receipt_id": receipt_id,
        "document_type": document_type,
        "structured_data": structured_data.model_dump(),
        "validation": {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
            await client.post(settings.WEBHOOK_URL, json=payload)
    except httpx.HTTPError as error:
        logger.warning("Failed to send receipt.processed webhook: %s", error)
