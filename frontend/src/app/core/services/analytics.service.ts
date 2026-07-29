import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../constants/api.constants';
import {
  AnalyticsCharts,
  AnalyticsSummary,
  CategorySpendingItem,
  DocumentTypesStats,
  MerchantSpendingItem,
  MonthlySpendingItem,
  TopProductItem,
  ValidationStats,
  AnalyticsInsightsResponse,
} from '../models/analytics.model';

@Injectable({
  providedIn: 'root',
})
export class AnalyticsService {
  private readonly baseUrl = API_BASE_URL;

  constructor(private http: HttpClient) {}

  getAnalyticsSummary(): Observable<AnalyticsSummary> {
    return this.http.get<AnalyticsSummary>(`${this.baseUrl}/api/analytics/summary`);
  }

  getDocumentTypes(): Observable<DocumentTypesStats> {
    return this.http.get<DocumentTypesStats>(`${this.baseUrl}/api/analytics/document-types`);
  }

  getValidationStats(): Observable<ValidationStats> {
    return this.http.get<ValidationStats>(`${this.baseUrl}/api/analytics/validation`);
  }

  getChartsData(): Observable<AnalyticsCharts> {
    return this.http.get<AnalyticsCharts>(`${this.baseUrl}/api/analytics/charts`);
  }

  getMerchantSpending(): Observable<MerchantSpendingItem[]> {
    return this.http.get<MerchantSpendingItem[]>(`${this.baseUrl}/api/analytics/merchant-spending`);
  }

  getMonthlySpending(): Observable<MonthlySpendingItem[]> {
    return this.http.get<MonthlySpendingItem[]>(`${this.baseUrl}/api/analytics/monthly-spending`);
  }

  getTopProducts(limit = 10): Observable<TopProductItem[]> {
    return this.http.get<TopProductItem[]>(
      `${this.baseUrl}/api/analytics/top-products?limit=${limit}`,
    );
  }

  getCategorySpending(): Observable<CategorySpendingItem[]> {
    return this.http.get<CategorySpendingItem[]>(`${this.baseUrl}/api/analytics/category-spending`);
  }

  getInsights(params: {
    period?: string;
    date_from?: string;
    date_to?: string;
    merchant?: string;
    category?: string;
  }): Observable<AnalyticsInsightsResponse> {
    const queryParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        queryParams.set(key, value);
      }
    });

    return this.http.get<AnalyticsInsightsResponse>(
      `${this.baseUrl}/api/analytics/insights?${queryParams.toString()}`,
    );
  }
}
