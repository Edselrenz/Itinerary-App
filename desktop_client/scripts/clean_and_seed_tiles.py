"""Purge stale ESRI RGB tiles from assets/tiles_cache/ and seed missing Z10-Z12 widescreen tiles."""
from pathlib import Path
import struct
import zlib

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
TILES_DIR = ASSETS_DIR / "tiles"
CACHE_DIR = ASSETS_DIR / "tiles_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def make_solid_png(r: int, g: int, b: int, width: int = 256, height: int = 256) -> bytes:
    """Create a valid 256x256 RGB PNG image of a single solid color (e.g. #aad3df OSM water)."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes([r, g, b]) * width
    idat = zlib.compress(row * height, level=9)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def is_stale_esri_or_blocked_tile(path: Path) -> bool:
    """Detect stale ESRI RGB tiles or OSM 403 blocked hazard tiles."""
    try:
        data = path.read_bytes()
        if len(data) < 67 or data[:8] != b"\x89PNG\r\n\x1a\n":
            return True
        # IHDR color_type is at byte 25: 2 = RGB (ESRI World Street Map), 3 = Palette (OSM Standard)
        # Keep our solid water PNGs (which are < 1200 bytes) but purge large RGB ESRI tiles (> 2500 bytes)
        color_type = data[25]
        if color_type == 2 and len(data) > 2500:
            return True
        # Also reject OSM's 403 hazard tile
        if len(data) in (21645, 21644, 15403) or b"Access blocked" in data or b"http://osm.wiki/Blocked" in data:
            return True
        return False
    except Exception:
        return True


def main() -> None:
    purged = 0
    for f in CACHE_DIR.glob("*.png"):
        if is_stale_esri_or_blocked_tile(f):
            print(f"Purging stale ESRI/corrupt tile: {f.name}")
            f.unlink(missing_ok=True)
            purged += 1
    print(f"Purged {purged} stale tiles from {CACHE_DIR}")

    # Pre-generate solid ocean tiles (#aad3df = RGB 170, 211, 223) for Z10 ocean area (x >= 858, y >= 464)
    water_png = make_solid_png(170, 211, 223)
    ocean_seeded = 0
    for x in range(858, 862):
        for y in range(464, 471):
            tile_path = CACHE_DIR / f"10_{x}_{y}.png"
            if not tile_path.exists():
                tile_path.write_bytes(water_png)
                ocean_seeded += 1
    print(f"Seeded {ocean_seeded} solid ocean tiles")


if __name__ == "__main__":
    main()
