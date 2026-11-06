import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { PLATFORM_ID } from '@angular/core';
import { ItineraryRouteMapComponent } from './itinerary-route-map.component';
import { ItineraryDay, ItineraryItem } from '../../../core/models/itinerary.models';
import * as L from 'leaflet';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';

describe('ItineraryRouteMapComponent', () => {
  let component: ItineraryRouteMapComponent;
  let fixture: ComponentFixture<ItineraryRouteMapComponent>;
  let mockRouter: { navigate: ReturnType<typeof vi.fn> };

  const sampleDay: ItineraryDay = {
    id: 'day-1',
    itinerary_id: 'itin-123',
    day_number: 1,
    travel_date: '2026-11-06',
    title: 'Historic Nueva Ecija',
    items: [
      {
        id: 'stop-1',
        day_id: 'day-1',
        order: 0,
        custom_title: 'Plaza Lucero',
        place: {
          id: 'place-1',
          name: 'Plaza Lucero',
          municipality: 'Cabanatuan City',
          latitude: 15.4862,
          longitude: 120.9658,
          category: 'Historical',
        },
      } as unknown as ItineraryItem,
      {
        id: 'stop-2',
        day_id: 'day-1',
        order: 1,
        custom_title: 'Camp Pangatian',
        route_polyline_from_prev: '_p~iF~ps|U_ulLnnqC_mqNvxq`@',
        place: {
          id: 'place-2',
          name: 'Camp Pangatian Memorial Shrine',
          municipality: 'Cabanatuan City',
          latitude: 15.5101,
          longitude: 121.0255,
          category: 'Historical',
        },
      } as unknown as ItineraryItem,
    ],
  };

  function createMockLMap() {
    return {
      addLayer: vi.fn(),
      removeLayer: vi.fn(),
      fitBounds: vi.fn(),
      setView: vi.fn(),
      invalidateSize: vi.fn(),
      remove: vi.fn(),
    } as unknown as L.Map;
  }

  beforeEach(async () => {
    TestBed.resetTestingModule();
    mockRouter = {
      navigate: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ItineraryRouteMapComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: PLATFORM_ID, useValue: 'browser' },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ItineraryRouteMapComponent);
    component = fixture.componentInstance;
    component.day = sampleDay;
    component.itineraryId = 'itin-123';
    component.map = createMockLMap();
  });

  afterEach(() => {
    if (component.map) {
      component.map.remove();
      component.map = null;
    }
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
    expect(component.isExpanded).toBe(true);
  });

  it('should toggle expanded state and invalidate map size', () => {
    expect(component.isExpanded).toBe(true);
    component.toggleExpand();
    expect(component.isExpanded).toBe(false);

    component.toggleExpand();
    expect(component.isExpanded).toBe(true);
  });

  it('should navigate to /tabs/map on openFullRouteOnMap', () => {
    component.openFullRouteOnMap();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tabs/map'], {
      queryParams: {
        followRoute: 'true',
        dayNumber: 1,
        itineraryId: 'itin-123',
      },
    });
  });

  it('should not navigate if day is null', () => {
    component.day = null;
    component.openFullRouteOnMap();
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  });

  it('should render route markers and polylines into Leaflet map', () => {
    fixture.detectChanges();
    component.initOrUpdateMap();

    expect(component.stopsLayer).toBeTruthy();
    expect(component.polylineLayer).toBeTruthy();
  });

  it('should render fallback geodesic spline if route_polyline_from_prev is missing', () => {
    fixture.detectChanges();
    const dayWithoutPolyline: ItineraryDay = {
      ...sampleDay,
      items: [
        {
          ...sampleDay.items[0],
          route_polyline_from_prev: undefined,
        },
        {
          ...sampleDay.items[1],
          route_polyline_from_prev: undefined,
        },
      ],
    };
    component.day = dayWithoutPolyline;

    component.initOrUpdateMap();
    expect(component.polylineLayer).toBeTruthy();
  });

  it('should emit stopSelected when stopSelected is triggered', () => {
    const spy = vi.spyOn(component.stopSelected, 'emit');
    component.stopSelected.emit(sampleDay.items[0]);
    expect(spy).toHaveBeenCalledWith(sampleDay.items[0]);
  });
});
