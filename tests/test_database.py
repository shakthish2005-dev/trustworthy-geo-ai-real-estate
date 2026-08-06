import trustestate.database as database


def test_bootstrap_login_and_case_permissions(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.ensure_bootstrap_users("admin_test", "AdminPassword123", "user_test", "UserPassword123", "pepper")
    admin = database.authenticate("admin_test", "AdminPassword123", "pepper")
    user = database.authenticate("user_test", "UserPassword123", "pepper")
    assert admin and admin["role"] == "admin"
    assert user and user["role"] == "user"
    assert database.authenticate("user_test", "wrong", "pepper") is None

    case_id = database.save_case(user["id"], {"title": "Test parcel", "city": "Chennai"}, 42.0, "Medium")
    assert len(database.list_cases(user["id"], "user")) == 1
    database.update_case_status(case_id, "Lawyer review", admin["id"])
    cases = database.list_cases(admin["id"], "admin")
    assert cases[0]["review_status"] == "Lawyer review"

