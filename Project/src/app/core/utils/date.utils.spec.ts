import { describe, expect, it } from 'vitest';
import {
  addDaysLocal,
  diffDaysLocal,
  formatDateRange,
  parseLocalIsoDate,
  toLocalIsoDate,
} from './date.utils';

describe('Date Utilities (CR-007)', () => {
  it('formats local date into YYYY-MM-DD string accurately without UTC shift', () => {
    const testDate = new Date(2026, 10, 5, 23, 30, 0); // Nov 5, 2026, 11:30 PM local
    expect(toLocalIsoDate(testDate)).toBe('2026-11-05');

    const morningDate = new Date(2026, 10, 5, 0, 15, 0); // Nov 5, 2026, 12:15 AM local
    expect(toLocalIsoDate(morningDate)).toBe('2026-11-05');
  });

  it('parses YYYY-MM-DD into local Date object without off-by-one error', () => {
    const parsed = parseLocalIsoDate('2026-11-05');
    expect(parsed.getFullYear()).toBe(2026);
    expect(parsed.getMonth()).toBe(10); // November (0-indexed)
    expect(parsed.getDate()).toBe(5);
    expect(parsed.getHours()).toBe(0);
    expect(parsed.getMinutes()).toBe(0);
  });

  it('adds calendar days across month boundaries in local time', () => {
    const start = parseLocalIsoDate('2026-10-31');
    const nextDay = addDaysLocal(start, 1);
    expect(toLocalIsoDate(nextDay)).toBe('2026-11-01');

    const plusFive = addDaysLocal(start, 5);
    expect(toLocalIsoDate(plusFive)).toBe('2026-11-05');
  });

  it('calculates inclusive calendar day differences', () => {
    expect(diffDaysLocal('2026-11-01', '2026-11-01')).toBe(1);
    expect(diffDaysLocal('2026-11-01', '2026-11-03')).toBe(3);
    expect(diffDaysLocal('2026-10-30', '2026-11-01')).toBe(3);
    expect(diffDaysLocal('2026-11-03', '2026-11-01')).toBe(1); // Guard against negative diff
  });

  it('formats friendly date ranges correctly', () => {
    expect(formatDateRange('2026-11-01', '2026-11-01')).toBe('Nov 1, 2026');
    expect(formatDateRange('2026-11-01', '2026-11-03')).toBe('Nov 1 – 3, 2026');
    expect(formatDateRange('2026-10-30', '2026-11-02')).toBe('Oct 30 – Nov 2, 2026');
    expect(formatDateRange('2026-12-30', '2027-01-02')).toBe('Dec 30, 2026 – Jan 2, 2027');
  });
});

