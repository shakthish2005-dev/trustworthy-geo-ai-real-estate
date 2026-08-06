from __future__ import annotations

from trustestate.config import CITY_STATE

NATIONAL_PORTALS = [
    {
        "name": "MoHUA RERA authorities directory",
        "purpose": "Find the official RERA authority and project/agent search for each state or UT.",
        "url": "https://www.mohua.gov.in/documents/acts-and-policies/rera-YDM4EzMtQWa?pageTitle=Real-Estate-%28Regulation-and-Development%29-Act%2C-2016-%5BRERA%5D",
    },
    {
        "name": "National Government Services Portal",
        "purpose": "Locate state services for land records, mutation, encumbrance certificates and property tax.",
        "url": "https://services.india.gov.in/",
    },
    {
        "name": "NGDRS property registration",
        "purpose": "Registration and deed services in participating states and UTs.",
        "url": "https://ngdrs.gov.in/",
    },
    {
        "name": "PARIVESH",
        "purpose": "Search environmental, forest, wildlife and coastal regulatory clearances.",
        "url": "https://parivesh.nic.in/",
    },
    {
        "name": "Bhuvan thematic maps",
        "purpose": "Review land-use, water-body, flood-hazard, erosion and other thematic layers.",
        "url": "https://bhuvan.nrsc.gov.in/gis/thematic/index.php",
    },
    {
        "name": "eCourts Services",
        "purpose": "Search court cases using party, advocate, case and other available details.",
        "url": "https://services.ecourts.gov.in/ecourtindia_v6/",
    },
    {
        "name": "CERSAI",
        "purpose": "Check the official portal for security-interest related asset searches where available.",
        "url": "https://www.cersai.org.in/CERSAI/home.prg",
    },
]

STATE_PORTALS = {
    "Maharashtra": {
        "rera": "https://maharera.maharashtra.gov.in/",
        "land_records": "https://bhulekh.mahabhumi.gov.in/",
        "registration": "https://igrmaharashtra.gov.in/",
    },
    "Karnataka": {
        "rera": "https://rera.karnataka.gov.in/",
        "land_records": "https://landrecords.karnataka.gov.in/",
        "registration": "https://kaveri.karnataka.gov.in/",
    },
    "Tamil Nadu": {
        "rera": "https://rera.tn.gov.in/",
        "land_records": "https://eservices.tn.gov.in/eservicesnew/index.html",
        "registration": "https://tnreginet.gov.in/portal/",
    },
    "Telangana": {
        "rera": "https://rera.telangana.gov.in/",
        "land_records": "https://www.telangana.gov.in/departments/revenue-registration-and-stamps/",
        "registration": "https://registration.telangana.gov.in/",
    },
    "Delhi": {
        "rera": "https://www.rera.delhi.gov.in/",
        "land_records": "https://dlrc.delhi.gov.in/",
        "registration": "https://doris.delhigovt.nic.in/",
    },
    "West Bengal": {
        "rera": "https://rera.wb.gov.in/",
        "land_records": "https://banglarbhumi.gov.in/",
        "registration": "https://wbregistration.gov.in/",
    },
    "Gujarat": {
        "rera": "https://gujrera.gujarat.gov.in/",
        "land_records": "https://anyror.gujarat.gov.in/",
        "registration": "https://garvi.gujarat.gov.in/",
    },
    "Rajasthan": {
        "rera": "https://rera.rajasthan.gov.in/",
        "land_records": "https://apnakhata.rajasthan.gov.in/",
        "registration": "https://epanjiyan.rajasthan.gov.in/",
    },
}


def portals_for_city(city: str) -> tuple[str, dict[str, str]]:
    state = CITY_STATE.get(city, "")
    return state, STATE_PORTALS.get(state, {})


def validate_registry() -> bool:
    required = {"rera", "land_records", "registration"}
    return all(required.issubset(record) for record in STATE_PORTALS.values())
