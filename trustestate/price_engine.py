from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = [
    "bhk", "area_sqft", "bathrooms", "floor", "age_years", "amenity_score",
    "school_nearby", "hospital_nearby", "metro_nearby", "mall_nearby",
]
CATEGORICAL_FEATURES = ["city", "locality", "property_type"]


@dataclass
class PriceModelBundle:
    pipeline: Pipeline
    metrics: dict[str, float]
    reference: pd.DataFrame


def train_price_model(df: pd.DataFrame) -> PriceModelBundle:
    clean = df[df["is_fraud"].eq(0)].copy()
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = clean[features]
    y = np.log1p(clean["price"])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )
    model = RandomForestRegressor(
        n_estimators=180,
        max_depth=16,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(X_train, y_train)
    predictions = np.expm1(pipeline.predict(X_test))
    actual = np.expm1(y_test)
    metrics = {
        "r2": round(float(r2_score(actual, predictions)), 4),
        "mae": round(float(mean_absolute_error(actual, predictions)), 2),
        "rmse": round(float(mean_squared_error(actual, predictions) ** 0.5), 2),
        "test_rows": int(len(X_test)),
    }
    return PriceModelBundle(pipeline=pipeline, metrics=metrics, reference=clean)


def predict_with_interval(bundle: PriceModelBundle, payload: dict[str, Any]) -> dict[str, Any]:
    row = pd.DataFrame([payload])[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    transformed = bundle.pipeline.named_steps["preprocessor"].transform(row)
    forest = bundle.pipeline.named_steps["model"]
    tree_predictions = np.array(
        [np.expm1(tree.predict(transformed)[0]) for tree in forest.estimators_]
    )
    predicted = float(np.median(tree_predictions))
    low, high = np.percentile(tree_predictions, [10, 90])

    local = bundle.reference[
        bundle.reference["city"].eq(payload["city"])
        & bundle.reference["property_type"].eq(payload["property_type"])
    ]
    city_median = float(local["price"].median()) if not local.empty else float(bundle.reference["price"].median())
    explanations = [
        f"Area: {payload['area_sqft']:,.0f} sqft",
        f"Local reference median: ₹{city_median / 1e5:,.1f} lakh",
        f"Amenity score: {payload['amenity_score']}/14",
        f"Property age: {payload['age_years']} years",
    ]
    return {
        "predicted_price": round(predicted, 2),
        "interval_low": round(float(low), 2),
        "interval_high": round(float(high), 2),
        "price_per_sqft": round(predicted / max(float(payload["area_sqft"]), 1), 2),
        "explanations": explanations,
        "model_metrics": bundle.metrics,
        "data_notice": "Trained on the included synthetic academic dataset; not a certified valuation.",
    }
