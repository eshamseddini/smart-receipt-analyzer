import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { ReceiptDetailComponent } from './receipt-detail';
import { ReceiptDetail } from '../../core/models/receipt.model';

function makeReceipt(overrides: Partial<ReceiptDetail> = {}): ReceiptDetail {
  return {
    id: 1,
    original_filename: 'ticket.png',
    content_type: 'image/png',
    saved_path: 'uploads/ticket.png',
    document_type: 'receipt',
    created_at: '2026-01-01T10:00:00Z',
    extracted_text: '',
    structured_data: {
      merchant_name: 'LIDL',
      purchase_date: '2026-01-01',
      total_amount: 10,
      discount_amount: 0,
      currency: 'EUR',
      category_totals: { dairy: 6, snack_sweet: 4 },
      items: [],
    },
    validation_result: { is_valid: true, errors: [], warnings: [] },
    ...overrides,
  };
}

describe('ReceiptDetailComponent', () => {
  let component: ReceiptDetailComponent;
  let fixture: ComponentFixture<ReceiptDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReceiptDetailComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ReceiptDetailComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('categoryTotals', () => {
    it('formats category keys into a display-friendly list', () => {
      component.receipt = makeReceipt();

      expect(component.categoryTotals).toEqual([
        { name: 'Dairy', amount: 6 },
        { name: 'Snack Sweet', amount: 4 },
      ]);
    });

    it('returns an empty list when there is no receipt loaded', () => {
      component.receipt = null;
      expect(component.categoryTotals).toEqual([]);
    });
  });

  describe('validationStatusLabel', () => {
    it('reports "Valid" when there are no errors or warnings', () => {
      component.receipt = makeReceipt({
        validation_result: { is_valid: true, errors: [], warnings: [] },
      });

      expect(component.validationStatusLabel).toBe('Valid');
    });

    it('reports "Needs review" when valid but with warnings', () => {
      component.receipt = makeReceipt({
        validation_result: { is_valid: true, errors: [], warnings: ['Purchase date is missing.'] },
      });

      expect(component.validationStatusLabel).toBe('Needs review');
    });

    it('reports "Invalid" when validation failed', () => {
      component.receipt = makeReceipt({
        validation_result: { is_valid: false, errors: ['Total amount is missing.'], warnings: [] },
      });

      expect(component.validationStatusLabel).toBe('Invalid');
    });

    it('reports "Unknown" when there is no validation result at all', () => {
      component.receipt = makeReceipt({ validation_result: null });
      expect(component.validationStatusLabel).toBe('Unknown');
    });
  });

  describe('review button label/variant', () => {
    it('prompts to fix extraction when invalid', () => {
      component.receipt = makeReceipt({
        validation_result: { is_valid: false, errors: ['x'], warnings: [] },
      });

      expect(component.reviewButtonLabel).toBe('Fix extraction');
      expect(component.reviewButtonVariant).toBe('danger');
    });

    it('prompts to review when there are warnings only', () => {
      component.receipt = makeReceipt({
        validation_result: { is_valid: true, errors: [], warnings: ['x'] },
      });

      expect(component.reviewButtonLabel).toBe('Review and correct');
      expect(component.reviewButtonVariant).toBe('warning');
    });

    it('offers a neutral edit action when everything is valid', () => {
      component.receipt = makeReceipt({
        validation_result: { is_valid: true, errors: [], warnings: [] },
      });

      expect(component.reviewButtonLabel).toBe('Edit extracted data');
      expect(component.reviewButtonVariant).toBe('neutral');
    });
  });
});
