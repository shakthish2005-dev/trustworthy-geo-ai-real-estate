from __future__ import annotations

from pathlib import Path

APP_NAME = "Trustworthy Geo-AI Real Estate Decision Support System"
APP_VERSION = "2.0.0"

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
DB_PATH = DATA_DIR / "trustestate.db"
PROPERTIES_CSV = DATA_DIR / "properties.csv"
DEMO_PANORAMA = ASSETS_DIR / "demo_land_panorama.png"

CITY_STATE = {
    "Mumbai": "Maharashtra",
    "Pune": "Maharashtra",
    "Bangalore": "Karnataka",
    "Hyderabad": "Telangana",
    "Chennai": "Tamil Nadu",
    "Delhi": "Delhi",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
    "Surat": "Gujarat",
    "Jaipur": "Rajasthan",
}

CITY_COORDINATES = {
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Bangalore": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Delhi": (28.6139, 77.2090),
    "Kolkata": (22.5726, 88.3639),
    "Ahmedabad": (23.0225, 72.5714),
    "Surat": (21.1702, 72.8311),
    "Jaipur": (26.9124, 75.7873),
}

DISCLAIMER = (
    "Decision-support only. This platform does not certify title, ownership, "
    "zoning, encumbrance status, construction permission, or legal fitness. "
    "Obtain certified records and independent advice from a qualified property "
    "lawyer, licensed surveyor, structural engineer, and relevant authorities."
)
