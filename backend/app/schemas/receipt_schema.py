from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class ReceiptItem(BaseModel):
    name: str
    unit_price: float | None = None
    quantity: float | None = None
    total_price: float | None = None
    category: str | None = None

class ExtractedReceiptData(BaseModel):
    merchant_name: str | None = None
    purchase_date: str | None = None
    total_amount: float | None = None
    discount_amount: float | None = None
    currency: str | None = "EUR"
    category_totals: dict[str, float] = Field(default_factory=dict)
    items: list[ReceiptItem] = Field(default_factory=list)

class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class ReceiptListItem(BaseModel):
    id: int
    original_filename: str
    content_type: str
    saved_path: str
    document_type: str | None 
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode for SQLAlchemy models

class ReceiptDetail(ReceiptListItem):
    extracted_text: str | None
    structured_data: ExtractedReceiptData | None   
    validation_result: ValidationResult | None

class PaginatedReceiptsResponse(BaseModel):
    items: list[ReceiptListItem]
    total: int
    skip: int
    limit: int

class DeleteReceiptResponse(BaseModel):
    receipt_id: int
    message: str

class UpdateReceiptStructuredDataRequest(BaseModel):
    structured_data: ExtractedReceiptData