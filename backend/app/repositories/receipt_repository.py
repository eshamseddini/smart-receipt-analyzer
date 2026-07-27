from sqlalchemy.orm import Session

from app.models.receipt import Receipt


def create_receipt(
    db: Session,
    original_filename: str,
    content_type: str,
    saved_path: str,
    extracted_text: str,
    document_type: str,
    structured_data: dict,
    validation_result: dict,
) -> Receipt:
    """
    Create a new receipt in the database.
    """
    db_receipt = Receipt(
        original_filename=original_filename,
        content_type=content_type,
        saved_path=saved_path,
        extracted_text=extracted_text,
        document_type=document_type,
        structured_data=structured_data,
        validation_result=validation_result,
    )

    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)

    return db_receipt

def get_receipts(db: Session, skip: int = 0, limit: int = 50):
    """
    Retrieve a paginated list of receipts from the database, most recent first.
    """
    return (
        db.query(Receipt)
        .order_by(Receipt.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

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

def delete_receipt(db: Session, receipt_id: int)-> Receipt | None:
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