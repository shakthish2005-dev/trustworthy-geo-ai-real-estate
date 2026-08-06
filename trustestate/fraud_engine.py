from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

FEATURES = ["bhk", "area_sqft", "amenity_score", "price_per_sqft", "age_years"]
SCAM_TERMS = {
    "urgent": 7,
    "cash only": 15,
    "token money": 15,
    "owner abroad": 8,
    "advance booking": 10,
    "no documents": 25,
    "original papers later": 25,
    "immediate transfer": 10,
}


@dataclass
class AnomalyBundle:
    scaler: StandardScaler
    model: IsolationForest
    reference: pd.DataFrame


def train_anomaly_model(df: pd.DataFrame) -> AnomalyBundle:
    reference = df[df["is_fraud"].eq(0)].copy()
    if "price_per_sqft" not in reference:
        reference["price_per_sqft"] = reference["price"] / reference["area_sqft"]
    scaler = StandardScaler()
    values = scaler.fit_transform(reference[FEATURES])
    model = IsolationForest(
        n_estimators=180, contamination=0.03, random_state=42, n_jobs=-1
    )
    model.fit(values)
    return AnomalyBundle(scaler=scaler, model=model, reference=reference)


def analyze_listing(bundle: AnomalyBundle, payload: dict[str, Any]) -> dict[str, Any]:
    area = max(float(payload.get("area_sqft") or 1), 1)
    price = max(float(payload.get("price") or 0), 0)
    bhk = max(int(payload.get("bhk") or 1), 1)
    description = str(payload.get("description") or "").lower()
    price_psf = price / area
    age = int(payload.get("age_years") or 0)
    amenity = int(payload.get("amenity_score") or 0)

    row = pd.DataFrame(
        [{
            "bhk": bhk,
            "area_sqft": area,
            "amenity_score": amenity,
            "price_per_sqft": price_psf,
            "age_years": age,
        }]
    )
    model_score = float(bundle.model.decision_function(bundle.scaler.transform(row[FEATURES]))[0])
    risk = max(0.0, min(40.0, (0.08 - model_score) * 180))
    reasons: list[str] = []

    city = payload.get("city")
    locality = payload.get("locality")
    reference = bundle.reference[bundle.reference["city"].eq(city)]
    local_ref = reference[reference["locality"].eq(locality)]
    if len(local_ref) >= 5:
        reference = local_ref
    median_psf = float(reference["price_per_sqft"].median()) if not reference.empty else 0.0
    deviation = ((price_psf / median_psf) - 1) * 100 if median_psf else 0.0
    if deviation < -45:
        risk += 30
        reasons.append(f"Listed price is {abs(deviation):.0f}% below the reference median")
    elif deviation > 80:
        risk += 12
        reasons.append(f"Listed price is {deviation:.0f}% above the reference median")

    sqft_per_bhk = area / bhk
    if sqft_per_bhk < 220:
        risk += 25
        reasons.append(f"Only {sqft_per_bhk:.0f} sqft per BHK - verify layout and measurements")

    hits = []
    for term, points in SCAM_TERMS.items():
        if term in description:
            risk += points
            hits.append(term)
    if hits:
        reasons.append("High-pressure wording detected: " + ", ".join(hits))

    risk = round(max(0, min(100, risk)), 1)
    if risk >= 65:
        band = "High"
    elif risk >= 35:
        band = "Medium"
    else:
        band = "Low"
    if not reasons:
        reasons.append("No major rule-based anomaly detected; documentary verification is still required")
    return {
        "risk_score": risk,
        "risk_band": band,
        "reasons": reasons,
        "price_per_sqft": round(price_psf, 2),
        "reference_median_psf": round(median_psf, 2),
        "model_anomaly_score": round(model_score, 4),
        "notice": "This is anomaly screening, not proof that a listing is genuine or fraudulent.",
    }
