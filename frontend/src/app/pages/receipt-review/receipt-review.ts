import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnInit,
  QueryList,
  ViewChildren,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ExtractedReceiptData, ReceiptDetail, ReceiptItem } from '../../core/models/receipt.model';
import { ReceiptService } from '../../core/services/receipt.service';
import { PageState } from '../../shared/components/page-state/page-state';
import { API_BASE_URL } from '../../core/constants/api.constants';

@Component({
  selector: 'app-receipt-review',
  imports: [FormsModule, DecimalPipe, RouterLink, PageState],
  templateUrl: './receipt-review.html',
  styleUrl: './receipt-review.css',
})
export class ReceiptReview implements OnInit {
  @ViewChildren('itemRow') itemRows!: QueryList<ElementRef<HTMLElement>>;

  receipt: ReceiptDetail | null = null;
  editableData: ExtractedReceiptData | null = null;

  loading = false;
  saving = false;
  errorMessage = '';
  successMessage = '';

  zoomLevel = 1;
  fitToWidth = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private receiptService: ReceiptService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');

    if (!idParam) {
      this.errorMessage = 'Receipt id is missing.';
      return;
    }

    const id = Number(idParam);

    if (Number.isNaN(id)) {
      this.errorMessage = 'Receipt id is invalid.';
      return;
    }

    this.loadReceipt(id);
  }

  loadReceipt(id: number): void {
    this.loading = true;
    this.errorMessage = '';

    this.receiptService.getReceiptById(id).subscribe({
      next: (data) => {
        this.receipt = data;
        this.editableData = structuredClone(data.structured_data);
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errorMessage = 'Unable to load receipt.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  addItem(): void {
    if (!this.editableData) return;

    this.editableData.items.push({
      name: '',
      unit_price: 0,
      quantity: 1,
      total_price: 0,
      category: 'other',
    });

    setTimeout(() => this.scrollToLastItem());
  }

  private scrollToLastItem(): void {
    const rows = this.itemRows?.toArray();
    const lastRow = rows?.[rows.length - 1];

    lastRow?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  removeItem(index: number): void {
    if (!this.editableData) return;

    this.editableData.items.splice(index, 1);
    this.recalculateTotals();
  }

  recalculateItemTotal(item: ReceiptItem): void {
    const unitPrice = Number(item.unit_price || 0);
    const quantity = Number(item.quantity || 0);

    item.total_price = Number((unitPrice * quantity).toFixed(2));

    this.recalculateTotals();
  }

  recalculateTotals(): void {
    if (!this.editableData) return;

    const categoryTotals: Record<string, number> = {};

    for (const item of this.editableData.items) {
      const category = item.category || 'other';
      const total = Number(item.total_price || 0);

      categoryTotals[category] = Number(((categoryTotals[category] || 0) + total).toFixed(2));
    }

    this.editableData.category_totals = categoryTotals;
  }

  get itemsTotal(): number {
    if (!this.editableData) return 0;

    return this.editableData.items.reduce(
      (total, item) => total + Number(item.total_price || 0),
      0,
    );
  }

  get expectedTotal(): number {
    if (!this.editableData) return 0;

    const paid = Number(this.editableData.total_amount || 0);
    const discount = Number(this.editableData.discount_amount || 0);

    return paid + discount;
  }

  get difference(): number {
    return Number(Math.abs(this.itemsTotal - this.expectedTotal).toFixed(2));
  }

  saveCorrections(): void {
    if (!this.receipt || !this.editableData) return;

    this.saving = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.recalculateTotals();

    this.receiptService.updateStructuredData(this.receipt.id, this.editableData).subscribe({
      next: (updatedReceipt) => {
        this.receipt = updatedReceipt;
        this.editableData = structuredClone(updatedReceipt.structured_data);
        this.successMessage = 'Corrections saved successfully.';
        this.saving = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errorMessage = 'Unable to save corrections.';
        this.saving = false;
        this.cdr.detectChanges();
      },
    });
  }

  saveAndReturn(): void {
    if (!this.receipt || !this.editableData) return;

    this.saving = true;
    this.errorMessage = '';

    this.recalculateTotals();

    this.receiptService.updateStructuredData(this.receipt.id, this.editableData).subscribe({
      next: () => {
        this.router.navigate(['/receipts', this.receipt?.id]);
      },
      error: () => {
        this.errorMessage = 'Unable to save corrections.';
        this.saving = false;
        this.cdr.detectChanges();
      },
    });
  }

  get receiptImageUrl(): string {
    if (!this.receipt?.saved_path) return '';

    return `${API_BASE_URL}/${this.receipt.saved_path}`;
  }

  zoomIn(): void {
    this.fitToWidth = false;
    this.zoomLevel = Math.min(this.zoomLevel + 0.15, 2.5);
  }

  zoomOut(): void {
    this.fitToWidth = false;
    this.zoomLevel = Math.max(this.zoomLevel - 0.15, 0.5);
  }

  resetZoom(): void {
    this.fitToWidth = true;
    this.zoomLevel = 1;
  }

  get imageZoomStyle(): string {
    if (this.fitToWidth) {
      return '100%';
    }
    return `${this.zoomLevel * 100}%`;
  }
}
