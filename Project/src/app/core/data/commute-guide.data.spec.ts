import { describe, expect, it } from 'vitest';
import { getCommuteInfoForMunicipality, getLegCommuteInfo, calculateHaversineMeters } from './commute-guide.data';

describe('commute-guide.data', () => {
  it('returns Bongabon commute details matching Figma specification', () => {
    const info = getCommuteInfoForMunicipality('Bongabon');
    expect(info.transitMode).toContain('UV Express');
    expect(info.departureHub).toBe('Cabanatuan City Central Terminal');
    expect(info.dropOffPoint).toContain('Ricky Food House');
    expect(info.estimatedTravelTime).toBe('1 hr – 1 hr 30 mins');
    expect(info.estimatedFare).toBe('₱66 – ₱80');
    expect(info.travelReminder).toContain('UV Express schedules');
  });

  it('resolves General Tinio when given Minalungao place name', () => {
    const info = getCommuteInfoForMunicipality(null, 'Minalungao National Park');
    expect(info.dropOffPoint).toContain('General Tinio');
    expect(info.travelReminder).toContain('Minalungao');
  });

  it('resolves Pantabangan for Highland Bali resort', () => {
    const info = getCommuteInfoForMunicipality('Pantabangan', 'Highland Bali Villas');
    expect(info.departureHub).toBe('Cabanatuan City Central Terminal');
    expect(info.estimatedFare).toBe('₱110 – ₱150');
  });

  it('provides safe fallback for unknown municipalities', () => {
    const info = getCommuteInfoForMunicipality('Talavera');
    expect(info.departureHub).toBe('Cabanatuan City Central Terminal');
    expect(info.dropOffPoint).toContain('Talavera');
  });

  describe('getLegCommuteInfo (ROUTE-05 / 27.3.5)', () => {
    it('returns gateway hub commute for the first stop of the day', () => {
      const stop1 = {
        custom_title: 'Farm Villaronte',
        place: { name: 'Farm Villaronte', municipality_name: 'Pantabangan' },
      };
      const legInfo = getLegCommuteInfo(null, stop1);
      expect(legInfo.departureHub).toBe('Cabanatuan City Central Terminal');
      expect(legInfo.isWalkingDistance).toBe(false);
      expect(legInfo.hopDistanceMeters).toBeNull();
    });

    it('returns walking/short tricycle advice for intra-town hops <= 1.2 km', () => {
      const stop1 = {
        custom_title: 'Lumang Gapan Plaza',
        place: { name: 'Lumang Gapan Plaza', municipality_name: 'Gapan City', latitude: 15.308, longitude: 120.947 },
      };
      const stop2 = {
        custom_title: 'Tagpuan sa Lumang Gapan',
        travel_distance_meters: 450,
        place: { name: 'Tagpuan sa Lumang Gapan', municipality_name: 'Gapan City', latitude: 15.311, longitude: 120.949 },
      };
      const legInfo = getLegCommuteInfo(stop1, stop2);
      expect(legInfo.isWalkingDistance).toBe(true);
      expect(legInfo.transitMode).toContain('Walking');
      expect(legInfo.estimatedFare).toContain('₱15 – ₱25');
      expect(legInfo.hopDistanceMeters).toBe(450);
    });

    it('returns local tricycle advice for medium hops within same municipality', () => {
      const stop1 = {
        custom_title: 'CLSU Main Gate',
        place: { name: 'CLSU Main Gate', municipality_name: 'Science City of Muñoz', latitude: 15.73, longitude: 120.93 },
      };
      const stop2 = {
        custom_title: 'PhilRice Experimental Farm',
        travel_distance_meters: 2800,
        place: { name: 'PhilRice Experimental Farm', municipality_name: 'Science City of Muñoz', latitude: 15.75, longitude: 120.95 },
      };
      const legInfo = getLegCommuteInfo(stop1, stop2);
      expect(legInfo.isWalkingDistance).toBe(false);
      expect(legInfo.transitMode).toBe('Local Tricycle');
      expect(legInfo.estimatedFare).toContain('₱25 – ₱50');
      expect(legInfo.hopDistanceMeters).toBe(2800);
    });

    it('returns inter-town corridor transit for hops across different municipalities', () => {
      const stop1 = {
        custom_title: 'Cabanatuan City Hall',
        place: { name: 'Cabanatuan City Hall', municipality_name: 'Cabanatuan City' },
      };
      const stop2 = {
        custom_title: 'Minalungao National Park',
        travel_distance_meters: 32000,
        place: { name: 'Minalungao National Park', municipality_name: 'General Tinio' },
      };
      const legInfo = getLegCommuteInfo(stop1, stop2);
      expect(legInfo.isWalkingDistance).toBe(false);
      expect(legInfo.transitMode).toContain('Jeepney / UV Express');
      expect(legInfo.estimatedFare).toContain('₱35 – ₱85');
    });

    it('correctly calculates Haversine distance in meters', () => {
      // Cabanatuan to Muñoz (~25 km)
      const dist = calculateHaversineMeters(15.4859, 120.9673, 15.7144, 120.9069);
      expect(dist).toBeGreaterThan(20000);
      expect(dist).toBeLessThan(35000);
    });
  });
});
