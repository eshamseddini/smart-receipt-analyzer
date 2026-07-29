import logging

from app.db.database import SessionLocal
from app.repositories.receipt_repository import (
    finalize_receipt_processing,
    mark_receipt_processing_failed,
)
from app.services.business_validation_service import validate_extracted_data
from app.services.classification_service import classify_document
from app.services.extraction_service import extract_structured_data
from app.services.integrations_service import send_receipt_webhook
from app.services.ocr.ocr_service import extract_text_from_file

logger = logging.getLogger(__name__)


async def process_receipt_upload(receipt_id: int, dest_path: str) -> None:
    """
    Runs OCR, classification, extraction and validation for a receipt that
    was already saved with processing_status="pending", then fills in the
    result (or records the failure reason).

    Runs as a FastAPI BackgroundTask, after the upload response has already
    been sent — uses its own DB session rather than the request-scoped one,
    since the request's session may already be closed by the time this runs.
    """
    db = SessionLocal()

    try:
        try:
            extracted_text = extract_text_from_file(dest_path)
        except Exception as error:  # noqa: BLE001 -- OCR/PIL/pdf2image raise many distinct error
            # types for a corrupted/unreadable file; a more specific message than the
            # outer catch-all is worth the broad except here.
            logger.warning("OCR failed to read uploaded file %s: %s", dest_path, error)
            mark_receipt_processing_failed(
                db,
                receipt_id,
                "Unable to read this file. It may be corrupted or not a valid image/PDF.",
            )
            return

        document_type = classify_document(extracted_text)

        try:
            structured_data = extract_structured_data(extracted_text, document_type)
        except ValueError as error:
            mark_receipt_processing_failed(db, receipt_id, str(error))
            return

        validation_result = validate_extracted_data(structured_data)

        finalize_receipt_processing(
            db=db,
            receipt_id=receipt_id,
            extracted_text=extracted_text,
            document_type=document_type,
            structured_data=structured_data.model_dump(),
            validation_result=validation_result.model_dump(),
        )

        await send_receipt_webhook(
            event="receipt.processed",
            receipt_id=receipt_id,
            document_type=document_type,
            structured_data=structured_data,
            validation_result=validation_result,
        )
    except Exception:
        logger.exception("Unexpected error while processing receipt %s", receipt_id)
        mark_receipt_processing_failed(
            db, receipt_id, "An unexpected error occurred while processing this receipt."
        )
    finally:
        db.close()
