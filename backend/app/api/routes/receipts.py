from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.repositories.receipt_repository import create_receipt, delete_receipt, get_receipt_by_id, get_receipts, count_receipts, update_receipt_structured_data

from app.services.file_service import delete_local_file, save_uploaded_file
from app.schemas.upload_schema import UploadReceiptResponse
from app.services.validation_service import validate_uploaded_file, validate_file_size
from app.services.ocr.ocr_service import extract_text_from_file
from app.services.classification_service import classify_document
from app.services.extraction_service import extract_structured_data, calculate_category_totals_from_items
from app.services.business_validation_service import validate_extracted_data
from app.services.integrations_service import send_receipt_webhook
from app.schemas.receipt_schema import DeleteReceiptResponse, PaginatedReceiptsResponse, ReceiptDetail, ReceiptListItem, UpdateReceiptStructuredDataRequest

router = APIRouter()
@router.post("/upload", response_model=UploadReceiptResponse)
async def upload_receipt(file : UploadFile = File(...), db: Session = Depends(get_db)) -> UploadReceiptResponse:
    validate_uploaded_file(file)
    contents = await file.read()
    validate_file_size(contents)
    dest_path = await save_uploaded_file(file, contents)
    extracted_text = extract_text_from_file(dest_path)
    document_type = classify_document(extracted_text)
    try:
        structured_data = extract_structured_data(extracted_text, document_type)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(error),
                "filename": file.filename,
                "document_type": document_type,
                "extracted_text_preview": extracted_text[:500],
            },
        ) from error

    validation_result = validate_extracted_data(structured_data)
    created_receipt = create_receipt(
        db=db,
        original_filename=file.filename,
        content_type=file.content_type,
        saved_path=dest_path,
        extracted_text=extracted_text,
        document_type=document_type,
        structured_data=structured_data.model_dump(),
        validation_result=validation_result.model_dump()
    )

    await send_receipt_webhook(
        event="receipt.processed",
        receipt_id=created_receipt.id,
        document_type=document_type,
        structured_data=structured_data,
        validation_result=validation_result,
    )

    return UploadReceiptResponse(
        receipt_id=created_receipt.id,
        filename=file.filename,
        content_type=file.content_type,
        saved_path=dest_path,
        extracted_text=extracted_text,
        document_type=document_type,
        structured_data=structured_data,
        validation_result=validation_result,
        message="File uploaded, processed, structured, validated and saved successfully.",
    )

@router.get("/", response_model=PaginatedReceiptsResponse)
def list_receipts(db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """
    Retrieve a paginated list of receipts from the database.
    """
    receipts = get_receipts(db, skip=skip, limit=limit)
    total = count_receipts(db)
    return PaginatedReceiptsResponse(items=receipts, total=total, skip=skip, limit=limit)

@router.get("/{receipt_id}", response_model=ReceiptDetail)
def get_receipt_detail(receipt_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a receipt by its ID from the database.
    """
    receipt = get_receipt_by_id(db, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

@router.delete("/{receipt_id}", response_model=DeleteReceiptResponse)
def delete_receipt_by_id(receipt_id: int, db: Session = Depends(get_db)):
    """
    Delete a receipt by its ID from the database.
    """
    deleted_receipt = delete_receipt(db, receipt_id)
    if not deleted_receipt:
        raise HTTPException(status_code=404, detail="Receipt not found.")
    delete_local_file(deleted_receipt.saved_path)
    return DeleteReceiptResponse(
        receipt_id=receipt_id,
        message="Receipt deleted successfully"
    )

@router.patch("/{receipt_id}/structured-data", response_model=ReceiptDetail)
async def update_structured_data(
    receipt_id: int,
    payload: UpdateReceiptStructuredDataRequest,
    db: Session = Depends(get_db),
):
    corrected_data = payload.structured_data

    corrected_data.category_totals = calculate_category_totals_from_items(
        [item.model_dump() for item in corrected_data.items]
    )

    validation_result = validate_extracted_data(corrected_data)

    updated_receipt = update_receipt_structured_data(
        db=db,
        receipt_id=receipt_id,
        structured_data=corrected_data.model_dump(),
        validation_result=validation_result.model_dump(),
    )

    if not updated_receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    await send_receipt_webhook(
        event="receipt.updated",
        receipt_id=updated_receipt.id,
        document_type=updated_receipt.document_type,
        structured_data=corrected_data,
        validation_result=validation_result,
    )

    return updated_receipt