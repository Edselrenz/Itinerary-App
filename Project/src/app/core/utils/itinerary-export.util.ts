/**
 * Itinerary Export Utility (UI-23)
 * Provides RFC 5545 .ics Calendar export, clipboard text summary,
 * Web Share API integration, and print formatting for Nueva Ecija trips.
 */

import type { Itinerary, ItineraryDay, ItineraryItem } from '../models/itinerary.models';

/**
 * Formats a Date object to RFC 5545 ICS timestamp (YYYYMMDDTHHMMSS).
 */
function formatIcsDateTime(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());
  return `${year}${month}${day}T${hours}${minutes}${seconds}`;
}

/**
 * Parses time string (e.g. "09:00:00", "14:30") into hour and minute.
 */
function parseTimeString(timeStr?: string | null): { hours: number; minutes: number } {
  if (!timeStr) {
    return { hours: 9, minutes: 0 };
  }
  const parts = String(timeStr).split(':');
  const hours = parseInt(parts[0], 10) || 9;
  const minutes = parseInt(parts[1], 10) || 0;
  return { hours, minutes };
}

/**
 * Generates valid RFC 5545 iCalendar (.ics) string representation of an itinerary.
 */
export function generateIcsCalendar(itinerary: Itinerary): string {
  if (!itinerary) {
    return '';
  }

  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Nueva Ecija Travel App//Trip Mo Trip Ko//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    `X-WR-CALNAME:Trip to ${itinerary.destination || 'Nueva Ecija'}`,
  ];

  const nowIcs = formatIcsDateTime(new Date()) + 'Z';

  // Base trip start date or tomorrow
  let baseDate = new Date();
  baseDate.setDate(baseDate.getDate() + 1);
  baseDate.setHours(0, 0, 0, 0);

  if (itinerary.start_date) {
    const parsedStart = new Date(itinerary.start_date);
    if (!isNaN(parsedStart.getTime())) {
      baseDate = parsedStart;
    }
  }

  const days: ItineraryDay[] = Array.isArray(itinerary.days) ? itinerary.days : [];

  for (const day of days) {
    const dayOffset = (day.day_number || 1) - 1;
    const dayDate = new Date(baseDate.getTime());
    dayDate.setDate(dayDate.getDate() + dayOffset);

    const items: ItineraryItem[] = Array.isArray(day.items) ? day.items : [];

    for (const item of items) {
      const { hours, minutes } = parseTimeString(item.planned_time);
      const startDt = new Date(dayDate.getTime());
      startDt.setHours(hours, minutes, 0, 0);

      const durationHours = typeof item.duration_minutes === 'number' && item.duration_minutes > 0
        ? (item.duration_minutes / 60)
        : 2;

      const endDt = new Date(startDt.getTime() + durationHours * 3600 * 1000);

      const uid = `ne-itin-${item.id || Math.random().toString(36).substring(2, 9)}@nuevaecijatravel.ph`;
      const location = [
        item.place?.name || item.custom_title || 'Destination Stop',
        item.place?.municipality_name || itinerary.destination || 'Nueva Ecija',
        'Nueva Ecija, Philippines',
      ].filter(Boolean).join(', ');

      const summary = `${item.place?.name || item.custom_title || 'Travel Stop'} (Day ${day.day_number})`;
      const description = [
        item.notes || '',
        item.place?.category ? `Category: ${item.place.category}` : '',
        item.place?.estimated_cost_min ? `Est. Cost: ₱${item.place.estimated_cost_min}` : '',
      ].filter(Boolean).join(' | ');

      lines.push(
        'BEGIN:VEVENT',
        `UID:${uid}`,
        `DTSTAMP:${nowIcs}`,
        `DTSTART:${formatIcsDateTime(startDt)}`,
        `DTEND:${formatIcsDateTime(endDt)}`,
        `SUMMARY:${summary.replace(/,/g, '\\,')}`,
        `LOCATION:${location.replace(/,/g, '\\,')}`,
        `DESCRIPTION:${description.replace(/\n/g, '\\n')}`,
        'STATUS:CONFIRMED',
        'END:VEVENT'
      );
    }
  }

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

/**
 * Triggers a client-side file download of the itinerary as an .ics file.
 */
export function downloadIcsFile(itinerary: Itinerary): boolean {
  try {
    const icsContent = generateIcsCalendar(itinerary);
    if (!icsContent) return false;

    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const filename = `${(itinerary.destination || 'nueva-ecija').toLowerCase().replace(/\s+/g, '-')}-itinerary.ics`;

    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(link.href);
    return true;
  } catch {
    return false;
  }
}

/**
 * Formats time string to 12-hour AM/PM format (e.g. "09:00:00" -> "9:00 AM").
 */
function formatHumanTime(timeStr?: string | null): string {
  if (!timeStr) return '';
  const parts = String(timeStr).split(':');
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10) || 0;
  if (isNaN(h)) return String(timeStr);
  const period = h >= 12 ? 'PM' : 'AM';
  const displayH = h % 12 || 12;
  const displayM = m < 10 ? `0${m}` : `${m}`;
  return `${displayH}:${displayM} ${period}`;
}

/**
 * Generates an editorial text summary of the itinerary suitable for SMS, Viber, WhatsApp.
 */
export function generateTextSummary(itinerary: Itinerary): string {
  if (!itinerary) return '';

  const days: ItineraryDay[] = Array.isArray(itinerary.days) ? itinerary.days : [];
  const totalDays = days.length || 1;
  const destination = itinerary.destination || 'Nueva Ecija';
  const title = itinerary.title || `${destination} Travel Itinerary`;

  let out = `🌟 ${title}\n`;
  out += `📍 Destination: ${destination}, Nueva Ecija\n`;
  out += `📅 Duration: ${totalDays} ${totalDays === 1 ? 'day' : 'days'}\n`;

  if (itinerary.start_date) {
    out += `🗓️ Dates: ${itinerary.start_date}${itinerary.end_date ? ' to ' + itinerary.end_date : ''}\n`;
  }

  if (itinerary.daily_budget) {
    out += `💰 Target Budget: ₱${itinerary.daily_budget.toLocaleString()}/day\n`;
  }

  if (itinerary.preferences && itinerary.preferences.length > 0) {
    out += `🏷️ Highlights: ${itinerary.preferences.join(', ')}\n`;
  }

  out += `\n📋 DAY-BY-DAY SCHEDULE:\n`;

  for (const day of days) {
    const dayLabel = day.title
      ? (day.title.toLowerCase().startsWith(`day ${day.day_number}`)
          ? day.title
          : `Day ${day.day_number} - ${day.title}`)
      : `Day ${day.day_number}`;
    out += `\n${dayLabel}:\n`;
    const items: ItineraryItem[] = Array.isArray(day.items) ? day.items : [];

    if (items.length === 0) {
      out += `  • Free day / Open exploration\n`;
    } else {
      for (const item of items) {
        const timeFormatted = formatHumanTime(item.planned_time);
        const name = item.place?.name || item.custom_title || 'Stop';
        const muni = item.place?.municipality_name ? ` (${item.place.municipality_name})` : '';
        const timePrefix = timeFormatted ? `${timeFormatted} - ` : '';
        out += `  • ${timePrefix}${name}${muni}\n`;
      }
    }
  }

  if (itinerary.assumptions && itinerary.assumptions.length > 0) {
    out += `\n📌 Practical Field Notes:\n`;
    for (const note of itinerary.assumptions) {
      out += `  • ${note}\n`;
    }
  }

  out += `\n— Planned with Trip mo, trip ko: Nueva Ecija Travel Guide`;
  return out;
}

/**
 * Copies the text summary to the clipboard.
 */
export async function copyTextSummary(itinerary: Itinerary): Promise<boolean> {
  const text = generateTextSummary(itinerary);
  if (!text) return false;

  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textArea);
    return success;
  } catch {
    return false;
  }
}

/**
 * Uses Web Share API if available to share the itinerary.
 */
export async function shareNativeItinerary(itinerary: Itinerary): Promise<boolean> {
  if (typeof navigator !== 'undefined' && 'share' in navigator) {
    try {
      await (navigator as any).share({
        title: itinerary.title || `Trip to ${itinerary.destination || 'Nueva Ecija'}`,
        text: generateTextSummary(itinerary),
      });
      return true;
    } catch {
      return false;
    }
  }
  return false;
}

/**
 * Invokes native window print.
 */
export function triggerPrintItinerary(): void {
  if (typeof window !== 'undefined') {
    window.print();
  }
}

/**
 * Generates a keyless multi-waypoint Google Maps navigation URL for a day's stops (ROUTE-04, UIUX-06).
 * Format: https://www.google.com/maps/dir/?api=1&origin=LAT,LNG&destination=LAT,LNG&waypoints=LAT,LNG|LAT,LNG&travelmode=driving
 */
export function buildGoogleMapsDayRouteUrl(items: ItineraryItem[]): string | null {
  if (!items || items.length === 0) return null;

  const validStops = items
    .map((item) => {
      const lat = item.place?.latitude ?? item.custom_lat;
      const lng = item.place?.longitude ?? item.custom_lng;
      if (lat != null && lng != null && !isNaN(lat) && !isNaN(lng)) {
        return { lat, lng, name: item.place?.name || item.custom_title || '' };
      }
      return null;
    })
    .filter((s): s is { lat: number; lng: number; name: string } => s !== null);

  if (validStops.length === 0) return null;
  if (validStops.length === 1) {
    return `https://www.google.com/maps/dir/?api=1&destination=${validStops[0].lat},${validStops[0].lng}&travelmode=driving`;
  }

  const origin = `${validStops[0].lat},${validStops[0].lng}`;
  const destination = `${validStops[validStops.length - 1].lat},${validStops[validStops.length - 1].lng}`;

  if (validStops.length === 2) {
    return `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving`;
  }

  const intermediate = validStops.slice(1, validStops.length - 1);
  const waypoints = intermediate.map((s) => `${s.lat},${s.lng}`).join('|');

  return `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&waypoints=${encodeURIComponent(waypoints)}&travelmode=driving`;
}
