from sqlalchemy.orm import Session

from app.models.receipt import Receipt


def create_pending_receipt(
    db: Session,
    original_filename: str,
    content_type: str,
    saved_path: str,
) -> Receipt:
    """
    Create a receipt row immediately after upload, before OCR/extraction has
    run. The background task fills in the rest once processing completes.
    """
    db_receipt = Receipt(
        original_filename=original_filename,
        content_type=content_type,
        saved_path=saved_path,
        processing_status="pending",
    )

    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)

    return db_receipt


def finalize_receipt_processing(
    db: Session,
    receipt_id: int,
    extracted_text: str,
    document_type: str,
    structured_data: dict,
    validation_result: dict,
) -> Receipt | None:
    """
    Fill in a pending receipt with its OCR/extraction results once the
    background processing task completes successfully.
    """
    receipt = get_receipt_by_id(db, receipt_id)

    if not receipt:
        return None

    receipt.extracted_text = extracted_text
    receipt.document_type = document_type
    receipt.structured_data = structured_data
    receipt.validation_result = validation_result
    receipt.processing_status = "completed"
    receipt.error_message = None

    db.commit()
    db.refresh(receipt)

    return receipt


def mark_receipt_processing_failed(
    db: Session,
    receipt_id: int,
    error_message: str,
) -> Receipt | None:
    """
    Record that background processing failed (unsupported merchant,
    corrupted file, ...) so the frontend can show the error to the user.
    """
    receipt = get_receipt_by_id(db, receipt_id)

    if not receipt:
        return None

    receipt.processing_status = "failed"
    receipt.error_message = error_message

    db.commit()
    db.refresh(receipt)

    return receipt


def get_receipts(db: Session, skip: int = 0, limit: int = 50):
    """
    Retrieve a paginated list of receipts from the database, most recent first.
    """
    return db.query(Receipt).order_by(Receipt.created_at.desc()).offset(skip).limit(limit).all()


def count_receipts(db: Session) -> int:
    """
    Count the total number of receipts in the database.
    """
    return db.query(Receipt).count()


def get_receipt_by_id(db: Session, receipt_id: int):
    """
    Retrieve a receipt by its ID from the database.
    """
    return db.query(Receipt).filter(Receipt.id == receipt_id).first()


def delete_receipt(db: Session, receipt_id: int) -> Receipt | None:
    """
    Delete a receipt by its ID from the database.
    """
    receipt = get_receipt_by_id(db, receipt_id)
    if receipt is None:
        return None
    db.delete(receipt)
    db.commit()
    return receipt


def update_receipt_structured_data(
    db: Session,
    receipt_id: int,
    structured_data: dict,
    validation_result: dict,
):
    receipt = get_receipt_by_id(db, receipt_id)

    if not receipt:
        return None

    receipt.structured_data = structured_data
    receipt.validation_result = validation_result

    db.commit()
    db.refresh(receipt)

    return receipt
