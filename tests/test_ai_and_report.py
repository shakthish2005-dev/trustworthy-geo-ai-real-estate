from trustestate.fraud_engine import analyze_listing, train_anomaly_model
from trustestate.geo import load_properties
from trustestate.price_engine import predict_with_interval, train_price_model
from trustestate.reporting import build_due_diligence_pdf
from trustestate.risk_engine import CHECKS, evaluate_due_diligence


def test_ai_and_pdf_smoke():
    data = load_properties()
    sample = data.iloc[0].to_dict()

    price_bundle = train_price_model(data)
    estimate = predict_with_interval(price_bundle, sample)
    assert estimate["interval_low"] < estimate["interval_high"]
    assert price_bundle.metrics["test_rows"] > 0

    anomaly_bundle = train_anomaly_model(data)
    screening = analyze_listing(anomaly_bundle, {**sample, "description": "clear documents"})
    assert screening["risk_band"] in {"Low", "Medium", "High"}
    assert "not proof" in screening["notice"].lower()

    statuses = {check.key: "Pending" for check in CHECKS}
    result = evaluate_due_diligence(statuses)
    report = build_due_diligence_pdf(
        {"title": "Test parcel", "city": "Delhi", "state": "Delhi", "survey_number": "TEST"},
        statuses,
        result,
    )
    assert report.startswith(b"%PDF")
    assert len(report) > 5_000

