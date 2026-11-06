import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { Geolocation, Position, CallbackID } from '@capacitor/geolocation';
import { ItineraryDay, ItineraryItem } from '../models/itinerary.models';
import {
  decodePolyline,
  haversineDistanceMeters,
  distanceToPolylineMeters,
  remainingDistanceAlongPolylineMeters,
} from '../utils/polyline.util';

export interface TrackingOptions {
  stopArrivalThresholdMeters?: number; // Default 50m
  offRouteThresholdMeters?: number; // Default 100m
  movementThrottleMeters?: number; // Default 10m
  averageSpeedMetersPerSec?: number; // Default ~36 km/h = 10 m/s
}

export interface RouteTrackingState {
  isTracking: boolean;
  currentPosition: [number, number] | null; // [latitude, longitude]
  heading: number | null;
  speed: number | null;
  snappedPosition: [number, number] | null;
  distanceToRouteMeters: number | null;
  isOffRoute: boolean;
  activeDay: ItineraryDay | null;
  nextStop: ItineraryItem | null;
  nextStopIndex: number | null;
  distanceToNextStopMeters: number | null;
  etaSecondsToNextStop: number | null;
  totalRemainingDistanceMeters: number | null;
  totalRemainingDurationSeconds: number | null;
  completedStopIds: Set<string>;
}

export const INITIAL_TRACKING_STATE: RouteTrackingState = {
  isTracking: false,
  currentPosition: null,
  heading: null,
  speed: null,
  snappedPosition: null,
  distanceToRouteMeters: null,
  isOffRoute: false,
  activeDay: null,
  nextStop: null,
  nextStopIndex: null,
  distanceToNextStopMeters: null,
  etaSecondsToNextStop: null,
  totalRemainingDistanceMeters: null,
  totalRemainingDurationSeconds: null,
  completedStopIds: new Set<string>(),
};

@Injectable({
  providedIn: 'root',
})
export class RouteTrackingService {
  private stateSubject = new BehaviorSubject<RouteTrackingState>({ ...INITIAL_TRACKING_STATE });
  public readonly state$: Observable<RouteTrackingState> = this.stateSubject.asObservable();

  private rerouteNeededSubject = new Subject<{ day: ItineraryDay; currentPosition: [number, number]; distanceToRoute: number }>();
  public readonly rerouteNeeded$: Observable<{ day: ItineraryDay; currentPosition: [number, number]; distanceToRoute: number }> =
    this.rerouteNeededSubject.asObservable();

  private stopReachedSubject = new Subject<{ stop: ItineraryItem; index: number }>();
  public readonly stopReached$: Observable<{ stop: ItineraryItem; index: number }> = this.stopReachedSubject.asObservable();

  private recenterSubject = new Subject<[number, number]>();
  public readonly recenter$: Observable<[number, number]> = this.recenterSubject.asObservable();

  private watchId: CallbackID | null = null;
  private activePolylineCoords: Array<[number, number]> = [];
  private options: Required<TrackingOptions> = {
    stopArrivalThresholdMeters: 50,
    offRouteThresholdMeters: 100,
    movementThrottleMeters: 10,
    averageSpeedMetersPerSec: 10, // ~36 km/h
  };

  public get currentState(): RouteTrackingState {
    return this.stateSubject.getValue();
  }

  /**
   * Starts GPS watch tracking for the specified itinerary day route.
   */
  public async startTracking(
    day: ItineraryDay,
    customOptions?: TrackingOptions
  ): Promise<void> {
    await this.stopTracking();

    this.options = {
      stopArrivalThresholdMeters: customOptions?.stopArrivalThresholdMeters ?? 50,
      offRouteThresholdMeters: customOptions?.offRouteThresholdMeters ?? 100,
      movementThrottleMeters: customOptions?.movementThrottleMeters ?? 10,
      averageSpeedMetersPerSec: customOptions?.averageSpeedMetersPerSec ?? 10,
    };

    if (day.day_overview_polyline) {
      this.activePolylineCoords = decodePolyline(day.day_overview_polyline);
    } else {
      this.activePolylineCoords = [];
    }

    const items = day.items || [];
    const firstStop = items.length > 0 ? items[0] : null;

    this.stateSubject.next({
      ...INITIAL_TRACKING_STATE,
      isTracking: true,
      activeDay: day,
      nextStop: firstStop,
      nextStopIndex: firstStop ? 0 : null,
      completedStopIds: new Set<string>(),
    });

    try {
      this.watchId = await Geolocation.watchPosition(
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        },
        (position: Position | null, err?: unknown) => {
          if (err || !position) {
            return;
          }
          this.handlePositionUpdate(position);
        }
      );
    } catch {
      // In web or headless environments Geolocation may fall back or reject
    }
  }

  /**
   * Stops active GPS route tracking and clears active listeners.
   */
  public async stopTracking(): Promise<void> {
    if (this.watchId !== null) {
      try {
        await Geolocation.clearWatch({ id: this.watchId });
      } catch {
        // Ignore clear watch errors
      }
      this.watchId = null;
    }

    this.activePolylineCoords = [];
    this.stateSubject.next({
      ...INITIAL_TRACKING_STATE,
      completedStopIds: new Set<string>(),
    });
  }

  /**
   * Processes an incoming GPS coordinate update with 10m movement throttle,
   * polyline snapping, off-route detection, and waypoint arrival tracking.
   */
  public handlePositionUpdate(position: Position): void {
    const current = this.currentState;
    if (!current.isTracking || !current.activeDay) {
      return;
    }

    const newPos: [number, number] = [
      position.coords.latitude,
      position.coords.longitude,
    ];

    // Movement throttle: Ignore updates if user moved less than throttle threshold
    if (current.currentPosition) {
      const movedDist = haversineDistanceMeters(
        current.currentPosition[0],
        current.currentPosition[1],
        newPos[0],
        newPos[1]
      );
      if (movedDist < this.options.movementThrottleMeters) {
        return;
      }
    }

    // Polyline snapping and off-route calculation
    let snappedPos: [number, number] | null = null;
    let distToRoute: number | null = null;
    let isOffRoute = false;

    if (this.activePolylineCoords.length > 0) {
      const snap = distanceToPolylineMeters(newPos, this.activePolylineCoords);
      distToRoute = snap.minDistance;
      snappedPos = snap.closestPoint;
      isOffRoute = distToRoute > this.options.offRouteThresholdMeters;

      if (isOffRoute && !current.isOffRoute) {
        this.rerouteNeededSubject.next({
          day: current.activeDay,
          currentPosition: newPos,
          distanceToRoute: distToRoute,
        });
      }
    }

    // Check stop arrivals and advance waypoints
    const completedIds = new Set<string>(current.completedStopIds);
    let nextStop = current.nextStop;
    let nextStopIndex = current.nextStopIndex;
    const items = current.activeDay.items || [];

    const getStopCoords = (item: ItineraryItem | null): [number, number] | null => {
      if (!item) return null;
      const lat = item.place?.latitude ?? item.custom_lat;
      const lng = item.place?.longitude ?? item.custom_lng;
      if (lat !== undefined && lat !== null && lng !== undefined && lng !== null) {
        return [lat, lng];
      }
      return null;
    };

    const nextCoords = getStopCoords(nextStop);
    if (nextStop && nextCoords) {
      const stopDist = haversineDistanceMeters(
        newPos[0],
        newPos[1],
        nextCoords[0],
        nextCoords[1]
      );

      if (stopDist <= this.options.stopArrivalThresholdMeters) {
        completedIds.add(nextStop.id);
        if (nextStopIndex !== null) {
          this.stopReachedSubject.next({ stop: nextStop, index: nextStopIndex });
        }

        // Advance to next uncompleted stop
        const foundNextIdx = items.findIndex(
          (item, idx) =>
            idx > (nextStopIndex ?? -1) && !completedIds.has(item.id)
        );

        if (foundNextIdx >= 0) {
          nextStop = items[foundNextIdx];
          nextStopIndex = foundNextIdx;
        } else {
          nextStop = null;
          nextStopIndex = null;
        }
      }
    }

    // Calculate distance and ETA to next stop
    let distToNextStop: number | null = null;
    let etaSecondsNextStop: number | null = null;

    const currentNextCoords = getStopCoords(nextStop);
    if (nextStop && currentNextCoords) {
      distToNextStop = haversineDistanceMeters(
        newPos[0],
        newPos[1],
        currentNextCoords[0],
        currentNextCoords[1]
      );
      const effectiveSpeed =
        position.coords.speed && position.coords.speed > 1.0
          ? position.coords.speed
          : this.options.averageSpeedMetersPerSec;
      etaSecondsNextStop = Math.round(distToNextStop / effectiveSpeed);
    }

    // Calculate total remaining distance along polyline
    let totalRemainingDist: number | null = null;
    let totalRemainingDuration: number | null = null;

    if (this.activePolylineCoords.length > 1) {
      totalRemainingDist = remainingDistanceAlongPolylineMeters(
        newPos,
        this.activePolylineCoords
      );
      const effectiveSpeed =
        position.coords.speed && position.coords.speed > 1.0
          ? position.coords.speed
          : this.options.averageSpeedMetersPerSec;
      totalRemainingDuration = Math.round(totalRemainingDist / effectiveSpeed);
    }

    this.stateSubject.next({
      ...current,
      currentPosition: newPos,
      heading: position.coords.heading ?? null,
      speed: position.coords.speed ?? null,
      snappedPosition: snappedPos,
      distanceToRouteMeters: distToRoute,
      isOffRoute: isOffRoute,
      nextStop: nextStop,
      nextStopIndex: nextStopIndex,
      distanceToNextStopMeters: distToNextStop,
      etaSecondsToNextStop: etaSecondsNextStop,
      totalRemainingDistanceMeters: totalRemainingDist,
      totalRemainingDurationSeconds: totalRemainingDuration,
      completedStopIds: completedIds,
    });
  }

  /**
   * Triggers a recentering request for Leaflet map views.
   */
  public triggerRecenter(): void {
    const pos = this.currentState.currentPosition;
    if (pos) {
      this.recenterSubject.next(pos);
    }
  }
}
