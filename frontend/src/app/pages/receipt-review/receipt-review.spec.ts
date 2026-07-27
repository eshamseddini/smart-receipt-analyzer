import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { ReceiptReview } from './receipt-review';
import { ExtractedReceiptData } from '../../core/models/receipt.model';

function makeEditableData(overrides: Partial<ExtractedReceiptData> = {}): ExtractedReceiptData {
  return {
    merchant_name: 'LIDL',
    purchase_date: '2026-01-01',
    total_amount: 10,
    discount_amount: 0,
    currency: 'EUR',
    category_totals: {},
    items: [],
    ...overrides,
  };
}

describe('ReceiptReview', () => {
  let component: ReceiptReview;
  let fixture: ComponentFixture<ReceiptReview>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReceiptReview],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ReceiptReview);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('totals calculations', () => {
    it('recalculates an item line total from quantity and unit price', () => {
      component.editableData = makeEditableData();
      const item = { name: 'Milk', unit_price: 1.5, quantity: 2, total_price: 0, category: 'dairy' };

      component.recalculateItemTotal(item);

      expect(item.total_price).toBe(3);
    });

    it('recomputes category totals from all items', () => {
      component.editableData = makeEditableData({
        items: [
          { name: 'Milk', unit_price: 1.5, quantity: 2, total_price: 3, category: 'dairy' },
          { name: 'Bread', unit_price: 2, quantity: 1, total_price: 2, category: 'carbohydrate' },
          { name: 'Cheese', unit_price: 4, quantity: 1, total_price: 4, category: 'dairy' },
        ],
      });

      component.recalculateTotals();

      expect(component.editableData.category_totals).toEqual({
        dairy: 7,
        carbohydrate: 2,
      });
    });

    it('computes the difference between items total and expected total (paid + discount)', () => {
      component.editableData = makeEditableData({
        total_amount: 10,
        discount_amount: 2,
        items: [
          { name: 'Milk', unit_price: 6, quantity: 1, total_price: 6, category: 'dairy' },
          { name: 'Bread', unit_price: 6, quantity: 1, total_price: 6, category: 'carbohydrate' },
        ],
      });

      expect(component.itemsTotal).toBe(12);
      expect(component.expectedTotal).toBe(12);
      expect(component.difference).toBe(0);
    });

    it('adding an item appends an empty editable row', () => {
      component.editableData = makeEditableData({ items: [] });

      component.addItem();

      expect(component.editableData.items.length).toBe(1);
      expect(component.editableData.items[0]).toEqual({
        name: '',
        unit_price: 0,
        quantity: 1,
        total_price: 0,
        category: 'other',
      });
    });

    it('removing an item recalculates the remaining category totals', () => {
      component.editableData = makeEditableData({
        items: [
          { name: 'Milk', unit_price: 3, quantity: 1, total_price: 3, category: 'dairy' },
          { name: 'Bread', unit_price: 2, quantity: 1, total_price: 2, category: 'carbohydrate' },
        ],
      });

      component.removeItem(0);

      expect(component.editableData.items.length).toBe(1);
      expect(component.editableData.category_totals).toEqual({ carbohydrate: 2 });
    });
  });
});
