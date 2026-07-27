import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { ReceiptDetailComponent } from './receipt-detail';

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
});
