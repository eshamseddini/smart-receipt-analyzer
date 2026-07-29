from pydantic import BaseModel

from app.schemas.receipt_schema import ExtractedReceiptData, ValidationResult


class UploadReceiptResponse(BaseModel):
    """
    Response model for the upload receipt endpoint.
    """

    receipt_id: int
    filename: str
    content_type: str
    saved_path: str
    extracted_text: str
    document_type: str | None
    structured_data: ExtractedReceiptData
    validation_result: ValidationResult
    message: str
