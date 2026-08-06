from __future__ import annotations

import hashlib
import math
from typing import Iterable

import numpy as np
import pandas as pd

from trustestate.config import CITY_COORDINATES, PROPERTIES_CSV


def load_properties() -> pd.DataFrame:
    df = pd.read_csv(PROPERTIES_CSV)
    df["price_per_sqft"] = (df["price"] / df["area_sqft"]).round(2)
    return enrich_demo_coordinates(df)


def _stable_offsets(value: object) -> tuple[float, float]:
    digest = hashlib.sha256(str(value).encode("utf-8")).digest()
    first = int.from_bytes(digest[:4], "big") / 2**32
    second = int.from_bytes(digest[4:8], "big") / 2**32
    return (first - 0.5) * 0.16, (second - 0.5) * 0.16


def enrich_demo_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Add approximate coordinates for the synthetic demo dataset.

    Coordinates are intentionally marked as approximate and must not be used as
    cadastral boundaries or proof of property location.
    """
    result = df.copy()
    coordinates = []
    for row in result.itertuples():
        base_lat, base_lon = CITY_COORDINATES.get(row.city, (20.5937, 78.9629))
        dlat, dlon = _stable_offsets(row.property_id)
        coordinates.append((base_lat + dlat, base_lon + dlon))
    result[["latitude", "longitude"]] = pd.DataFrame(coordinates, index=result.index)
    result["coordinate_quality"] = "Demo approximation - not survey data"
    return result


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_comparables(
    df: pd.DataFrame,
    latitude: float,
    longitude: float,
    city: str | None = None,
    property_type: str | None = None,
    limit: int = 8,
) -> pd.DataFrame:
    pool = df.copy()
    if city:
        pool = pool[pool["city"].eq(city)]
    if property_type:
        pool = pool[pool["property_type"].eq(property_type)]
    pool = pool[pool["is_fraud"].eq(0)].copy()
    pool["distance_km"] = [
        haversine_km(latitude, longitude, lat, lon)
        for lat, lon in zip(pool["latitude"], pool["longitude"])
    ]
    return pool.sort_values(["distance_km", "price_per_sqft"]).head(limit)


def polygon_area_sqft(points: Iterable[tuple[float, float]]) -> float:
    """Approximate small parcel area from latitude/longitude boundary points."""
    pts = list(points)
    if len(pts) < 3:
        return 0.0
    lat0 = math.radians(sum(p[0] for p in pts) / len(pts))
    projected = []
    for lat, lon in pts:
        x = math.radians(lon) * 6371008.8 * math.cos(lat0)
        y = math.radians(lat) * 6371008.8
        projected.append((x, y))
    area_m2 = 0.0
    for i, (x1, y1) in enumerate(projected):
        x2, y2 = projected[(i + 1) % len(projected)]
        area_m2 += x1 * y2 - x2 * y1
    return abs(area_m2) / 2 * 10.7639104
