"""Settings and application constants for Nueva Ecija Travel Desktop Client.

Adheres strictly to the Figma & Ionic Web Client Design System:
- Brand Title: "Trip mo, trip ko"
- Primary Accent: Travel Azure Blue (#0084ff / #2563eb)
- Suggested Card: Dark Navy Gradient (#091338 -> #03081e)
- Custom Card: Sky Blue Border (#38bdf8) on Pure White (#ffffff)
- Surfaces: Soft Slate (#f8fafc) background, Pure White (#ffffff) cards, Border (#e2e8f0)
- Verified Budgets & Honest Costs: Emerald Green (#047857 / #059669)
"""

import os
from pathlib import Path
import sys
from dataclasses import dataclass, field


def _resolve_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ThemeColors:
    """Design System Color Palette matching the Ionic Angular web client and Figma tokens."""

    # Brand Primary - Travel Azure Blue
    AZURE_PRIMARY: str = "#0084ff"
    AZURE_DEEP: str = "#0066cc"
    AZURE_SOFT: str = "#e8f2ff"
    PRIMARY_BLUE: str = "#0084ff"
    PRIMARY_HOVER: str = "#0066cc"
    PRIMARY_LIGHT: str = "#e8f2ff"

    # Action Cards Tokens
    NAVY_GRADIENT_START: str = "#091338"
    NAVY_GRADIENT_END: str = "#03081e"
    CUSTOM_CARD_BORDER: str = "#38bdf8"

    # Badges Tokens
    SUGGESTED_BADGE_BG: str = "#091338"
    SUGGESTED_BADGE_TEXT: str = "#38bdf8"
    CUSTOM_BADGE_BG: str = "#e0f2fe"
    CUSTOM_BADGE_TEXT: str = "#0284c7"

    # Legacy / Secondary Accents (Sierra Madre & Central Luzon)
    EMERALD_DARK: str = "#1b4332"
    EMERALD_PRIMARY: str = "#2d6a4f"
    EMERALD_LIGHT: str = "#40916c"
    EMERALD_MINT: str = "#d8f3dc"

    WARM_GOLD: str = "#d97706"
    AMBER_LIGHT: str = "#fef3c7"

    # Neutral Surfaces - Light Mode (Default)
    BG_LIGHT: str = "#f8fafc"
    SURFACE_LIGHT: str = "#ffffff"
    BORDER_LIGHT: str = "#e2e8f0"
    TEXT_MAIN_LIGHT: str = "#0f172a"
    TEXT_MUTED_LIGHT: str = "#64748b"
    TEXT_FAINT_LIGHT: str = "#94a3b8"
    TEXT_BLACK: str = "#000000"

    # Neutral Surfaces - Dark Mode
    BG_DARK: str = "#0b0f19"
    SURFACE_DARK: str = "#151e2e"
    SURFACE_DARK_HOVER: str = "#1e293b"
    BORDER_DARK: str = "#243247"
    TEXT_MAIN_DARK: str = "#f8fafc"
    TEXT_MUTED_DARK: str = "#94a3b8"
    TEXT_FAINT_DARK: str = "#64748b"

    # Semantic Feedback
    SUCCESS: str = "#10b981"
    SUCCESS_BG: str = "#ecfdf5"
    BUDGET_GREEN: str = "#047857"
    WARNING: str = "#f59e0b"
    WARNING_BG: str = "#fffbeb"
    ERROR: str = "#ef4444"
    ERROR_BG: str = "#fef2f2"
    INFO: str = "#0084ff"
    INFO_BG: str = "#eff6ff"


CANONICAL_CATEGORIES = [
    {"key": "nature_park", "label": "Nature & Parks", "icon": "eco"},
    {"key": "tourist_attraction", "label": "Tourist Attractions", "icon": "attractions"},
    {"key": "museum_cultural", "label": "Museums & Culture", "icon": "museum"},
    {"key": "church_religious", "label": "Churches & Historic", "icon": "church"},
    {"key": "resort_swimming", "label": "Resorts & Pools", "icon": "pool"},
    {"key": "restaurant", "label": "Restaurants & Dining", "icon": "restaurant"},
    {"key": "cafe", "label": "Cafes & Coffee", "icon": "local_cafe"},
    {"key": "hotel_accommodation", "label": "Hotels & Stays", "icon": "hotel"},
    {"key": "shopping_market", "label": "Markets & Souvenirs", "icon": "shopping_bag"},
    {"key": "transport_terminal", "label": "Transport Terminals", "icon": "directions_bus"},
    {"key": "hospital_clinic", "label": "Hospitals & Health", "icon": "local_hospital"},
    {"key": "pharmacy", "label": "Pharmacies", "icon": "medication"},
    {"key": "bank_atm", "label": "Banks & ATMs", "icon": "atm"},
    {"key": "fuel_station", "label": "Fuel & Charging", "icon": "local_gas_station"},
    {"key": "convenience_store", "label": "Convenience Stores", "icon": "store"},
    {"key": "public_facility", "label": "Public Facilities", "icon": "account_balance"},
]

NUEVA_ECIJA_LGUS = [
    "Aliaga", "Bongabon", "Cabanatuan City", "Cabiao", "Carranglan",
    "Cuyapo", "Gabaldon", "Gapan City", "General Mamerto Natividad", "General Tinio",
    "Guimba", "Jaen", "Laur", "Licab", "Llanera",
    "Lupao", "Nampicuan", "Palayan City", "Pantabangan", "Peñaranda",
    "Quezon", "Rizal", "San Antonio", "San Isidro", "San Jose City",
    "San Leonardo", "Santa Rosa", "Santo Domingo", "Science City of Muñoz", "Talavera",
    "Talugtug", "Zaragoza",
]

PACING_OPTIONS = [
    {"key": "relaxed", "label": "Relaxed", "desc": "2-3 stops per day, leisure visits"},
    {"key": "moderate", "label": "Moderate", "desc": "3-4 stops per day, balanced pace"},
    {"key": "packed", "label": "Packed", "desc": "5+ stops per day, maximum coverage"},
]

BUDGET_PRESETS = [
    {"key": "backpacker", "label": "Backpacker (₱1,000 / day)", "amount": 1000.0},
    {"key": "moderate", "label": "Moderate (₱2,500 / day)", "amount": 2500.0},
    {"key": "comfort", "label": "Comfort (₱5,000 / day)", "amount": 5000.0},
    {"key": "luxury", "label": "Luxury (₱10,000+ / day)", "amount": 10000.0},
]


@dataclass
class Settings:
    """Runtime configuration settings."""

    app_title: str = "Trip mo, trip ko — Nueva Ecija Desktop"
    brand_name: str = "Trip mo, trip ko"
    app_version: str = "1.0.0"
    api_base_url: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
    api_timeout_seconds: float = float(os.getenv("API_TIMEOUT_SECONDS", "15.0"))
    itinerary_gen_timeout_seconds: float = float(os.getenv("ITINERARY_GEN_TIMEOUT_SECONDS", "45.0"))
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # Desktop Window Constraints
    window_min_width: int = 1080
    window_min_height: int = 720
    window_width: int = 1280
    window_height: int = 840

    # Local Storage Directory
    base_dir: Path = field(default_factory=_resolve_base_dir)
    storage_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "storage_dir", self.base_dir / "storage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Retrieves the singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
