import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { AnalyticsService } from '../../core/services/analytics.service';
import {
  AnalyticsInsightsResponse,
  CategorySpendingItem,
  MerchantSpendingItem,
  MonthlySpendingItem,
  TopProductInsightItem,
} from '../../core/models/analytics.model';
import { PageState } from '../../shared/components/page-state/page-state';

@Component({
  selector: 'app-analytics',
  imports: [DecimalPipe, FormsModule, PageState],
  templateUrl: './analytics.html',
  styleUrl: './analytics.css',
})
export class Analytics implements OnInit {
  insights: AnalyticsInsightsResponse | null = null;

  merchantSpending: MerchantSpendingItem[] = [];
  monthlySpending: MonthlySpendingItem[] = [];
  topProducts: TopProductInsightItem[] = [];
  categorySpending: CategorySpendingItem[] = [];

  selectedPeriod = 'all';
  dateFrom = '';
  dateTo = '';
  selectedMerchant = '';
  selectedCategory = '';

  loading = false;
  errorMessage = '';

  showFilters = false;
  showAllMerchants = false;
  showAllCategories = false;
  showAllProducts = false;

  readonly minDonutSlicePercentage = 4;

  readonly chartWidth = 720;
  readonly chartHeight = 240;

  constructor(
    private analyticsService: AnalyticsService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadAnalytics();
  }

  loadAnalytics(): void {
    this.loading = true;
    this.errorMessage = '';

    this.analyticsService
      .getInsights({
        period: this.selectedPeriod,
        date_from: this.selectedPeriod === 'custom' ? this.dateFrom : '',
        date_to: this.selectedPeriod === 'custom' ? this.dateTo : '',
        merchant: this.selectedMerchant,
        category: this.selectedCategory,
      })
      .subscribe({
        next: (data) => {
          this.insights = data;

          this.merchantSpending = data.merchant_spending;
          this.monthlySpending = data.monthly_spending;
          this.topProducts = data.top_products;
          this.categorySpending = data.category_spending;

          this.loading = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.errorMessage = 'Unable to load analytics data.';
          this.loading = false;
          this.cdr.detectChanges();
        },
      });
  }

  resetFilters(): void {
    this.selectedPeriod = 'all';
    this.dateFrom = '';
    this.dateTo = '';
    this.selectedMerchant = '';
    this.selectedCategory = '';
    this.loadAnalytics();
  }

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  toggleMerchants(): void {
    this.showAllMerchants = !this.showAllMerchants;
  }

  toggleCategories(): void {
    this.showAllCategories = !this.showAllCategories;
  }

  toggleProducts(): void {
    this.showAllProducts = !this.showAllProducts;
  }

  get totalSpent(): number {
    return this.insights?.kpis.total_spent ?? 0;
  }

  get receiptsCount(): number {
    return this.insights?.kpis.receipt_count ?? 0;
  }

  get averageBasket(): number {
    return this.insights?.kpis.average_basket ?? 0;
  }

  get topMerchant(): string {
    return this.insights?.kpis.top_merchant ?? 'No data';
  }

  get topCategory(): string {
    const category = this.insights?.kpis.top_category;
    return category ? this.formatLabel(category) : 'No data';
  }

  get merchantOptions(): string[] {
    return this.insights?.filter_options.merchants ?? [];
  }

  get categoryOptions(): string[] {
    return this.insights?.filter_options.categories ?? [];
  }

  get visibleMerchants(): MerchantSpendingItem[] {
    return this.showAllMerchants ? this.merchantSpending : this.merchantSpending.slice(0, 5);
  }

  get visibleCategories(): CategorySpendingItem[] {
    return this.showAllCategories ? this.categorySpending : this.categorySpending.slice(0, 6);
  }

  get visibleProducts(): TopProductInsightItem[] {
    return this.showAllProducts ? this.topProducts : this.topProducts.slice(0, 8);
  }

  get maxMonthlySpending(): number {
    if (this.monthlySpending.length === 0) return 0;

    return Math.max(...this.monthlySpending.map((month) => month.total_spent));
  }

  get maxMerchantSpending(): number {
    if (this.merchantSpending.length === 0) return 0;

    return Math.max(...this.merchantSpending.map((merchant) => merchant.total_spent));
  }

  get maxProductSpending(): number {
    if (this.topProducts.length === 0) return 0;

    return Math.max(...this.topProducts.map((product) => product.total_spent));
  }

  get maxCategorySpending(): number {
    if (this.categorySpending.length === 0) return 0;

    return Math.max(...this.categorySpending.map((category) => category.total_spent));
  }

  get activeFiltersCount(): number {
    let count = 0;

    if (this.selectedPeriod !== 'all') count++;
    if (this.selectedMerchant) count++;
    if (this.selectedCategory) count++;
    if (this.selectedPeriod === 'custom' && this.dateFrom) count++;
    if (this.selectedPeriod === 'custom' && this.dateTo) count++;

    return count;
  }

  get selectedPeriodLabel(): string {
    const labels: Record<string, string> = {
      all: 'All time',
      today: 'Today',
      this_month: 'This month',
      custom: 'Custom period',
    };

    return labels[this.selectedPeriod] ?? 'All time';
  }

  get dataQualityScore(): number {
    return this.insights?.data_quality.score ?? 0;
  }

  get dataQualityLabel(): string {
    return this.insights?.data_quality.label ?? 'No data';
  }

  get engineeringSummary(): string {
    const quality = this.insights?.data_quality;

    if (!quality || quality.receipt_count === 0) {
      return 'No processed receipts available for analytics.';
    }

    return `${quality.receipt_count} receipt(s), ${quality.product_line_count} product line(s), ${quality.category_count} category bucket(s), ${quality.merchant_count} merchant group(s).`;
  }

  get dataAnalystInsight(): string {
    if (this.receiptsCount === 0) {
      return 'No receipt data available yet.';
    }

    if (this.selectedMerchant) {
      return `${this.selectedMerchant} represents ${this.totalSpent.toFixed(2)} EUR in the current filtered dataset.`;
    }

    if (this.selectedCategory) {
      return `${this.formatLabel(this.selectedCategory)} is isolated to analyze category-level spending behavior.`;
    }

    return `${this.topMerchant} is currently the top merchant and ${this.topCategory} is the highest spending category.`;
  }

  get dataEngineeringInsight(): string {
    return 'OCR extraction → document classification → JSON structuring → schema validation → business validation → analytics aggregation.';
  }

  get averageProductValue(): number {
    if (this.topProducts.length === 0) return 0;

    const total = this.topProducts.reduce((sum, product) => sum + product.total_spent, 0);

    return Number((total / this.topProducts.length).toFixed(2));
  }

  get categoryTotalSpent(): number {
    return Number(
      this.categorySpending.reduce((total, category) => total + category.total_spent, 0).toFixed(2),
    );
  }

  get categoryShareItems(): {
    category: string;
    label: string;
    amount: number;
    percentage: number;
    color: string;
  }[] {
    if (this.categoryTotalSpent === 0) return [];

    const rawItems = this.categorySpending.map((category) => {
      const percentage = (category.total_spent / this.categoryTotalSpent) * 100;

      return {
        category: category.category,
        label: this.formatLabel(category.category),
        amount: category.total_spent,
        percentage,
        color: this.getCategoryColor(category.category),
      };
    });

    const mainItems = rawItems.filter((item) => item.percentage >= this.minDonutSlicePercentage);

    const smallItems = rawItems.filter((item) => item.percentage < this.minDonutSlicePercentage);

    if (smallItems.length === 0) {
      return rawItems.map((item) => ({
        ...item,
        percentage: Math.round(item.percentage),
      }));
    }

    const otherAmount = smallItems.reduce((sum, item) => sum + item.amount, 0);

    return [
      ...mainItems.map((item) => ({
        ...item,
        percentage: Math.round(item.percentage),
      })),
      {
        category: 'other',
        label: 'Other small categories',
        amount: Number(otherAmount.toFixed(2)),
        percentage: Math.round((otherAmount / this.categoryTotalSpent) * 100),
        color: 'var(--category-other)',
      },
    ];
  }

  get donutGradient(): string {
    if (this.categoryShareItems.length === 0) {
      return 'conic-gradient(var(--color-border) 0deg 360deg)';
    }

    let currentDegree = 0;

    const segments = this.categoryShareItems.map((item) => {
      const degrees = (item.amount / this.categoryTotalSpent) * 360;
      const start = currentDegree;
      const end = currentDegree + degrees;

      currentDegree = end;

      return `${item.color} ${start}deg ${end}deg`;
    });

    return `conic-gradient(${segments.join(', ')})`;
  }

  get monthlyLinePoints(): string {
    if (this.monthlySpending.length === 0) return '';

    const max = this.maxMonthlySpending || 1;
    const lastIndex = Math.max(this.monthlySpending.length - 1, 1);

    return this.monthlySpending
      .map((month, index) => {
        const x = (index / lastIndex) * this.chartWidth;
        const y = this.chartHeight - (month.total_spent / max) * this.chartHeight;

        return `${x},${y}`;
      })
      .join(' ');
  }

  get monthlyAreaPoints(): string {
    if (!this.monthlyLinePoints) return '';

    return `0,${this.chartHeight} ${this.monthlyLinePoints} ${this.chartWidth},${this.chartHeight}`;
  }

  get monthlyChartDots(): {
    x: number;
    y: number;
    label: string;
    value: number;
  }[] {
    if (this.monthlySpending.length === 0) return [];

    const max = this.maxMonthlySpending || 1;
    const lastIndex = Math.max(this.monthlySpending.length - 1, 1);

    return this.monthlySpending.map((month, index) => ({
      x: (index / lastIndex) * this.chartWidth,
      y: this.chartHeight - (month.total_spent / max) * this.chartHeight,
      label: month.month,
      value: month.total_spent,
    }));
  }

  get productScatterPoints(): {
    name: string;
    quantity: number;
    amount: number;
    category: string | null;
    x: number;
    y: number;
    color: string;
  }[] {
    if (this.topProducts.length === 0) return [];

    const quantities = this.topProducts.map((product) => product.quantity || 0);
    const amounts = this.topProducts.map((product) => product.total_spent || 0);

    const minQuantity = Math.min(...quantities);
    const maxQuantity = Math.max(...quantities);

    const minAmount = Math.min(...amounts);
    const maxAmount = Math.max(...amounts);

    return this.topProducts.map((product) => {
      const quantity = product.quantity || 0;
      const amount = product.total_spent || 0;

      return {
        name: product.product_name,
        quantity,
        amount,
        category: product.category,
        x: this.scaleToChartPosition(quantity, minQuantity, maxQuantity),
        y: 100 - this.scaleToChartPosition(amount, minAmount, maxAmount),
        color: this.getCategoryColor(product.category),
      };
    });
  }

  get visibleCategoryShareItems(): {
    category: string;
    label: string;
    amount: number;
    percentage: number;
    color: string;
  }[] {
    return this.showAllCategories ? this.categoryShareItems : this.categoryShareItems.slice(0, 6);
  }

  get shouldShowCategoryToggle(): boolean {
    return this.categoryShareItems.length > 6;
  }

  get scatterXAxisTicks(): number[] {
    if (this.topProducts.length === 0) return [];

    const quantities = this.topProducts.map((product) => product.quantity || 0);
    const min = Math.min(...quantities);
    const max = Math.max(...quantities);

    return this.buildAxisTicks(min, max);
  }

  get scatterYAxisTicks(): number[] {
    if (this.topProducts.length === 0) return [];

    const amounts = this.topProducts.map((product) => product.total_spent || 0);
    const min = Math.min(...amounts);
    const max = Math.max(...amounts);

    return this.buildAxisTicks(min, max);
  }

  buildAxisTicks(min: number, max: number): number[] {
    if (max === min) {
      return [min];
    }

    const steps = 4;
    const interval = (max - min) / steps;

    return Array.from({ length: steps + 1 }, (_, index) =>
      Number((min + interval * index).toFixed(2)),
    );
  }

  getScatterTickPosition(value: number, ticks: number[]): number {
    if (ticks.length <= 1) {
      return 50;
    }

    const min = ticks[0];
    const max = ticks[ticks.length - 1];

    return this.scaleToChartPosition(value, min, max);
  }

  getBarWidth(value: number, max: number): string {
    if (!max || max <= 0) return '0%';

    const percentage = Math.round((value / max) * 100);

    return `${Math.max(percentage, 4)}%`;
  }

  getChartHeight(value: number, max: number): string {
    if (!max || max <= 0) return '4%';

    const percentage = Math.round((value / max) * 100);

    return `${Math.max(percentage, 6)}%`;
  }

  getCategoryColor(category: string | null | undefined): string {
    if (!category) {
      return 'var(--category-other)';
    }

    const cssName = category.replaceAll('_', '-');

    return `var(--category-${cssName}, var(--category-other))`;
  }

  formatLabel(value: string): string {
    return value
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  scaleToChartPosition(value: number, min: number, max: number): number {
    const padding = 10;

    if (max === min) {
      return 50;
    }

    const percentage = ((value - min) / (max - min)) * 100;

    return Math.min(100 - padding, Math.max(padding, percentage));
  }
}
