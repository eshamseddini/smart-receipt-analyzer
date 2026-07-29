from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    total_receipts: int
    valid_receipts: int
    invalid_receipts: int
    unknown_documents: int
    receipt_documents: int
    invoice_documents: int


class DocumentTypesStatsResponse(BaseModel):
    unknown: int
    receipt: int
    invoice: int


class ValidationStatsResponse(BaseModel):
    valid: int
    invalid: int
    with_warnings: int
    without_warnings: int


class ChartDataItem(BaseModel):
    label: str
    value: int


class AnalyticsChartsResponse(BaseModel):
    document_types: list[ChartDataItem]
    validation_status: list[ChartDataItem]


class MerchantSpendingItem(BaseModel):
    merchant_name: str
    total_spent: float
    receipt_count: int


class MonthlySpendingItem(BaseModel):
    month: str
    total_spent: float
    receipt_count: int


class TopProductItem(BaseModel):
    product_name: str
    total_spent: float
    quantity: float


class CategorySpendingItem(BaseModel):
    category: str
    total_spent: float


class AnalyticsKpis(BaseModel):
    total_spent: float
    receipt_count: int
    average_basket: float
    top_merchant: str | None
    top_category: str | None


class TopProductInsightItem(BaseModel):
    product_name: str
    category: str | None
    total_spent: float
    quantity: float


class DataQualityResponse(BaseModel):
    score: int
    label: str
    receipt_count: int
    product_line_count: int
    category_count: int
    merchant_count: int


class FilterOptionsResponse(BaseModel):
    merchants: list[str]
    categories: list[str]


class AnalyticsInsightsResponse(BaseModel):
    kpis: AnalyticsKpis
    monthly_spending: list[MonthlySpendingItem]
    merchant_spending: list[MerchantSpendingItem]
    category_spending: list[CategorySpendingItem]
    top_products: list[TopProductInsightItem]
    data_quality: DataQualityResponse
    filter_options: FilterOptionsResponse
