/**
 * Encoded Polyline & Geodesic Distance Utilities for Leaflet and Turn-by-Turn Route Tracking.
 * Implements the standard Google Maps Encoded Polyline Algorithm (precision 5).
 */

/**
 * Decodes a Google Encoded Polyline string into an array of [latitude, longitude] pairs.
 */
export function decodePolyline(encoded: string): Array<[number, number]> {
  const points: Array<[number, number]> = [];
  let index = 0;
  const len = encoded.length;
  let lat = 0;
  let lng = 0;

  while (index < len) {
    let b: number;
    let shift = 0;
    let result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    points.push([lat / 1e5, lng / 1e5]);
  }

  return points;
}

/**
 * Encodes an array of [latitude, longitude] coordinates into Google Encoded Polyline format.
 */
export function encodePolyline(points: Array<[number, number]>): string {
  let result = '';
  let prevLat = 0;
  let prevLng = 0;

  for (const [lat, lng] of points) {
    const latInt = Math.round(lat * 1e5);
    const lngInt = Math.round(lng * 1e5);

    const dLat = latInt - prevLat;
    const dLng = lngInt - prevLng;

    prevLat = latInt;
    prevLng = lngInt;

    for (const d of [dLat, dLng]) {
      let val = d < 0 ? ~(d << 1) : d << 1;
      while (val >= 0x20) {
        result += String.fromCharCode((0x20 | (val & 0x1f)) + 63);
        val >>= 5;
      }
      result += String.fromCharCode(val + 63);
    }
  }

  return result;
}

/**
 * Calculates Great Circle distance between two points in meters using the Haversine formula.
 */
export function haversineDistanceMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000.0; // Earth radius in meters
  const toRad = (deg: number) => (deg * Math.PI) / 180.0;

  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const deltaPhi = toRad(lat2 - lat1);
  const deltaLambda = toRad(lon2 - lon1);

  const a =
    Math.sin(deltaPhi / 2.0) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2.0) ** 2;
  const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));

  return R * c;
}

/**
 * Finds the closest point on segment AB to point P and returns the perpendicular/closest distance in meters.
 */
export function distanceToSegmentMeters(
  point: [number, number],
  segStart: [number, number],
  segEnd: [number, number]
): { distance: number; closestPoint: [number, number]; projectionRatio: number } {
  const [latP, lonP] = point;
  const [latA, lonA] = segStart;
  const [latB, lonB] = segEnd;

  const midLatRad = ((latA + latB) / 2.0) * (Math.PI / 180.0);
  const cosMidLat = Math.cos(midLatRad);

  // Equirectangular local coordinates
  const ax = lonA * cosMidLat;
  const ay = latA;
  const bx = lonB * cosMidLat;
  const by = latB;
  const px = lonP * cosMidLat;
  const py = latP;

  const vx = bx - ax;
  const vy = by - ay;
  const wx = px - ax;
  const wy = py - ay;

  const segLenSq = vx * vx + vy * vy;
  let t = 0;
  if (segLenSq > 1e-12) {
    t = (wx * vx + wy * vy) / segLenSq;
    t = Math.max(0, Math.min(1, t));
  }

  const closestLat = latA + t * (latB - latA);
  const closestLon = lonA + t * (lonB - lonA);
  const dist = haversineDistanceMeters(latP, lonP, closestLat, closestLon);

  return {
    distance: dist,
    closestPoint: [closestLat, closestLon],
    projectionRatio: t,
  };
}

/**
 * Calculates the perpendicular/orthogonal distance from a point to the nearest segment of a polyline.
 * Returns Infinity if polyline has less than 1 coordinate.
 */
export function distanceToPolylineMeters(
  point: [number, number],
  polyline: Array<[number, number]>
): { minDistance: number; nearestSegmentIndex: number; closestPoint: [number, number] } {
  if (!polyline || polyline.length === 0) {
    return { minDistance: Infinity, nearestSegmentIndex: -1, closestPoint: point };
  }
  if (polyline.length === 1) {
    const dist = haversineDistanceMeters(point[0], point[1], polyline[0][0], polyline[0][1]);
    return { minDistance: dist, nearestSegmentIndex: 0, closestPoint: polyline[0] };
  }

  let minDistance = Infinity;
  let nearestSegmentIndex = 0;
  let closestPoint: [number, number] = polyline[0];

  for (let i = 0; i < polyline.length - 1; i++) {
    const res = distanceToSegmentMeters(point, polyline[i], polyline[i + 1]);
    if (res.distance < minDistance) {
      minDistance = res.distance;
      nearestSegmentIndex = i;
      closestPoint = res.closestPoint;
    }
  }

  return { minDistance, nearestSegmentIndex, closestPoint };
}

/**
 * Computes the remaining distance along the polyline from the current location to the route end.
 */
export function remainingDistanceAlongPolylineMeters(
  point: [number, number],
  polyline: Array<[number, number]>
): number {
  if (!polyline || polyline.length < 2) {
    return 0;
  }

  const snap = distanceToPolylineMeters(point, polyline);
  if (snap.nearestSegmentIndex < 0) {
    return 0;
  }

  // Distance from closest snapped point to end of current segment
  let remaining = haversineDistanceMeters(
    snap.closestPoint[0],
    snap.closestPoint[1],
    polyline[snap.nearestSegmentIndex + 1][0],
    polyline[snap.nearestSegmentIndex + 1][1]
  );

  // Sum all subsequent segments
  for (let i = snap.nearestSegmentIndex + 1; i < polyline.length - 1; i++) {
    remaining += haversineDistanceMeters(
      polyline[i][0],
      polyline[i][1],
      polyline[i + 1][0],
      polyline[i + 1][1]
    );
  }

  return remaining;
}
