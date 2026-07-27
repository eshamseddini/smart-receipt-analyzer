import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { Receipts } from './receipts';
import { ReceiptService } from '../../core/services/receipt.service';
import { ReceiptListItem } from '../../core/models/receipt.model';

function makeReceipt(overrides: Partial<ReceiptListItem>): ReceiptListItem {
  return {
    id: 1,
    original_filename: 'ticket.png',
    content_type: 'image/png',
    saved_path: 'uploads/ticket.png',
    document_type: 'receipt',
    created_at: '2026-01-01T10:00:00Z',
    ...overrides,
  };
}

describe('Receipts', () => {
  let component: Receipts;
  let fixture: ComponentFixture<Receipts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Receipts],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Receipts);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('pagination', () => {
    it('computes the number of pages from the server total and the page size', () => {
      component.pageSize = 10;
      component.totalReceipts = 25;

      expect(component.totalPages).toBe(3);
    });

    it('always reports at least one page, even with zero receipts', () => {
      component.pageSize = 10;
      component.totalReceipts = 0;

      expect(component.totalPages).toBe(1);
    });

    it('ignores navigation to a page below 1 or beyond the last page', () => {
      component.pageSize = 10;
      component.totalReceipts = 20;
      component.currentPage = 1;

      const receiptService = TestBed.inject(ReceiptService);
      const getReceiptsSpy = vi.spyOn(receiptService, 'getReceipts');

      component.goToPage(0);
      component.goToPage(3);

      expect(component.currentPage).toBe(1);
      expect(getReceiptsSpy).not.toHaveBeenCalled();
    });

    it('reloads the correct page (skip/limit) when navigating to a valid page', () => {
      component.pageSize = 10;
      component.totalReceipts = 25;
      component.currentPage = 1;

      const receiptService = TestBed.inject(ReceiptService);
      const getReceiptsSpy = vi
        .spyOn(receiptService, 'getReceipts')
        .mockReturnValue(of({ items: [], total: 25, skip: 10, limit: 10 }));

      component.goToPage(2);

      expect(component.currentPage).toBe(2);
      expect(getReceiptsSpy).toHaveBeenCalledWith(10, 10);
    });
  });

  describe('filteredReceipts', () => {
    beforeEach(() => {
      component.receipts = [
        makeReceipt({ id: 1, original_filename: 'lidl-ticket.png', document_type: 'receipt' }),
        makeReceipt({ id: 2, original_filename: 'invoice.pdf', document_type: 'invoice' }),
        makeReceipt({ id: 3, original_filename: 'unknown-doc.jpg', document_type: 'unknown' }),
      ];
    });

    it('filters by search term across filename and document type', () => {
      component.searchTerm = 'lidl';

      expect(component.filteredReceipts.map((r) => r.id)).toEqual([1]);
    });

    it('filters by selected document type', () => {
      component.searchTerm = '';
      component.selectedDocumentType = 'invoice';

      expect(component.filteredReceipts.map((r) => r.id)).toEqual([2]);
    });

    it('returns everything when the filters do not match anything specific', () => {
      component.searchTerm = '';
      component.selectedDocumentType = 'all';

      expect(component.filteredReceipts.length).toBe(3);
    });
  });
});
