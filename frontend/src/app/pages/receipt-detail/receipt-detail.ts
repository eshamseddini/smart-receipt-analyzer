import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { DatePipe, JsonPipe, DecimalPipe } from '@angular/common';
import { finalize, interval, Subscription, switchMap, takeWhile } from 'rxjs';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ReceiptService } from '../../core/services/receipt.service';
import { ReceiptDetail as ReceiptDetailModel } from '../../core/models/receipt.model';
import { PageState } from '../../shared/components/page-state/page-state';

const POLL_INTERVAL_MS = 3000;

@Component({
  selector: 'app-receipt-detail',
  imports: [DatePipe, JsonPipe, RouterLink, PageState, DecimalPipe],
  templateUrl: './receipt-detail.html',
  styleUrl: './receipt-detail.css',
})
export class ReceiptDetailComponent implements OnInit, OnDestroy {
  receipt: ReceiptDetailModel | null = null;
  loading = false;
  errorMessage = '';

  private pollingSubscription: Subscription | null = null;

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

  ngOnDestroy(): void {
    this.pollingSubscription?.unsubscribe();
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

          if (data.processing_status === 'pending') {
            this.startPolling(id);
          }
        },
        error: () => {
          this.errorMessage = 'Unable to load receipt.';
        },
      });
  }

  private startPolling(id: number): void {
    this.pollingSubscription?.unsubscribe();

    this.pollingSubscription = interval(POLL_INTERVAL_MS)
      .pipe(
        switchMap(() => this.receiptService.getReceiptById(id)),
        takeWhile((data) => data.processing_status === 'pending', true),
      )
      .subscribe((data) => {
        this.receipt = data;
        this.cdr.detectChanges();
      });
  }

  get isProcessing(): boolean {
    return this.receipt?.processing_status === 'pending';
  }

  get isFailed(): boolean {
    return this.receipt?.processing_status === 'failed';
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
