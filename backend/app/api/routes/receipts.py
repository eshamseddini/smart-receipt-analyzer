import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.receipt_repository import (
    count_receipts,
    create_pending_receipt,
    delete_receipt,
    get_receipt_by_id,
    get_receipts,
    update_receipt_structured_data,
)
from app.schemas.receipt_schema import (
    DeleteReceiptResponse,
    PaginatedReceiptsResponse,
    ReceiptDetail,
    UpdateReceiptStructuredDataRequest,
)
from app.schemas.upload_schema import UploadAcceptedResponse
from app.services.business_validation_service import validate_extracted_data
from app.services.extraction_service import calculate_category_totals_from_items
from app.services.file_service import delete_local_file, save_uploaded_file
from app.services.integrations_service import send_receipt_webhook
from app.services.receipt_processing_service import process_receipt_upload
from app.services.validation_service import validate_file_size, validate_uploaded_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadAcceptedResponse, status_code=202)
async def upload_receipt(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadAcceptedResponse:
    """
    Validates and saves the file, then returns immediately with a "pending"
    status. OCR/extraction/validation run in the background — poll
    GET /api/receipts/{receipt_id} to get the final result.

    Processing is not done inline because OCR is CPU-heavy: on constrained
    hosting (e.g. a free-tier instance) it can take far longer than a
    reverse proxy's gateway timeout, which would otherwise turn a slow but
    successful upload into a client-facing 502/504.
    """
    validate_uploaded_file(file)
    contents = await file.read()
    validate_file_size(contents)
    dest_path = save_uploaded_file(file, contents)

    created_receipt = create_pending_receipt(
        db=db,
        original_filename=file.filename,
        content_type=file.content_type,
        saved_path=dest_path,
    )

    background_tasks.add_task(process_receipt_upload, created_receipt.id, dest_path)

    return UploadAcceptedResponse(
        receipt_id=created_receipt.id,
        filename=file.filename,
        processing_status=created_receipt.processing_status,
        message="File uploaded successfully. Processing in the background.",
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
    return DeleteReceiptResponse(receipt_id=receipt_id, message="Receipt deleted successfully")


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
