from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CheckDefinition:
    key: str
    label: str
    category: str
    weight: int
    critical: bool
    evidence: str


CHECKS = [
    CheckDefinition("title_chain", "30-year title chain reviewed", "Ownership", 10, True, "Certified parent deeds and legal opinion"),
    CheckDefinition("seller_identity", "Seller identity matches title records", "Ownership", 8, True, "Government ID, title deed and authority documents"),
    CheckDefinition("encumbrance", "Encumbrance certificate is clear", "Ownership", 10, True, "Certified EC covering the lawyer-recommended period"),
    CheckDefinition("mutation", "Mutation / revenue record is current", "Ownership", 6, True, "Current RoR, Patta, Khata, 7/12 or state equivalent"),
    CheckDefinition("survey_match", "Survey number, extent and boundaries match", "Survey", 10, True, "Licensed survey report and official cadastral sketch"),
    CheckDefinition("access_road", "Legal access road exists on record", "Survey", 7, True, "Approved layout and access/right-of-way evidence"),
    CheckDefinition("conversion", "Land-use conversion is valid", "Planning", 8, True, "Conversion order for intended non-agricultural use"),
    CheckDefinition("zoning", "Zoning/master-plan use permits the purchase purpose", "Planning", 8, True, "Planning authority zoning certificate/map"),
    CheckDefinition("layout_approval", "Layout approval is verified", "Planning", 8, True, "Sanctioned layout from local planning authority"),
    CheckDefinition("rera", "RERA registration checked where applicable", "Regulatory", 5, False, "Official RERA project and promoter record"),
    CheckDefinition("prohibited_land", "Not listed as prohibited/government/assigned land", "Regulatory", 10, True, "Official prohibited-property and revenue search"),
    CheckDefinition("litigation", "Pending litigation search completed", "Legal", 8, True, "eCourts search and advocate review"),
    CheckDefinition("tax_paid", "Property and land taxes are paid", "Financial", 4, False, "Latest tax receipt and no-dues confirmation"),
    CheckDefinition("loan_release", "Existing lender charge is released", "Financial", 8, True, "Bank NOC/release deed and updated EC/CERSAI search"),
    CheckDefinition("market_value", "Guideline/market value has been checked", "Financial", 3, False, "Official registration valuation source"),
    CheckDefinition("flood", "Flood/waterlogging exposure reviewed", "Physical risk", 6, False, "Bhuvan/local authority layer and site history"),
    CheckDefinition("water_body", "Buffer from water body/drain is compliant", "Physical risk", 7, True, "Survey overlay and authority setback rule"),
    CheckDefinition("environment", "Environmental/forest/CRZ restrictions checked", "Physical risk", 7, True, "PARIVESH and competent authority search"),
    CheckDefinition("soil", "Soil bearing capacity/site condition reviewed", "Engineering", 3, False, "Geotechnical or soil test report"),
    CheckDefinition("utilities", "Water, electricity, sewer/drainage are verified", "Infrastructure", 3, False, "Connection records and physical inspection"),
    CheckDefinition("road_width", "Road width and frontage meet intended use", "Infrastructure", 4, False, "Survey measurement and planning rules"),
    CheckDefinition("physical_possession", "Physical possession and occupation checked", "Site inspection", 8, True, "Dated site inspection, neighbours and possession record"),
    CheckDefinition("power_of_attorney", "Power of Attorney is valid where used", "Legal", 7, True, "Registered POA and lawyer verification"),
    CheckDefinition("agreement_review", "Sale agreement reviewed before token payment", "Legal", 7, True, "Independent lawyer-approved agreement"),
]

STATUS_FACTOR = {
    "Verified": 0.0,
    "Not applicable": 0.0,
    "Pending": 0.55,
    "Concern": 0.8,
    "Failed": 1.0,
}


def definitions_as_dicts() -> list[dict[str, Any]]:
    return [asdict(item) for item in CHECKS]


def evaluate_due_diligence(statuses: dict[str, str]) -> dict[str, Any]:
    total_weight = sum(check.weight for check in CHECKS)
    risk_points = 0.0
    blockers: list[str] = []
    pending: list[str] = []
    verified = 0

    for check in CHECKS:
        status = statuses.get(check.key, "Pending")
        factor = STATUS_FACTOR.get(status, STATUS_FACTOR["Pending"])
        risk_points += check.weight * factor
        if status in {"Verified", "Not applicable"}:
            verified += 1
        elif status == "Pending":
            pending.append(check.label)
        if check.critical and status in {"Concern", "Failed"}:
            blockers.append(check.label)

    score = round(100 * risk_points / total_weight, 1)
    if blockers or score >= 60:
        band = "High"
        decision = "STOP - do not pay a token or sign until critical issues are independently cleared."
    elif score >= 30:
        band = "Medium"
        decision = "PROCEED ONLY WITH CONDITIONS - complete evidence and professional reviews first."
    else:
        band = "Low"
        decision = "LOWER OBSERVED RISK - still obtain certified records and professional advice."

    return {
        "risk_score": score,
        "risk_band": band,
        "decision": decision,
        "blockers": blockers,
        "pending": pending,
        "verified_count": verified,
        "total_checks": len(CHECKS),
        "completion_pct": round(100 * verified / len(CHECKS)),
    }


def land_feature_score(features: dict[str, Any]) -> dict[str, Any]:
    """Transparent physical-usability score, separate from legal due diligence."""
    score = 50.0
    reasons: list[str] = []
    frontage = float(features.get("frontage_ft") or 0)
    road = float(features.get("road_width_ft") or 0)
    slope = float(features.get("slope_pct") or 0)

    if frontage >= 40:
        score += 10
        reasons.append("Strong road frontage")
    elif frontage and frontage < 20:
        score -= 12
        reasons.append("Limited frontage")
    if road >= 30:
        score += 10
        reasons.append("Good access-road width")
    elif road and road < 20:
        score -= 15
        reasons.append("Narrow approach road")
    if features.get("corner_plot"):
        score += 5
        reasons.append("Corner plot")
    if features.get("water") and features.get("electricity"):
        score += 10
        reasons.append("Basic utilities reported")
    if slope > 10:
        score -= 10
        reasons.append("High slope may increase site-development cost")
    if features.get("flood_history"):
        score -= 20
        reasons.append("Reported flood/waterlogging history")

    return {"score": round(max(0, min(100, score))), "reasons": reasons}
