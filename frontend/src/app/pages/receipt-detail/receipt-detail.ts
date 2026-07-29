import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { DatePipe, JsonPipe, DecimalPipe } from '@angular/common';
import { finalize } from 'rxjs';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ReceiptService } from '../../core/services/receipt.service';
import { ReceiptDetail as ReceiptDetailModel } from '../../core/models/receipt.model';
import { PageState } from '../../shared/components/page-state/page-state';

@Component({
  selector: 'app-receipt-detail',
  imports: [DatePipe, JsonPipe, RouterLink, PageState, DecimalPipe],
  templateUrl: './receipt-detail.html',
  styleUrl: './receipt-detail.css',
})
export class ReceiptDetailComponent implements OnInit {
  receipt: ReceiptDetailModel | null = null;
  loading = false;
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
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

    this.receiptService
      .getReceiptById(id)
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (data) => {
          this.receipt = data;
        },
        error: () => {
          this.errorMessage = 'Unable to load receipt.';
        },
      });
  }
  get categoryTotals(): { name: string; amount: number }[] {
    if (!this.receipt?.structured_data?.category_totals) {
      return [];
    }

    return Object.entries(this.receipt.structured_data.category_totals).map(([name, amount]) => ({
      name: this.formatCategoryName(name),
      amount,
    }));
  }

  formatCategoryName(category: string): string {
    return category
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  get extractedItems() {
    return this.receipt?.structured_data?.items ?? [];
  }

  get validationStatusLabel(): string {
    const validation = this.receipt?.validation_result;

    if (!validation) return 'Unknown';

    if (!validation.is_valid) {
      return 'Invalid';
    }

    if (validation.warnings.length > 0) {
      return 'Needs review';
    }

    return 'Valid';
  }

  get reviewButtonLabel(): string {
    if (this.validationStatusLabel === 'Invalid') {
      return 'Fix extraction';
    }

    if (this.validationStatusLabel === 'Needs review') {
      return 'Review and correct';
    }

    return 'Edit extracted data';
  }

  get reviewButtonVariant(): string {
    if (this.validationStatusLabel === 'Invalid') {
      return 'danger';
    }

    if (this.validationStatusLabel === 'Needs review') {
      return 'warning';
    }

    return 'neutral';
  }
}
