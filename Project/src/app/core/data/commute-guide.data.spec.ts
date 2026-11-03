import { describe, expect, it } from 'vitest';
import { getCommuteInfoForMunicipality } from './commute-guide.data';

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
});
