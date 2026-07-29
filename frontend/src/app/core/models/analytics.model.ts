export interface AnalyticsSummary {
  total_receipts: number;
  valid_receipts: number;
  invalid_receipts: number;
  unknown_documents: number;
  receipt_documents: number;
  invoice_documents: number;
}

export interface DocumentTypesStats {
  unknown: number;
  receipt: number;
  invoice: number;
}

export interface ValidationStats {
  valid: number;
  invalid: number;
  with_warnings: number;
  without_warnings: number;
}

export interface ChartDataItem {
  label: string;
  value: number;
}

export interface AnalyticsCharts {
  document_types: ChartDataItem[];
  validation_status: ChartDataItem[];
}

export interface MerchantSpendingItem {
  merchant_name: string;
  total_spent: number;
  receipt_count: number;
}

export interface MonthlySpendingItem {
  month: string;
  total_spent: number;
  receipt_count: number;
}

export interface TopProductItem {
  product_name: string;
  total_spent: number;
  quantity: number;
}

export interface CategorySpendingItem {
  category: string;
  total_spent: number;
}

export interface AnalyticsKpis {
  total_spent: number;
  receipt_count: number;
  average_basket: number;
  top_merchant: string | null;
  top_category: string | null;
}

export interface TopProductInsightItem {
  product_name: string;
  category: string | null;
  total_spent: number;
  quantity: number;
}

export interface DataQualityResponse {
  score: number;
  label: string;
  receipt_count: number;
  product_line_count: number;
  category_count: number;
  merchant_count: number;
}

export interface FilterOptionsResponse {
  merchants: string[];
  categories: string[];
}

export interface AnalyticsInsightsResponse {
  kpis: AnalyticsKpis;
  monthly_spending: MonthlySpendingItem[];
  merchant_spending: MerchantSpendingItem[];
  category_spending: CategorySpendingItem[];
  top_products: TopProductInsightItem[];
  data_quality: DataQualityResponse;
  filter_options: FilterOptionsResponse;
}
