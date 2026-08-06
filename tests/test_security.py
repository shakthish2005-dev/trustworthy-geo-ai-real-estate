from trustestate.security import hash_password, validate_password_strength, verify_password


def test_password_hash_round_trip():
    stored = hash_password("StrongPassword123", "separate-pepper")
    assert stored != "StrongPassword123"
    assert verify_password("StrongPassword123", stored, "separate-pepper")
    assert not verify_password("wrong-password", stored, "separate-pepper")


def test_password_strength():
    assert validate_password_strength("StrongPassword123")[0]
    assert not validate_password_strength("short")[0]

