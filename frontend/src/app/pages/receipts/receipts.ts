import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { finalize } from 'rxjs';

import { ReceiptListItem } from '../../core/models/receipt.model';
import { ReceiptService } from '../../core/services/receipt.service';
import { Router, RouterLink } from '@angular/router';
import { PageState } from '../../shared/components/page-state/page-state';
import { ActionButton } from '../../shared/components/action-button/action-button';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-receipts',
  imports: [DatePipe, RouterLink, FormsModule, PageState, ActionButton],
  templateUrl: './receipts.html',
  styleUrl: './receipts.css',
})
export class Receipts implements OnInit {
  receipts: ReceiptListItem[] = [];

  loading = false;
  uploading = false;
  deleting = false;

  errorMessage = '';
  successMessage = '';

  searchTerm = '';
  selectedDocumentType = 'all';
  sortOrder: 'newest' | 'oldest' = 'newest';

  pageSize = 10;
  currentPage = 1;
  totalReceipts = 0;

  selectedFile: File | null = null;

  showDeleteModal = false;
  receiptIdToDelete: number | null = null;

  constructor(
    private receiptService: ReceiptService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadReceipts();
  }

  loadReceipts(): void {
    this.loading = true;
    this.errorMessage = '';

    const skip = (this.currentPage - 1) * this.pageSize;

    this.receiptService
      .getReceipts(skip, this.pageSize)
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (data) => {
          this.receipts = data.items;
          this.totalReceipts = data.total;
        },
        error: () => {
          this.errorMessage = 'Unable to load receipts.';
        },
      });
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalReceipts / this.pageSize));
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages || page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.loadReceipts();
  }

  previousPage(): void {
    this.goToPage(this.currentPage - 1);
  }

  nextPage(): void {
    this.goToPage(this.currentPage + 1);
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (!input.files || input.files.length === 0) {
      this.selectedFile = null;
      return;
    }

    this.selectedFile = input.files[0];
    this.successMessage = '';
    this.errorMessage = '';
  }

  uploadReceipt(): void {
    if (!this.selectedFile) {
      this.errorMessage = 'Please select a file before uploading.';
      return;
    }

    this.uploading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.receiptService.uploadReceipt(this.selectedFile).subscribe({
      next: (response) => {
        this.uploading = false;
        this.errorMessage = '';
        this.successMessage = 'Receipt uploaded and processed successfully.';

        // adapte selon ton router actuel
        this.router.navigate(['/receipts', response.receipt_id]);
      },

      error: (error) => {
        this.uploading = false;
        this.successMessage = '';

        if (error.status === 422 && error.error?.detail?.message) {
          this.errorMessage = error.error.detail.message;
          return;
        }

        if (error.status === 400 && error.error?.detail) {
          this.errorMessage = error.error.detail;
          return;
        }

        this.errorMessage = 'An unexpected error occurred while uploading the file.';
      },
    });
  }

  get filteredReceipts(): ReceiptListItem[] {
    const term = this.searchTerm.trim().toLowerCase();

    const filtered = this.receipts.filter((receipt) => {
      const filename = receipt.original_filename.toLowerCase();
      const contentType = receipt.content_type.toLowerCase();
      const documentType = receipt.document_type?.toLowerCase() ?? 'unknown';

      const matchesSearch =
        !term ||
        filename.includes(term) ||
        contentType.includes(term) ||
        documentType.includes(term);

      const matchesType =
        this.selectedDocumentType === 'all' ||
        documentType === this.selectedDocumentType;

      return matchesSearch && matchesType;
    });

    return filtered.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();

      return this.sortOrder === 'newest'
        ? dateB - dateA
        : dateA - dateB;
    });
  }

  get resultsLabel(): string {
    const shown = this.filteredReceipts.length;

    if (this.totalReceipts === 0) {
      return 'No documents yet';
    }

    if (shown === this.receipts.length) {
      return `${this.totalReceipts} document${this.totalReceipts > 1 ? 's' : ''} · page ${this.currentPage} of ${this.totalPages}`;
    }

    return `Showing ${shown} of ${this.receipts.length} on this page (${this.totalReceipts} total)`;
  }

  openDeleteModal(id: number): void {
    this.receiptIdToDelete = id;
    this.showDeleteModal = true;
    this.errorMessage = '';
    this.successMessage = '';
  }

  closeDeleteModal(): void {
    this.showDeleteModal = false;
    this.receiptIdToDelete = null;
  }

  confirmDelete(): void {
    if (this.receiptIdToDelete === null) {
      return;
    }

    const id = this.receiptIdToDelete;

    this.deleting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.receiptService
      .deleteReceipt(id)
      .pipe(
        finalize(() => {
          this.deleting = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.receipts = this.receipts.filter((receipt) => receipt.id !== id);
          this.successMessage = 'Receipt deleted successfully.';
          this.closeDeleteModal();
          this.loadReceipts();
        },
        error: () => {
          this.errorMessage = 'Unable to delete the receipt.';
          this.closeDeleteModal();
          this.loadReceipts();
        },
      });
  }
}