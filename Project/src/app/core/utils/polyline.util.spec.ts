import { describe, it, expect } from 'vitest';
import {
  decodePolyline,
  encodePolyline,
  haversineDistanceMeters,
  distanceToSegmentMeters,
  distanceToPolylineMeters,
  remainingDistanceAlongPolylineMeters,
} from './polyline.util';

describe('polyline.util', () => {
  it('should encode and decode coordinates reversibly with precision 5', () => {
    const coords: Array<[number, number]> = [
      [15.4859, 120.9669],
      [15.5414, 121.0844],
      [15.7167, 121.05],
    ];

    const encoded = encodePolyline(coords);
    expect(typeof encoded).toBe('string');
    expect(encoded.length).toBeGreaterThan(0);

    const decoded = decodePolyline(encoded);
    expect(decoded.length).toBe(3);
    for (let i = 0; i < coords.length; i++) {
      expect(decoded[i][0]).toBeCloseTo(coords[i][0], 4);
      expect(decoded[i][1]).toBeCloseTo(coords[i][1], 4);
    }
  });

  it('should compute accurate Haversine distance between Nueva Ecija towns', () => {
    // Cabanatuan to Palayan is ~14 km
    const dist = haversineDistanceMeters(15.4859, 120.9669, 15.5414, 121.0844);
    expect(dist).toBeGreaterThan(13000);
    expect(dist).toBeLessThan(16000);

    // Identical coordinates should be 0
    expect(haversineDistanceMeters(15.0, 121.0, 15.0, 121.0)).toBe(0);
  });

  it('should accurately calculate distance to segment and snapping point', () => {
    const segStart: [number, number] = [15.0, 120.0];
    const segEnd: [number, number] = [15.0, 121.0];

    // Point exactly on midpoint
    const midPoint: [number, number] = [15.0, 120.5];
    const resMid = distanceToSegmentMeters(midPoint, segStart, segEnd);
    expect(resMid.distance).toBeLessThan(5); // ~0 meters
    expect(resMid.projectionRatio).toBeCloseTo(0.5, 2);

    // Point slightly north of midpoint (15.001 is ~111 meters north)
    const northPoint: [number, number] = [15.001, 120.5];
    const resNorth = distanceToSegmentMeters(northPoint, segStart, segEnd);
    expect(resNorth.distance).toBeGreaterThan(100);
    expect(resNorth.distance).toBeLessThan(125);
    expect(resNorth.closestPoint[0]).toBeCloseTo(15.0, 5);
    expect(resNorth.closestPoint[1]).toBeCloseTo(120.5, 4);

    // Point beyond end (clamped to end)
    const pastEnd: [number, number] = [15.0, 121.5];
    const resPast = distanceToSegmentMeters(pastEnd, segStart, segEnd);
    expect(resPast.projectionRatio).toBe(1.0);
    expect(resPast.closestPoint[0]).toBe(15.0);
    expect(resPast.closestPoint[1]).toBe(121.0);
  });

  it('should calculate distance to polyline and detect off-route', () => {
    const polyline: Array<[number, number]> = [
      [15.4859, 120.9669],
      [15.5414, 121.0844],
      [15.7167, 121.05],
    ];

    // Point exactly on first waypoint
    const onStart = distanceToPolylineMeters([15.4859, 120.9669], polyline);
    expect(onStart.minDistance).toBeLessThan(1);

    // Point far away (> 5km)
    const farAway = distanceToPolylineMeters([16.0, 120.0], polyline);
    expect(farAway.minDistance).toBeGreaterThan(50000);
  });

  it('should calculate remaining distance along polyline', () => {
    const polyline: Array<[number, number]> = [
      [15.0, 120.0],
      [15.0, 121.0],
      [15.0, 122.0],
    ];

    // Starting at beginning
    const totalRemaining = remainingDistanceAlongPolylineMeters([15.0, 120.0], polyline);
    expect(totalRemaining).toBeGreaterThan(200000);

    // Midway on second segment
    const halfRemaining = remainingDistanceAlongPolylineMeters([15.0, 121.5], polyline);
    expect(halfRemaining).toBeLessThan(totalRemaining);
    expect(halfRemaining).toBeGreaterThan(40000);
  });
});
