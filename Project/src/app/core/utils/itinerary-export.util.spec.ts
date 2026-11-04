import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  generateIcsCalendar,
  downloadIcsFile,
  generateTextSummary,
  copyTextSummary,
  shareNativeItinerary,
  triggerPrintItinerary,
} from './itinerary-export.util';
import type { Itinerary } from '../models/itinerary.models';

describe('itinerary-export.util', () => {
  const mockItinerary: Itinerary = {
    id: 'itin-exp-1',
    user_id: 'user-1',
    title: 'Bongabon Agro-Eco Trip',
    destination: 'Bongabon',
    start_date: '2026-11-10',
    end_date: '2026-11-12',
    daily_budget: 3000,
    preferences: ['Food Trip', 'Culture & History'],
    type: 'suggested',
    assumptions: ['Pacing: 2 to 3 stops per day', 'Clustering: Clustered around Bongabon'],
    created_at: '2026-11-04T00:00:00Z',
    days: [
      {
        id: 'day-1',
        itinerary_id: 'itin-exp-1',
        day_number: 1,
        travel_date: '2026-11-10',
        title: 'Bongabon',
        items: [
          {
            id: 'item-1',
            day_id: 'day-1',
            sort_order: 1,
            planned_time: '09:00:00',
            duration_minutes: 120,
            notes: 'Morning heritage visit',
            place: {
              id: 'place-1',
              name: 'Camp Pangatian War Memorial Shrine',
              municipality_name: 'Cabanatuan City',
              category: 'Historical',
              estimated_cost_min: 50,
            } as any,
          },
          {
            id: 'item-2',
            day_id: 'day-1',
            sort_order: 2,
            planned_time: '12:00:00',
            duration_minutes: 90,
            notes: 'Lunch at local dining',
            custom_title: 'Bongabon Local Diner',
          },
        ],
      },
      {
        id: 'day-2',
        itinerary_id: 'itin-exp-1',
        day_number: 2,
        travel_date: '2026-11-11',
        title: 'Bongabon',
        items: [],
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('generateIcsCalendar', () => {
    it('generates valid RFC 5545 iCalendar content', () => {
      const ics = generateIcsCalendar(mockItinerary);
      expect(ics).toContain('BEGIN:VCALENDAR');
      expect(ics).toContain('VERSION:2.0');
      expect(ics).toContain('PRODID:-//Nueva Ecija Travel App//Trip Mo Trip Ko//EN');
      expect(ics).toContain('X-WR-CALNAME:Trip to Bongabon');
      expect(ics).toContain('BEGIN:VEVENT');
      expect(ics).toContain('SUMMARY:Camp Pangatian War Memorial Shrine (Day 1)');
      expect(ics).toContain('SUMMARY:Bongabon Local Diner (Day 1)');
      expect(ics).toContain('LOCATION:Camp Pangatian War Memorial Shrine');
      expect(ics).toContain('END:VEVENT');
      expect(ics).toContain('END:VCALENDAR');
    });

    it('handles null or empty itinerary safely', () => {
      expect(generateIcsCalendar(null as any)).toBe('');
    });
  });

  describe('downloadIcsFile', () => {
    it('triggers link download on browser', () => {
      const createObjectURLMock = vi.fn().mockReturnValue('blob:test');
      const revokeObjectURLMock = vi.fn();
      globalThis.URL.createObjectURL = createObjectURLMock;
      globalThis.URL.revokeObjectURL = revokeObjectURLMock;

      const clickMock = vi.fn();
      const appendChildSpy = vi.spyOn(document.body, 'appendChild');
      const removeChildSpy = vi.spyOn(document.body, 'removeChild');

      const originalCreateElement = document.createElement.bind(document);
      vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        const el = originalCreateElement(tagName);
        if (tagName === 'a') {
          el.click = clickMock;
        }
        return el;
      });

      const result = downloadIcsFile(mockItinerary);
      expect(result).toBe(true);
      expect(clickMock).toHaveBeenCalled();
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();
    });
  });

  describe('generateTextSummary', () => {
    it('produces formatted readable itinerary overview', () => {
      const text = generateTextSummary(mockItinerary);
      expect(text).toContain('🌟 Bongabon Agro-Eco Trip');
      expect(text).toContain('📍 Destination: Bongabon, Nueva Ecija');
      expect(text).toContain('📅 Duration: 2 days');
      expect(text).toContain('💰 Target Budget: ₱3,000/day');
      expect(text).toContain('Day 1 - Bongabon:');
      expect(text).toContain('9:00 AM - Camp Pangatian War Memorial Shrine (Cabanatuan City)');
      expect(text).toContain('12:00 PM - Bongabon Local Diner');
      expect(text).toContain('Day 2 - Bongabon:');
      expect(text).toContain('Free day / Open exploration');
      expect(text).toContain('📌 Practical Field Notes:');
      expect(text).toContain('Pacing: 2 to 3 stops per day');
    });

    it('returns empty string on null itinerary', () => {
      expect(generateTextSummary(null as any)).toBe('');
    });
  });

  describe('copyTextSummary', () => {
    it('copies to clipboard via navigator.clipboard', async () => {
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
      });

      const success = await copyTextSummary(mockItinerary);
      expect(success).toBe(true);
      expect(writeTextMock).toHaveBeenCalledWith(expect.stringContaining('Bongabon Agro-Eco Trip'));
    });
  });

  describe('shareNativeItinerary', () => {
    it('invokes navigator.share if available', async () => {
      const shareMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        share: shareMock,
      });

      const shared = await shareNativeItinerary(mockItinerary);
      expect(shared).toBe(true);
      expect(shareMock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Bongabon Agro-Eco Trip',
        })
      );
    });

    it('returns false if navigator.share rejects or fails', async () => {
      const shareMock = vi.fn().mockRejectedValue(new Error('User cancelled'));
      Object.assign(navigator, {
        share: shareMock,
      });

      const shared = await shareNativeItinerary(mockItinerary);
      expect(shared).toBe(false);
    });
  });

  describe('triggerPrintItinerary', () => {
    it('calls window.print', () => {
      const printMock = vi.fn();
      window.print = printMock;

      triggerPrintItinerary();
      expect(printMock).toHaveBeenCalled();
    });
  });
});
