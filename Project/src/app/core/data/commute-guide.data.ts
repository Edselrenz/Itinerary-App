export interface CommuteInfo {
  transitMode: string;
  departureHub: string;
  dropOffPoint: string;
  estimatedTravelTime: string;
  estimatedFare: string;
  travelReminder: string;
}

const COMMUTE_BY_MUNICIPALITY: Record<string, CommuteInfo> = {
  Bongabon: {
    transitMode: 'By Bus / UV Express',
    departureHub: 'Cabanatuan City Central Terminal',
    dropOffPoint: 'Ricky Food House / Bongabon Town Proper',
    estimatedTravelTime: '1 hr – 1 hr 30 mins',
    estimatedFare: '₱66 – ₱80',
    travelReminder:
      'Tricycle transfer fares and UV Express schedules may vary by time of day. Morning departures (6:00 AM – 9:00 AM) run frequently.',
  },
  Pantabangan: {
    transitMode: 'By UV Express / Bus (Baler / Pantabangan route)',
    departureHub: 'Cabanatuan City Central Terminal',
    dropOffPoint: 'Pantabangan Junction / Lake Resort Crossing',
    estimatedTravelTime: '1 hr 30 mins – 2 hrs',
    estimatedFare: '₱110 – ₱150',
    travelReminder:
      'Resorts around Lake Pantabangan and Highland Bali may require a local chartered tricycle or resort shuttle from the highway junction.',
  },
  'General Tinio': {
    transitMode: 'By Jeepney / Tricycle',
    departureHub: 'Gapan City Terminal or Cabanatuan Central Terminal',
    dropOffPoint: 'General Tinio Municipal Hall / Minalungao Tourism Center',
    estimatedTravelTime: '1 hr – 1 hr 20 mins',
    estimatedFare: '₱50 – ₱75',
    travelReminder:
      'Access to Minalungao National Park requires a local chartered tricycle from General Tinio poblacion. Standard local rates apply.',
  },
  'Gapan City': {
    transitMode: 'By Bus (Five Star, Baliwag Transit) / Jeepney',
    departureHub: 'Cabanatuan Central Terminal or Metro Manila Cubao/Pasay',
    dropOffPoint: 'Gapan City Proper / Lumang Gapan Plaza',
    estimatedTravelTime: '30 mins – 45 mins from Cabanatuan',
    estimatedFare: '₱40 – ₱60',
    travelReminder:
      'Walking distance to Tagpuan sa Lumang Gapan from the municipal plaza. Tricycles readily available at the national highway crossing.',
  },
  'Science City of Muñoz': {
    transitMode: 'By Bus / Jeepney (San Jose route)',
    departureHub: 'Cabanatuan City Central Terminal',
    dropOffPoint: 'CLSU Main Gate / Muñoz Public Market',
    estimatedTravelTime: '45 mins – 1 hr',
    estimatedFare: '₱50 – ₱70',
    travelReminder:
      'CLSU agricultural research centers, PCC carabao dairy center, and PhilRice are reachable via local campus tricycles.',
  },
  'Cabanatuan City': {
    transitMode: 'By City Tricycle / Jeepney',
    departureHub: 'Within Cabanatuan City',
    dropOffPoint: 'Destination landmark / City Proper',
    estimatedTravelTime: '10 mins – 25 mins',
    estimatedFare: '₱15 – ₱30',
    travelReminder:
      'Cabanatuan City serves as the primary transport gateway for Nueva Ecija with direct inter-provincial bus connections to Metro Manila and northern provinces.',
  },
  Gabaldon: {
    transitMode: 'By Bus / Van (Dingalan / Gabaldon line)',
    departureHub: 'Cabanatuan City Central Terminal',
    dropOffPoint: 'Gabaldon Poblacion / Dupinga Crossing',
    estimatedTravelTime: '1 hr 30 mins – 2 hrs',
    estimatedFare: '₱90 – ₱120',
    travelReminder:
      'Dupinga River ecotourism site is accessible by tricycle from the town proper. Bring cash as ATMs are limited.',
  },
  'San Jose City': {
    transitMode: 'By Bus / UV Express',
    departureHub: 'Cabanatuan City Central Terminal',
    dropOffPoint: 'San Jose City Public Market / Bus Stop',
    estimatedTravelTime: '1 hr – 1 hr 15 mins',
    estimatedFare: '₱70 – ₱95',
    travelReminder:
      'Gateway to Northern Luzon. Major transit stop with frequent 24-hour bus services along Maharlika Highway.',
  },
};

export function getCommuteInfoForMunicipality(
  municipalityName: string | null | undefined,
  placeName?: string | null
): CommuteInfo {
  const muni = (municipalityName || '').trim();

  // Check normalized match
  if (muni) {
    for (const [key, value] of Object.entries(COMMUTE_BY_MUNICIPALITY)) {
      if (muni.toLowerCase().includes(key.toLowerCase()) || key.toLowerCase().includes(muni.toLowerCase())) {
        return value;
      }
    }
  }

  // Check if placeName gives a hint
  const place = (placeName || '').toLowerCase();
  if (place.includes('minalungao')) {
    return COMMUTE_BY_MUNICIPALITY['General Tinio'];
  }
  if (place.includes('pantabangan') || place.includes('highland bali')) {
    return COMMUTE_BY_MUNICIPALITY['Pantabangan'];
  }
  if (place.includes('lumang gapan')) {
    return COMMUTE_BY_MUNICIPALITY['Gapan City'];
  }
  if (place.includes('clsu') || place.includes('philrice') || place.includes('muñoz') || place.includes('munoz')) {
    return COMMUTE_BY_MUNICIPALITY['Science City of Muñoz'];
  }
  if (place.includes('bongabon')) {
    return COMMUTE_BY_MUNICIPALITY['Bongabon'];
  }

  const label = muni || 'Nueva Ecija';
  return {
    transitMode: 'By Bus / Local UV Express',
    departureHub: 'Cabanatuan City Central Terminal',
    dropOffPoint: `${label} Town Proper / Highway Crossing`,
    estimatedTravelTime: '45 mins – 1 hr 30 mins',
    estimatedFare: '₱50 – ₱100',
    travelReminder:
      'Provincial PUVs depart regularly from Cabanatuan Central Terminal. Check with local terminal marshals for schedule adjustments and night trips.',
  };
}

export interface LegCommuteInfo extends CommuteInfo {
  isWalkingDistance: boolean;
  hopDistanceMeters?: number | null;
}

/**
 * Calculates Haversine distance in meters between two coordinates.
 */
export function calculateHaversineMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371e3; // Earth radius in meters
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

/**
 * Leg-Aware Provincial Commute Guidance (Phase 27.3.5 / ROUTE-05).
 * Computes specific transit and cost guidance between consecutive itinerary stops:
 * - Intra-town hops (<= 1.2 km): walk or local tricycle (₱15–₱25)
 * - Intra-municipality hops (> 1.2 km): local chartered tricycle (₱25–₱50)
 * - Inter-town corridors: provincial PUV/jeepney/bus (₱35–₱85)
 * - First stop: gateway commute from provincial transit hubs
 */
export function getLegCommuteInfo(
  prevStop: any | null | undefined,
  currStop: any
): LegCommuteInfo {
  const currTitle = currStop?.place?.name || currStop?.custom_title || 'Destination';
  const currMuni = currStop?.place?.municipality_name || 'Nueva Ecija';

  if (!prevStop) {
    const base = getCommuteInfoForMunicipality(currMuni, currTitle);
    return {
      ...base,
      isWalkingDistance: false,
      hopDistanceMeters: null,
    };
  }

  const prevTitle = prevStop?.place?.name || prevStop?.custom_title || 'Previous Stop';
  const prevMuni = prevStop?.place?.municipality_name || currMuni;

  // Determine distance
  let distMeters: number | null = currStop?.travel_distance_meters ?? null;
  if (distMeters == null) {
    const pLat = prevStop?.place?.latitude ?? prevStop?.custom_lat;
    const pLng = prevStop?.place?.longitude ?? prevStop?.custom_lng;
    const cLat = currStop?.place?.latitude ?? currStop?.custom_lat;
    const cLng = currStop?.place?.longitude ?? currStop?.custom_lng;
    if (pLat != null && pLng != null && cLat != null && cLng != null) {
      distMeters = calculateHaversineMeters(pLat, pLng, cLat, cLng);
    }
  }

  const isIntraTown = prevMuni.toLowerCase() === currMuni.toLowerCase();

  // Intra-town short hop (<= 1.2 km)
  if (distMeters != null && distMeters <= 1200) {
    const isVeryShort = distMeters <= 400;
    return {
      transitMode: isVeryShort ? 'Walking' : 'Walking or Short Tricycle Hop',
      departureHub: prevTitle,
      dropOffPoint: currTitle,
      estimatedTravelTime: isVeryShort
        ? '3 – 5 mins walk'
        : `${Math.round(distMeters / 80)} mins walk or 3 mins tricycle`,
      estimatedFare: isVeryShort ? 'Free (Walking)' : 'Free (Walk) or ₱15 – ₱25 tricycle',
      travelReminder:
        'Short distance within town proper. Walking is scenic and pleasant, or flag a passing tricycle.',
      isWalkingDistance: true,
      hopDistanceMeters: distMeters,
    };
  }

  // Intra-town medium hop (> 1.2 km within same municipality or short distance)
  if (isIntraTown || (distMeters != null && distMeters < 5000)) {
    const dKm = distMeters != null ? (distMeters / 1000).toFixed(1) : '3';
    return {
      transitMode: 'Local Tricycle',
      departureHub: `${prevTitle} (${prevMuni})`,
      dropOffPoint: `${currTitle} (${currMuni})`,
      estimatedTravelTime: `${Math.max(5, Math.round((distMeters ?? 3000) / 400))} – ${Math.max(10, Math.round((distMeters ?? 3000) / 250))} mins`,
      estimatedFare: '₱25 – ₱50 per ride',
      travelReminder: `Intra-town transfer (${dKm} km). Local tricycles are readily stationed nearby or hailable along the road.`,
      isWalkingDistance: false,
      hopDistanceMeters: distMeters,
    };
  }

  // Inter-town corridor hop
  const dKm = distMeters != null ? (distMeters / 1000).toFixed(1) : '15';
  return {
    transitMode: 'Jeepney / UV Express / Inter-Town Bus',
    departureHub: `${prevMuni} Town Proper / Highway`,
    dropOffPoint: `${currMuni} Crossing / ${currTitle}`,
    estimatedTravelTime: `${Math.max(20, Math.round((distMeters ?? 15000) / 700))} – ${Math.max(30, Math.round((distMeters ?? 15000) / 450))} mins`,
    estimatedFare: '₱35 – ₱85',
    travelReminder: `Inter-municipal corridor (${dKm} km from ${prevMuni} to ${currMuni}). Ride passing public utility jeepneys, buses, or UV Express along Maharlika / provincial highways.`,
    isWalkingDistance: false,
    hopDistanceMeters: distMeters,
  };
}
