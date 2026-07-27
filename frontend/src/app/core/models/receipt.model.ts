export interface ReceiptItem {
  name: string;
  unit_price: number | null;
  quantity: number | null;
  total_price: number | null;
  category: string | null;
}

export interface ExtractedReceiptData {
  merchant_name: string | null;
  purchase_date: string | null;
  total_amount: number | null;
  discount_amount: number | null;
  currency: string | null;
  category_totals: Record<string, number>;
  items: ReceiptItem[];
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ReceiptListItem {
  id: number;
  original_filename: string;
  content_type: string;
  saved_path: string;
  document_type: string | null;
  created_at: string;
}

export interface ReceiptDetail extends ReceiptListItem {
  extracted_text: string | null;
  structured_data: ExtractedReceiptData | null;
  validation_result: ValidationResult | null;
}

export interface UploadReceiptResponse {
  receipt_id: number;
  filename: string;
  content_type: string;
  saved_path: string;
  extracted_text: string;
  document_type: string;
  structured_data: ExtractedReceiptData;
  validation_result: ValidationResult;
  message: string;
}

export interface PaginatedReceipts {
  items: ReceiptListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface DeleteReceiptResponse {
  receipt_id: number;
  message: string;
}