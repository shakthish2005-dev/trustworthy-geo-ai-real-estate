from trustestate.risk_engine import CHECKS, evaluate_due_diligence, land_feature_score


def test_verified_case_is_low_risk():
    statuses = {check.key: "Verified" for check in CHECKS}
    result = evaluate_due_diligence(statuses)
    assert result["risk_score"] == 0
    assert result["risk_band"] == "Low"
    assert result["completion_pct"] == 100


def test_failed_critical_check_blocks_purchase():
    statuses = {check.key: "Verified" for check in CHECKS}
    statuses["title_chain"] = "Failed"
    result = evaluate_due_diligence(statuses)
    assert result["risk_band"] == "High"
    assert "30-year title chain reviewed" in result["blockers"]
    assert result["decision"].startswith("STOP")


def test_land_feature_score_is_bounded():
    result = land_feature_score({"frontage_ft": 50, "road_width_ft": 40, "slope_pct": 1, "corner_plot": True})
    assert 0 <= result["score"] <= 100

