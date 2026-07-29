import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../constants/api.constants';
import { HealthResponse } from '../models/health.model';

@Injectable({
  providedIn: 'root',
})
export class HealthService {
  private readonly baseUrl = API_BASE_URL;

  constructor(private http: HttpClient) {}

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/api/health`);
  }
}
