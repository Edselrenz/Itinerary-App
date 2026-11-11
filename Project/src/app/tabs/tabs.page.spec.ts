import type { ComponentFixture } from '@angular/core/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { TabsPage } from './tabs.page';

describe('TabsPage', () => {
  let component: TabsPage;
  let fixture: ComponentFixture<TabsPage>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TabsPage],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TabsPage);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve(true));
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should reset query params to empty when map tab is clicked in discovery mode', () => {
    Object.defineProperty(router, 'url', { value: '/tabs/home', configurable: true });
    component.onMapTabClicked();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/map'], { queryParams: {} });
  });

  it('should preserve active route navigation when following a route on map (Finding 7)', () => {
    Object.defineProperty(router, 'url', { value: '/tabs/map?followRoute=true&routeItineraryId=it-123', configurable: true });
    component.onMapTabClicked();
    expect(router.navigate).not.toHaveBeenCalled();
  });
});
