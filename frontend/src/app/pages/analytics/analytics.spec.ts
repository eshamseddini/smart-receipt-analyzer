import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { Analytics } from './analytics';
import { CategorySpendingItem, MerchantSpendingItem } from '../../core/models/analytics.model';

describe('Analytics', () => {
  let component: Analytics;
  let fixture: ComponentFixture<Analytics>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Analytics],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Analytics);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('activeFiltersCount', () => {
    it('counts zero when everything is at its default value', () => {
      expect(component.activeFiltersCount).toBe(0);
    });

    it('counts each active filter independently', () => {
      component.selectedPeriod = 'custom';
      component.dateFrom = '2026-01-01';
      component.dateTo = '2026-01-31';
      component.selectedMerchant = 'LIDL';
      component.selectedCategory = 'dairy';

      expect(component.activeFiltersCount).toBe(5);
    });

    it('does not count dateFrom/dateTo unless the period is custom', () => {
      component.selectedPeriod = 'all';
      component.dateFrom = '2026-01-01';
      component.dateTo = '2026-01-31';

      expect(component.activeFiltersCount).toBe(0);
    });
  });

  describe('visible* toggles', () => {
    const merchants: MerchantSpendingItem[] = Array.from({ length: 8 }, (_, i) => ({
      merchant_name: `Merchant ${i}`,
      total_spent: i,
      receipt_count: 1,
    }));

    it('limits merchants to 5 by default', () => {
      component.merchantSpending = merchants;
      expect(component.visibleMerchants.length).toBe(5);
    });

    it('shows every merchant once toggled', () => {
      component.merchantSpending = merchants;
      component.toggleMerchants();
      expect(component.visibleMerchants.length).toBe(8);
    });
  });

  describe('categoryShareItems', () => {
    it('groups slices under the minimum percentage into "Other"', () => {
      const categories: CategorySpendingItem[] = [
        { category: 'dairy', total_spent: 90 },
        { category: 'snack_sweet', total_spent: 2 },
        { category: 'beverage', total_spent: 8 },
      ];

      component.categorySpending = categories;

      const items = component.categoryShareItems;
      const labels = items.map((item) => item.category);

      // dairy (90%) and beverage (8%) stay as-is; snack_sweet (2%) is below
      // the 4% threshold and gets folded into a synthetic "other" bucket.
      expect(labels).toEqual(['dairy', 'beverage', 'other']);
      expect(items.find((item) => item.category === 'other')?.amount).toBe(2);
    });

    it('returns an empty list when there is no spending at all', () => {
      component.categorySpending = [];
      expect(component.categoryShareItems).toEqual([]);
    });
  });

  describe('formatLabel', () => {
    it('turns snake_case into Title Case words', () => {
      expect(component.formatLabel('snack_sweet')).toBe('Snack Sweet');
    });
  });

  describe('getCategoryColor', () => {
    it('maps a category to its CSS variable', () => {
      expect(component.getCategoryColor('snack_sweet')).toBe(
        'var(--category-snack-sweet, var(--category-other))',
      );
    });

    it('falls back to the "other" color when category is missing', () => {
      expect(component.getCategoryColor(null)).toBe('var(--category-other)');
    });
  });

  describe('KPI getters', () => {
    it('default to safe empty values when no insights are loaded yet', () => {
      expect(component.totalSpent).toBe(0);
      expect(component.receiptsCount).toBe(0);
      expect(component.topMerchant).toBe('No data');
      expect(component.topCategory).toBe('No data');
    });
  });
});
