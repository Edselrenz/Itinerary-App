import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RouteTrackingService } from './route-tracking.service';
import { ItineraryDay, ItineraryItem } from '../models/itinerary.models';
import { Place } from '../models/place.models';
import { encodePolyline } from '../utils/polyline.util';
import { Position } from '@capacitor/geolocation';

describe('RouteTrackingService', () => {
  let service: RouteTrackingService;

  const mockPlace1 = {
    id: 'place-1',
    name: 'Cabanatuan Plaza',
    category: 'tourist_attraction',
    latitude: 15.4859,
    longitude: 120.9669,
  } as unknown as Place;

  const mockPlace2 = {
    id: 'place-2',
    name: 'Palayan Capitol',
    category: 'public_facility',
    latitude: 15.5414,
    longitude: 121.0844,
  } as unknown as Place;

  const mockItem1: ItineraryItem = {
    id: 'item-1',
    day_id: 'day-1',
    place_id: 'place-1',
    sort_order: 0,
    duration_minutes: 60,
    place: mockPlace1,
  };

  const mockItem2: ItineraryItem = {
    id: 'item-2',
    day_id: 'day-1',
    place_id: 'place-2',
    sort_order: 1,
    duration_minutes: 60,
    place: mockPlace2,
  };

  const testPolyline = encodePolyline([
    [15.4859, 120.9669],
    [15.5000, 121.0000],
    [15.5414, 121.0844],
  ]);

  const mockDay: ItineraryDay = {
    id: 'day-1',
    itinerary_id: 'itin-1',
    day_number: 1,
    travel_date: '2026-11-06',
    day_overview_polyline: testPolyline,
    items: [mockItem1, mockItem2],
  };

  beforeEach(() => {
    service = new RouteTrackingService();
  });

  it('should initialize with idle state', () => {
    const state = service.currentState;
    expect(state.isTracking).toBe(false);
    expect(state.currentPosition).toBeNull();
    expect(state.isOffRoute).toBe(false);
  });

  it('should start tracking and initialize waypoints from day', async () => {
    await service.startTracking(mockDay);
    const state = service.currentState;

    expect(state.isTracking).toBe(true);
    expect(state.activeDay?.id).toBe('day-1');
    expect(state.nextStop?.id).toBe('item-1');
    expect(state.nextStopIndex).toBe(0);
  });

  it('should throttle updates if position delta is less than 10 meters', async () => {
    await service.startTracking(mockDay);

    const pos1 = {
      timestamp: Date.now(),
      coords: {
        latitude: 15.4859,
        longitude: 120.9669,
        accuracy: 5,
        altitude: null,
        altitudeAccuracy: null,
        heading: 90,
        speed: 10,
      },
    } as unknown as Position;

    service.handlePositionUpdate(pos1);
    expect(service.currentState.currentPosition).toEqual([15.4859, 120.9669]);

    // Small jitter: ~1 meter away (0.00001 deg lat is ~1.1 meters)
    const jitterPos = {
      timestamp: Date.now() + 1000,
      coords: {
        latitude: 15.485908,
        longitude: 120.966905,
        accuracy: 5,
        altitude: null,
        altitudeAccuracy: null,
        heading: 92,
        speed: 10,
      },
    } as unknown as Position;

    service.handlePositionUpdate(jitterPos);
    // Should still have original position because movement was throttled (<10m)
    expect(service.currentState.currentPosition).toEqual([15.4859, 120.9669]);
  });

  it('should detect off-route when user departs > 100m from route polyline', async () => {
    await service.startTracking(mockDay);

    let rerouteFired = false;
    service.rerouteNeeded$.subscribe((evt) => {
      rerouteFired = true;
      expect(evt.distanceToRoute).toBeGreaterThan(100);
    });

    // Position far away (> 500m)
    const offRoutePos = {
      timestamp: Date.now(),
      coords: {
        latitude: 15.4950,
        longitude: 120.9400,
        accuracy: 5,
        altitude: null,
        altitudeAccuracy: null,
        heading: 0,
        speed: 8,
      },
    } as unknown as Position;

    service.handlePositionUpdate(offRoutePos);
    expect(service.currentState.isOffRoute).toBe(true);
    expect(rerouteFired).toBe(true);
  });

  it('should advance to next stop when user arrives within 50 meters of waypoint', async () => {
    await service.startTracking(mockDay);

    let reachedStopId: string | null = null;
    service.stopReached$.subscribe((evt) => {
      reachedStopId = evt.stop.id;
    });

    // Position within 15 meters of stop 1
    const atStop1 = {
      timestamp: Date.now(),
      coords: {
        latitude: 15.4860,
        longitude: 120.9670,
        accuracy: 5,
        altitude: null,
        altitudeAccuracy: null,
        heading: 45,
        speed: 1,
      },
    } as unknown as Position;

    service.handlePositionUpdate(atStop1);

    expect(reachedStopId).toBe('item-1');
    expect(service.currentState.completedStopIds.has('item-1')).toBe(true);
    expect(service.currentState.nextStop?.id).toBe('item-2');
    expect(service.currentState.nextStopIndex).toBe(1);
  });

  it('should reset state on stopTracking', async () => {
    await service.startTracking(mockDay);
    await service.stopTracking();

    expect(service.currentState.isTracking).toBe(false);
    expect(service.currentState.activeDay).toBeNull();
    expect(service.currentState.nextStop).toBeNull();
  });
});
