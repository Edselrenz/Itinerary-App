#!/usr/bin/env python3
"""Export all OpenStreetMap and curated places from the database to Project/src/assets/data/osm_places.json.

Allows the client to display all real-world places (cafes, tourist spots, lodging,
parks, museums, restaurants, clinics, etc.) across Nueva Ecija in offline, standalone,
or decoupled mode.

Usage:
    python scripts/export_osm_to_client_asset.py
"""

import json
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "nueva_ecija_travel.db"
OUTPUT_PATH = ROOT_DIR / "Project" / "src" / "assets" / "data" / "osm_places.json"


def export_places():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, m.name as m_name
        FROM places p
        LEFT JOIN municipalities m ON p.municipality_id = m.id
        WHERE p.is_active = 1
        ORDER BY p.is_featured DESC, p.name ASC
    """)
    rows = cursor.fetchall()

    places = []
    for r in rows:
        tags = []
        if r["tags"]:
            try:
                tags = json.loads(r["tags"])
            except Exception:
                tags = [r["tags"]]

        item = {
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "cost_currency": r["cost_currency"] or "PHP",
            "source_name": r["source_name"] or "OpenStreetMap",
            "source_record_id": r["source_record_id"] or "",
            "imported_at": r["imported_at"] or "",
            "is_featured": bool(r["is_featured"]),
            "tags": tags,
            "directions_url": r["google_maps_uri"] or f"https://www.google.com/maps/dir/?api=1&destination={r['latitude']},{r['longitude']}",
        }

        # Include optional non-empty fields to keep JSON payload lean
        if r["m_name"]:
            item["municipality_name"] = r["m_name"]
        if r["municipality_id"]:
            item["municipality_id"] = r["municipality_id"]
        if r["address_text"]:
            item["address_text"] = r["address_text"]
        if r["description"]:
            item["description"] = r["description"]
        if r["phone"]:
            item["phone"] = r["phone"]
        if r["website"]:
            item["website"] = r["website"]
        if r["opening_hours"]:
            item["opening_hours"] = r["opening_hours"]
        if r["estimated_cost_min"] is not None:
            item["estimated_cost_min"] = r["estimated_cost_min"]
        if r["estimated_cost_max"] is not None:
            item["estimated_cost_max"] = r["estimated_cost_max"]
        if r["image_url"]:
            item["image_url"] = r["image_url"]
        if r["source_url"]:
            item["source_url"] = r["source_url"]
        if r["rating"] is not None:
            item["rating"] = r["rating"]
        if r["user_rating_count"] is not None:
            item["user_rating_count"] = r["user_rating_count"]

        places.append(item)

    conn.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(places, f, separators=(",", ":"), ensure_ascii=False)

    print(f"[OK] Successfully exported {len(places)} places to {OUTPUT_PATH}")
    print(f"     Asset file size: {OUTPUT_PATH.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    export_places()

