/**
 * Centralized Date Utilities (CR-007)
 *
 * Prevents UTC off-by-one calendar day shifts. Standard JavaScript
 * `new Date("YYYY-MM-DD")` parses as UTC midnight (00:00:00Z), causing
 * local timezones (such as Philippine Standard Time UTC+8 or US Pacific UTC-8)
 * to exhibit off-by-one day bugs when reading or formatting dates.
 */

/**
 * Returns a `YYYY-MM-DD` string in the local timezone.
 */
export function toLocalIsoDate(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Parses a `YYYY-MM-DD` string into a local Date object anchored at 00:00:00 local time.
 */
export function parseLocalIsoDate(dateStr: string): Date {
  if (!dateStr) return new Date();
  const cleanStr = dateStr.includes('T') ? dateStr.split('T')[0] : dateStr;
  const parts = cleanStr.split('-');
  if (parts.length !== 3) {
    return new Date(dateStr);
  }
  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);
  return new Date(year, month, day, 0, 0, 0, 0);
}

/**
 * Adds calendar days in local time, returning a new Date object.
 */
export function addDaysLocal(date: Date, days: number): Date {
  const result = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0, 0);
  result.setDate(result.getDate() + days);
  return result;
}

/**
 * Calculates the inclusive number of calendar days between two ISO date strings.
 */
export function diffDaysLocal(startStr: string, endStr: string): number {
  if (!startStr || !endStr) return 1;
  const start = parseLocalIsoDate(startStr);
  const end = parseLocalIsoDate(endStr);
  const diffTime = end.getTime() - start.getTime();
  if (diffTime < 0) return 1;
  return Math.round(diffTime / (1000 * 60 * 60 * 24)) + 1;
}

/**
 * Formats a start and end date into a user-friendly display range.
 */
export function formatDateRange(startStr: string, endStr: string): string {
  if (!startStr || !endStr) return '';
  const start = parseLocalIsoDate(startStr);
  const end = parseLocalIsoDate(endStr);

  const startMonth = start.toLocaleDateString('en-US', { month: 'short' });
  const endMonth = end.toLocaleDateString('en-US', { month: 'short' });
  const startYear = start.getFullYear();
  const endYear = end.getFullYear();
  const startDay = start.getDate();
  const endDay = end.getDate();

  if (startYear !== endYear) {
    return `${startMonth} ${startDay}, ${startYear} – ${endMonth} ${endDay}, ${endYear}`;
  }
  if (startMonth === endMonth && startDay === endDay) {
    return `${startMonth} ${startDay}, ${startYear}`;
  }
  if (startMonth === endMonth) {
    return `${startMonth} ${startDay} – ${endDay}, ${startYear}`;
  }
  return `${startMonth} ${startDay} – ${endMonth} ${endDay}, ${startYear}`;
}

