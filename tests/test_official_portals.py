from trustestate.official_portals import NATIONAL_PORTALS, portals_for_city, validate_registry


def test_registry_has_required_routes():
    assert validate_registry()
    assert len(NATIONAL_PORTALS) >= 6


def test_city_routes_to_state():
    state, portals = portals_for_city("Chennai")
    assert state == "Tamil Nadu"
    assert {"rera", "land_records", "registration"}.issubset(portals)

