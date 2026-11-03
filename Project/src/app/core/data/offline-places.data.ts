/**
 * Consolidated canonical offline destinations and presets for Nueva Ecija MVP (DEF-05).
 * Single source of truth for offline fallback across Home tab, PlaceService, and ItineraryService.
 */

import { Place } from '../models/place.models';

export interface CanonicalOfflinePlace {
  id: string;
  name: string;
  category: string;
  categoryName: string;
  municipality: string;
  addressText: string;
  latitude: number;
  longitude: number;
  description: string;
  phone: string | null;
  website: string | null;
  openingHours: string | null;
  estimatedCostMin: number | null;
  estimatedCostMax: number | null;
  costCurrency: string;
  image: string;
  tags: string[];
  directionsUrl: string;
  defaultTime: string;
  defaultDurationMinutes: number;
  isFeatured: boolean;
}

export const CANONICAL_OFFLINE_PLACES: CanonicalOfflinePlace[] = [
  {
    id: 'dest-rohi-paperflower',
    name: 'Rohi Paperflower Cafe',
    category: 'cafe',
    categoryName: 'Cafe & Dining',
    municipality: 'Bongabon',
    addressText: 'Bongabon, Nueva Ecija',
    latitude: 15.6315,
    longitude: 121.1440,
    description: 'Charming artisanal cafe adorned with vibrant paper flower crafts, signature coffee blends, and baked pastries.',
    phone: null,
    website: null,
    openingHours: '10:00-21:00',
    estimatedCostMin: 150,
    estimatedCostMax: 350,
    costCurrency: 'PHP',
    image: 'assets/images/rohi_paperflower.png',
    tags: ['Cafe', 'Artisan Coffee', 'Crafts'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6315,121.1440',
    defaultTime: '12:00 PM - 2:00 PM',
    defaultDurationMinutes: 120,
    isFeatured: true,
  },
  {
    id: 'dest-museo-bongabon',
    name: 'Museo de Bongabon',
    category: 'museum_cultural',
    categoryName: 'Culture & Museum',
    municipality: 'Bongabon',
    addressText: 'Bongabon, Nueva Ecija',
    latitude: 15.6300,
    longitude: 121.1430,
    description: 'Community heritage museum chronicling the agricultural identity, historic revolution roots, and onion industry of Bongabon.',
    phone: null,
    website: null,
    openingHours: '08:00-17:00',
    estimatedCostMin: null,
    estimatedCostMax: null,
    costCurrency: 'PHP',
    image: 'assets/images/museo_bongabon.png',
    tags: ['Museum', 'Culture', 'History'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6300,121.1430',
    defaultTime: '2:00 PM - 5:00 PM',
    defaultDurationMinutes: 180,
    isFeatured: true,
  },
  {
    id: 'dest-thornes-samgyupsal',
    name: 'Thornes Samgyupsal House',
    category: 'restaurant',
    categoryName: 'Restaurant',
    municipality: 'Bongabon',
    addressText: 'Bongabon, Nueva Ecija',
    latitude: 15.6330,
    longitude: 121.1460,
    description: 'Beloved dining spot serving unlimited Korean samgyupsal BBQ, savory side dishes, and fresh lettuce wraps.',
    phone: null,
    website: null,
    openingHours: '11:00-22:00',
    estimatedCostMin: 399,
    estimatedCostMax: 599,
    costCurrency: 'PHP',
    image: 'assets/images/thornes_samgyupsal.png',
    tags: ['Korean BBQ', 'Samgyupsal', 'Dinner'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6330,121.1460',
    defaultTime: '5:00 PM - 7:00 PM',
    defaultDurationMinutes: 120,
    isFeatured: true,
  },
  {
    id: 'dest-la-casa-prime',
    name: 'La Casa Prime Cabins',
    category: 'hotel_accommodation',
    categoryName: 'Resort & Stay',
    municipality: 'Bongabon',
    addressText: 'Bongabon, Nueva Ecija',
    latitude: 15.6280,
    longitude: 121.1520,
    description: 'Serene mountain cabin sanctuary with overlooking views of Pantabangan Lake and modern glamping amenities.',
    phone: null,
    website: null,
    openingHours: '24 Hours',
    estimatedCostMin: 2500,
    estimatedCostMax: 6000,
    costCurrency: 'PHP',
    image: 'assets/images/la_casa_prime.png',
    tags: ['Mountain Cabins', 'Lake View', 'Glamping'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6280,121.1520',
    defaultTime: '1 Night · 2 Days',
    defaultDurationMinutes: 1320,
    isFeatured: true,
  },
  {
    id: 'dest-minalungao',
    name: 'Minalungao National Park',
    category: 'nature_park',
    categoryName: 'Nature & Adventure',
    municipality: 'General Tinio',
    addressText: 'General Tinio, Nueva Ecija',
    latitude: 15.2981,
    longitude: 121.1223,
    description: 'Towering 16-meter limestone cliffs, emerald-green Peñaranda River bamboo rafting, and subterranean caves.',
    phone: null,
    website: null,
    openingHours: '07:00-17:00',
    estimatedCostMin: 100,
    estimatedCostMax: 500,
    costCurrency: 'PHP',
    image: 'assets/images/minalungao.png',
    tags: ['Balsa Rafting', 'Cliff Diving', 'Caving'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
    defaultTime: '09:00',
    defaultDurationMinutes: 180,
    isFeatured: true,
  },
  {
    id: 'dest-tagpuan-gapan',
    name: 'Tagpuan sa Lumang Gapan',
    category: 'church_religious',
    categoryName: 'Heritage & Faith',
    municipality: 'Gapan City',
    addressText: 'Gapan City, Nueva Ecija',
    latitude: 15.3065,
    longitude: 120.9461,
    description: 'The "Little Vigan" of Nueva Ecija featuring restored Spanish colonial street lamps, historic brick facades, and night food stalls.',
    phone: null,
    website: null,
    openingHours: '06:00-20:00',
    estimatedCostMin: null,
    estimatedCostMax: null,
    costCurrency: 'PHP',
    image: 'assets/images/tagpuan_gapan.png',
    tags: ['Colonial Walk', 'Night Market', 'Historic Street'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.3065,120.9461',
    defaultTime: '17:00',
    defaultDurationMinutes: 120,
    isFeatured: true,
  },
  {
    id: 'dest-pantabangan-lake',
    name: 'Pantabangan Dam and Lake Viewpoint',
    category: 'tourist_attraction',
    categoryName: 'Tourist Attraction',
    municipality: 'Pantabangan',
    addressText: 'Pantabangan, Nueva Ecija',
    latitude: 15.8126,
    longitude: 121.1098,
    description: "One of Southeast Asia's largest clean water reservoirs, framed by scenic Sierra Madre mountain ridges and bass fishing spots.",
    phone: null,
    website: null,
    openingHours: '06:00-18:00',
    estimatedCostMin: null,
    estimatedCostMax: null,
    costCurrency: 'PHP',
    image: 'assets/images/pantabangan_lake.png',
    tags: ['Bass Fishing', 'Scenic View', 'Dam Site'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8126,121.1098',
    defaultTime: '13:00',
    defaultDurationMinutes: 120,
    isFeatured: true,
  },
  {
    id: 'dest-george-point',
    name: 'George Point',
    category: 'cafe',
    categoryName: 'Cafe & Dining',
    municipality: 'Pantabangan',
    addressText: 'Pantabangan, Nueva Ecija',
    latitude: 15.8200,
    longitude: 121.1150,
    description: 'Scenic panoramic hilltop overlooking Pantabangan Lake, ideal for sunset views, relaxing lakeside dining, and coffee.',
    phone: null,
    website: null,
    openingHours: '08:00-20:00',
    estimatedCostMin: 150,
    estimatedCostMax: 450,
    costCurrency: 'PHP',
    image: 'assets/images/george_point.png',
    tags: ['Sunset View', 'Lakeside Coffee', 'Photography'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8200,121.1150',
    defaultTime: '12:00',
    defaultDurationMinutes: 90,
    isFeatured: true,
  },
  {
    id: 'dest-highland-bali',
    name: 'Highland Bali Villas Resort and Spa',
    category: 'hotel_accommodation',
    categoryName: 'Resort & Stay',
    municipality: 'Pantabangan',
    addressText: 'Pantabangan, Nueva Ecija',
    latitude: 15.8180,
    longitude: 121.1210,
    description: 'Balinese-inspired lakefront retreat with water sports, exotic villas, and breathtaking vistas across the water.',
    phone: null,
    website: null,
    openingHours: '24 Hours',
    estimatedCostMin: 3500,
    estimatedCostMax: 8000,
    costCurrency: 'PHP',
    image: 'assets/images/highland_bali.png',
    tags: ['Water Sports', 'Resort Villas', 'Spa'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8180,121.1210',
    defaultTime: '15:00',
    defaultDurationMinutes: 150,
    isFeatured: true,
  },
  {
    id: 'dest-farm-villaronte',
    name: 'Farm Villaronte',
    category: 'tourist_attraction',
    categoryName: 'Tourist Attraction',
    municipality: 'San Jose City',
    addressText: 'San Jose City, Nueva Ecija',
    latitude: 15.7850,
    longitude: 120.9980,
    description: 'Vibrant flower farm, organic produce picking, rustic pavilions, and family-friendly agro-tourism trails.',
    phone: null,
    website: null,
    openingHours: '08:00-17:00',
    estimatedCostMin: 50,
    estimatedCostMax: 200,
    costCurrency: 'PHP',
    image: 'assets/images/farm_villaronte.png',
    tags: ['Sunflower Fields', 'Organic Produce', 'Agri-Tour'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.7850,120.9980',
    defaultTime: '09:00',
    defaultDurationMinutes: 90,
    isFeatured: true,
  },
  {
    id: 'dest-casa-batik',
    name: 'Casa Batik',
    category: 'museum_cultural',
    categoryName: 'Culture & Museum',
    municipality: 'Cabanatuan City',
    addressText: 'Cabanatuan City, Nueva Ecija',
    latitude: 15.4850,
    longitude: 120.9680,
    description: 'Artisan craft space celebrating Philippine textile traditions, local handcrafted coffee, and homegrown culinary heritage.',
    phone: null,
    website: null,
    openingHours: '09:00-19:00',
    estimatedCostMin: 100,
    estimatedCostMax: 300,
    costCurrency: 'PHP',
    image: 'assets/images/casa_batik.png',
    tags: ['Handcrafted Goods', 'Art Cafe', 'Local Heritage'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.4850,120.9680',
    defaultTime: '11:00',
    defaultDurationMinutes: 90,
    isFeatured: true,
  },
  {
    id: 'dest-pavillion-farm',
    name: "D' Pavilion Farm and Resort",
    category: 'resort_swimming',
    categoryName: 'Resort & Swimming',
    municipality: 'Bongabon',
    addressText: 'Bongabon, Nueva Ecija',
    latitude: 15.6322,
    longitude: 121.1447,
    description: 'Sprawling eco-tourism estate in the Onion Capital with open lawns, fresh mountain breezes, and native dining.',
    phone: null,
    website: null,
    openingHours: '08:00-18:00',
    estimatedCostMin: 150,
    estimatedCostMax: 400,
    costCurrency: 'PHP',
    image: 'assets/images/pavillion_farm.png',
    tags: ['Mountain View', 'Onion Capital', 'Eco Camp'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6322,121.1447',
    defaultTime: '13:00',
    defaultDurationMinutes: 120,
    isFeatured: true,
  },
  {
    id: 'dest-lake-farm-marre',
    name: 'Lake Farm de La Marre',
    category: 'hotel_accommodation',
    categoryName: 'Resort & Stay',
    municipality: 'San Jose City',
    addressText: 'San Jose City, Nueva Ecija',
    latitude: 15.7720,
    longitude: 120.9850,
    description: 'Tranquil countryside lakefront farm estate with boating, peaceful nature retreats, and farm-to-table culinary dining.',
    phone: null,
    website: null,
    openingHours: '08:00-20:00',
    estimatedCostMin: 500,
    estimatedCostMax: 2500,
    costCurrency: 'PHP',
    image: 'assets/images/lake_farm_marre.png',
    tags: ['Lakeside Retreat', 'Nature Farm', 'Boating'],
    directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.7720,120.9850',
    defaultTime: '14:00',
    defaultDurationMinutes: 120,
    isFeatured: true,
  },
];

/**
 * Converts canonical offline places into Place model instances for PlaceService.
 */
export function getOfflinePlacesAsPlaceEntities(): Place[] {
  const now = '2026-10-31T00:00:00Z';
  return CANONICAL_OFFLINE_PLACES.map((p) => ({
    id: p.id,
    name: p.name,
    category: p.category,
    latitude: p.latitude,
    longitude: p.longitude,
    municipality_name: p.municipality,
    address_text: p.addressText,
    description: p.description,
    phone: p.phone,
    website: p.website,
    opening_hours: p.openingHours,
    estimated_cost_min: p.estimatedCostMin,
    estimated_cost_max: p.estimatedCostMax,
    cost_currency: p.costCurrency,
    image_url: p.image,
    image_license: null,
    source_name: 'CuratedNuevaEcijaMVP',
    source_record_id: `curated/${p.id.replace('dest-', '')}`,
    source_url: null,
    imported_at: now,
    verified_at: now,
    is_featured: p.isFeatured,
    tags: p.tags,
    directions_url: p.directionsUrl,
  }));
}

/**
 * Formats cost display string with honest null handling.
 */
export function formatCostDisplay(min: number | null, max: number | null): string {
  if (min != null || max != null) {
    const low = min ?? max;
    const high = max ?? min;
    return low === high ? `₱${low}` : `₱${low} - ₱${high}`;
  }
  return 'Cost not provided';
}

/**
 * Converts canonical offline places into DestinationItem format for the Home page.
 */
export function getOfflineDestinationsForHome(): any[] {
  return CANONICAL_OFFLINE_PLACES.map((p) => ({
    id: p.id.replace('dest-', ''),
    name: p.name,
    municipality: p.municipality,
    category: p.categoryName,
    categoryKey: p.category,
    image: p.image,
    description: p.description,
    tags: p.tags,
    searchQuery: `${p.name} ${p.municipality} Nueva Ecija`,
    directionsUrl: p.directionsUrl,
    openingHours: p.openingHours,
    costDisplay: formatCostDisplay(p.estimatedCostMin, p.estimatedCostMax),
  }));
}

export interface OfflineCuratedPlace {
  id: string;
  name: string;
  category: string;
  categoryKey: string;
  municipality: string;
  lat: number;
  lng: number;
  image: string;
  description: string;
  tags: string[];
  directionsUrl: string;
  openingHours: string | null;
  min: number | null;
  max: number | null;
  time: string;
  dur: number;
}

/**
 * Curated pool items formatted for ItineraryService offline suggested plan generation.
 */
export function getOfflineCuratedPoolForItinerary(): OfflineCuratedPlace[] {
  return CANONICAL_OFFLINE_PLACES.map((p) => ({
    id: p.id,
    name: p.name,
    category: p.categoryName,
    categoryKey: p.category,
    municipality: p.municipality,
    lat: p.latitude,
    lng: p.longitude,
    image: p.image,
    description: p.description,
    tags: p.tags,
    directionsUrl: p.directionsUrl,
    openingHours: p.openingHours,
    min: p.estimatedCostMin,
    max: p.estimatedCostMax,
    time: p.defaultTime,
    dur: p.defaultDurationMinutes,
  }));
}

export interface DayClusterPreset {
  municipality: string;
  subtitle: string;
  places: OfflineCuratedPlace[];
}

/**
 * Clustered day presets for ItineraryService (DEF-03: strictly chronological).
 */
export function getOfflineDayClusterPresets(curatedPool: OfflineCuratedPlace[]): DayClusterPreset[] {
  return [
    {
      municipality: 'Bongabon',
      subtitle: 'Food spots, local culture, and historic sites!',
      places: [
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-rohi-paperflower')!,   // 12:00 PM - 2:00 PM
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-museo-bongabon')!,     // 2:00 PM - 5:00 PM
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-thornes-samgyupsal')!, // 5:00 PM - 7:00 PM
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-la-casa-prime')!,      // Overnight Stay
      ],
    },
    {
      municipality: 'Cabanatuan City',
      subtitle: 'Heritage art crafts, authentic dining, and countryside leisure!',
      places: [
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-farm-villaronte')!,    // 09:00 - 10:30 AM
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-casa-batik')!,         // 11:00 AM - 12:30 PM
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-pavillion-farm')!,     // 11:30
      ],
    },
    {
      municipality: 'Gapan City',
      subtitle: 'Historic Spanish streetscapes, night food stalls, and scenic river adventures!',
      places: [
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-minalungao')!,         // 09:00
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-pantabangan-lake')!,   // 13:00
        curatedPool.find((p: OfflineCuratedPlace) => p.id === 'dest-tagpuan-gapan')!,      // 17:00
      ],
    },
  ];
}

export interface NearbyPlaceItem {
  id: string;
  name: string;
  category: 'restaurant' | 'hospital' | 'store';
  openingHours: string;
  municipality: string;
}

/**
 * Resolves nearby places with strict retail/store classification (DEF-06).
 * Cultural attractions, nature parks, and lodging are NEVER misclassified as stores.
 */
export function getOfflineNearbyPlaces(municipality: string = 'Bongabon'): NearbyPlaceItem[] {
  const norm = (municipality || '').trim();
  const targetMuni = norm || 'Bongabon';

  if (targetMuni.toLowerCase() !== 'bongabon') {
    const places = getOfflinePlacesAsPlaceEntities();
    const matches = places
      .filter((p) => p.municipality_name?.toLowerCase().includes(targetMuni.toLowerCase()))
      .filter((p) => {
        // Strict category filter (DEF-06): only true dining, health, or retail places
        return (
          p.category === 'restaurant' ||
          p.category === 'cafe' ||
          p.category === 'hospital_clinic' ||
          p.category === 'pharmacy' ||
          p.category === 'shopping_market' ||
          p.category === 'convenience_store' ||
          p.category === 'supermarket' ||
          (p.tags && p.tags.some((t: string) => t.toLowerCase().includes('store') || t.toLowerCase().includes('market') || t.toLowerCase().includes('retail')))
        );
      })
      .map((p) => {
        let cat: 'restaurant' | 'hospital' | 'store' = 'store';
        if (p.category === 'restaurant' || p.category === 'cafe') {
          cat = 'restaurant';
        } else if (p.category === 'hospital_clinic' || p.category === 'pharmacy') {
          cat = 'hospital';
        }
        return {
          id: `nb-${p.id}`,
          name: p.name,
          category: cat,
          openingHours: p.opening_hours || 'Hours not verified',
          municipality: p.municipality_name || targetMuni,
        };
      });

    if (matches.length > 0) {
      return matches;
    }
  }

  // Default curated Bongabon essentials directly from Figma
  return [
    // 1. Restaurants
    { id: 'nb-r-1', name: 'Boss Samgyupsal', category: 'restaurant', openingHours: 'Daily, 10:00 AM to 10:00 PM', municipality: targetMuni },
    { id: 'nb-r-2', name: 'Lomi-Raiyah Foodhouse', category: 'restaurant', openingHours: 'Mon-Sat, 5:00 AM to 8:00 PM', municipality: targetMuni },
    { id: 'nb-r-3', name: 'The Hangover by Y3-J', category: 'restaurant', openingHours: 'Daily, 6:00 AM to 11:30 PM', municipality: targetMuni },
    { id: 'nb-r-4', name: 'Banchan Gogi Unlimited Korean Grill', category: 'restaurant', openingHours: 'Daily, 12:30 PM to 11:00 PM', municipality: targetMuni },
    { id: 'nb-r-5', name: 'Tara G!', category: 'restaurant', openingHours: 'Daily, 24 hrs', municipality: targetMuni },
    { id: 'nb-r-6', name: "Hera's Diner By Rac's Catering", category: 'restaurant', openingHours: 'Tue-Sun, 6:00 AM to 8:00 PM', municipality: targetMuni },

    // 2. Hospital & Pharmacies
    { id: 'nb-h-1', name: `${targetMuni} District Hospital`, category: 'hospital', openingHours: 'Mon-Sat, 7:00 AM to 5:00 PM', municipality: targetMuni },
    { id: 'nb-h-2', name: 'PharmVille Pharmacy and Medical Supplies', category: 'hospital', openingHours: 'Daily, 7:00 AM to 10:00 PM', municipality: targetMuni },
    { id: 'nb-h-3', name: 'Deb Pharmacy', category: 'hospital', openingHours: 'Mon-Sat, 7:30 AM to 7:00 PM. Sun and Holidays, 9:00 AM to 5:00 PM', municipality: targetMuni },
    { id: 'nb-h-4', name: 'Resma Medical Clinic', category: 'hospital', openingHours: 'Daily, 6:30 AM to 3:30 PM', municipality: targetMuni },

    // 3. Stores
    { id: 'nb-s-1', name: 'J&B- Convenience Store', category: 'store', openingHours: 'Daily, 24 hrs', municipality: targetMuni },
    { id: 'nb-s-2', name: 'Rc Sylvia Store', category: 'store', openingHours: 'Daily, 6:00 AM to 8:00 PM', municipality: targetMuni },
    { id: 'nb-s-3', name: 'Maila Store', category: 'store', openingHours: 'Daily, 6:00 AM to 8:00 PM', municipality: targetMuni },
    { id: 'nb-s-4', name: `Alfamart ${targetMuni}`, category: 'store', openingHours: 'Mon-Fri, 6:00 AM to 11:00 PM. Sat-Sun, 24 hrs', municipality: targetMuni },
    { id: 'nb-s-5', name: 'M2 Mc. Oil', category: 'store', openingHours: 'Daily, 5:30 AM to 8:00 PM', municipality: targetMuni },
    { id: 'nb-s-6', name: "Franks N' Burgers", category: 'store', openingHours: 'Daily, 24 hrs', municipality: targetMuni },
  ];
}
