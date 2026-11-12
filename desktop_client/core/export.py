"""Itinerary Exporter for iCalendar (.ics), Text Summary, and JSON formats."""

from datetime import datetime, timedelta, timezone
import json
from typing import Optional
import uuid

from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem


def export_to_ics(itinerary: Itinerary) -> str:
    """Exports an itinerary to RFC 5545 iCalendar (.ics) format compatible with

    Google Calendar, Apple Calendar, and Outlook.
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Nueva Ecija Travel//Desktop Client 1.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{itinerary.title}",
    ]

    for day in itinerary.days:
        travel_date_str = day.travel_date  # YYYY-MM-DD
        try:
            day_dt = datetime.strptime(travel_date_str, "%Y-%m-%d")
        except ValueError:
            day_dt = datetime.now()

        for idx, item in enumerate(day.items):
            uid = f"{item.id}@{itinerary.id}.nuevaecijatravel.ph"
            
            # Resolve event timing
            start_hour = 9 + (idx * 2)  # Default progression if no planned time
            start_minute = 0
            if item.planned_time:
                try:
                    time_parts = item.planned_time.split(":")
                    start_hour = int(time_parts[0])
                    start_minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                except Exception:
                    pass

            event_start = day_dt.replace(hour=min(start_hour, 23), minute=start_minute, second=0)
            duration = item.duration_minutes or 90
            event_end = event_start + timedelta(minutes=duration)

            dtstart = event_start.strftime("%Y%m%dT%H%M%S")
            dtend = event_end.strftime("%Y%m%dT%H%M%S")
            dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

            summary = item.display_title
            location = ""
            if item.place:
                location = item.place.address_text or item.place.municipality_name or "Nueva Ecija"
            elif item.custom_title:
                location = "Custom Venue, Nueva Ecija"

            description_parts = [
                f"Itinerary: {itinerary.title}",
                f"Day {day.day_number}: {day.title or travel_date_str}",
                f"Estimated Cost: {item.display_cost}",
            ]
            if item.notes:
                description_parts.append(f"Notes: {item.notes}")
            if item.place and item.place.directions_url:
                description_parts.append(f"Directions: {item.place.directions_url}")

            description = "\\n".join(description_parts)

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                f"SUMMARY:{summary}",
                f"LOCATION:{location}",
                f"DESCRIPTION:{description}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def export_to_text(itinerary: Itinerary) -> str:
    """Exports a structured, human-readable Markdown summary of the travel itinerary."""
    lines = [
        f"# {itinerary.title}",
        f"**Destination:** {itinerary.destination}",
        f"**Dates:** {itinerary.date_range_display} ({len(itinerary.days)} days)",
        f"**Daily Budget:** ₱{itinerary.daily_budget:,.2f}",
        f"**Total Estimated Cost:** ₱{itinerary.total_estimated_cost:,.2f}",
        f"**Total Stops:** {itinerary.total_stops}",
        "",
        "---",
        "",
    ]

    for day in itinerary.days:
        lines.append(f"## {day.display_title} ({day.travel_date})")
        lines.append(f"*Day Budget/Cost: ~₱{day.total_day_cost:,.2f}*")
        lines.append("")

        if not day.items:
            lines.append("  *No scheduled stops for this day.*")
            lines.append("")
            continue

        for idx, item in enumerate(day.items, 1):
            time_str = f"[{item.planned_time}] " if item.planned_time else ""
            lines.append(f"### {idx}. {time_str}{item.display_title}")
            
            if item.place:
                lines.append(f"- **Category:** {item.place.formatted_category}")
                lines.append(f"- **Location:** {item.place.address_text or item.place.municipality_name or 'Nueva Ecija'}")
                lines.append(f"- **Operating Hours:** {item.place.opening_hours or 'Check locally'}")
                if item.place.phone:
                    lines.append(f"- **Contact:** {item.place.phone}")
            
            lines.append(f"- **Duration:** {item.duration_minutes} minutes")
            lines.append(f"- **Cost:** {item.display_cost}")
            
            if item.notes:
                lines.append(f"- **Notes:** {item.notes}")
            
            if item.place and item.place.directions_url:
                lines.append(f"- **Google Maps:** {item.place.directions_url}")
            
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.extend([
        "### Traveler Guidelines & Local Notes",
        "- Honest pricing: Values represent estimated entry fees or meal costs per person.",
        "- Tricycle and jeepney fares vary slightly by municipality.",
        "- Always carry cash as smaller local cafes and mountain resorts may have limited card connectivity.",
        "- Generated with Nueva Ecija Travel Desktop Client.",
    ])

    return "\n".join(lines)


def export_to_json(itinerary: Itinerary) -> str:
    """Serializes itinerary into pretty-printed JSON."""
    return json.dumps(itinerary.to_dict(), indent=2, ensure_ascii=False)
