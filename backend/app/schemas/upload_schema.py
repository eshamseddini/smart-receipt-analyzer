from pydantic import BaseModel


class UploadAcceptedResponse(BaseModel):
    """
    Response model for the upload receipt endpoint.

    Processing (OCR, extraction, validation) happens in the background —
    poll GET /api/receipts/{receipt_id} until processing_status is no
    longer "pending" to get the final result.
    """

    receipt_id: int
    filename: str
    processing_status: str
    message: str
