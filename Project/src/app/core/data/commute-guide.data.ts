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
