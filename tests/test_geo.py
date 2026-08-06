from trustestate.geo import haversine_km, polygon_area_sqft


def test_haversine_identity():
    assert haversine_km(12.97, 77.59, 12.97, 77.59) == 0


def test_polygon_area_for_small_square():
    points = [(12.9700, 77.5900), (12.9700, 77.5901), (12.9701, 77.5901), (12.9701, 77.5900)]
    area = polygon_area_sqft(points)
    assert 1_000 < area < 2_000
