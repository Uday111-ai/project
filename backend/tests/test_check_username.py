from app.core.username_suggestions import (
    MAX_USERNAME_LENGTH,
    MIN_USERNAME_LENGTH,
    generate_candidates,
)

VALID_PASSWORD = "Str0ng!Passw0rd"


def signup_payload(username="takenuser", email="taken@example.com", password=VALID_PASSWORD):
    return {
        "username": username,
        "email": email,
        "create_password": password,
        "confirm_password": password,
    }


def test_check_username_available(client):
    resp = client.get("/check-username", params={"username": "nobodyhasthisname"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    # Omitted entirely when available, per the API contract.
    assert "suggestions" not in body


def test_check_username_taken_returns_real_available_suggestions(client, db_session):
    client.post("/signup", json=signup_payload())

    resp = client.get("/check-username", params={"username": "takenuser"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert "suggestions" in body
    assert 0 < len(body["suggestions"]) <= 4

    # Every suggestion must itself currently be free — verify against the
    # DB directly rather than trusting the endpoint's own claim.
    from sqlalchemy import func

    from app.models.user import User

    for suggestion in body["suggestions"]:
        assert (
            db_session.query(User)
            .filter(func.lower(User.username) == suggestion.lower())
            .first()
            is None
        )
        assert MIN_USERNAME_LENGTH <= len(suggestion) <= MAX_USERNAME_LENGTH


def test_check_username_case_insensitive(client):
    client.post("/signup", json=signup_payload())

    resp = client.get("/check-username", params={"username": "TakenUser"})
    assert resp.status_code == 200
    assert resp.json()["available"] is False


def test_check_username_rejects_out_of_bounds_length(client):
    too_short = client.get("/check-username", params={"username": "ab"})
    assert too_short.status_code == 422

    too_long = client.get("/check-username", params={"username": "a" * 31})
    assert too_long.status_code == 422

    # Matches the shape of the rest of the API's validation errors.
    assert isinstance(too_short.json()["detail"], list)


def test_check_username_does_not_write_anything(client, db_session):
    from app.models.user import User

    client.get("/check-username", params={"username": "somefreename"})
    assert db_session.query(User).count() == 0


def test_check_username_suggestions_never_offer_a_taken_name(client, monkeypatch):
    """When every candidate the generator produces is itself already
    taken, suggestions must come back empty rather than ever offering a
    taken name. Pins the generator's output via monkeypatch so the
    endpoint's own (independently randomized) call is deterministic and
    the test can seed exactly the names it will check.
    """
    base = "popularname"
    fixed_candidates = ["popularname_1", "popularname_2", "popularname_3"]

    client.post("/signup", json=signup_payload(username=base, email="a@example.com"))
    for i, candidate in enumerate(fixed_candidates):
        client.post(
            "/signup",
            json=signup_payload(username=candidate, email=f"b{i}@example.com"),
        )

    monkeypatch.setattr(
        "app.main.generate_candidates", lambda username, count=8: list(fixed_candidates)
    )

    resp = client.get("/check-username", params={"username": base})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body.get("suggestions", []) == []


def test_check_username_rate_limited():
    """The production limiter (30/minute) is disabled globally in
    conftest.py so other tests aren't affected by it, so this test spins
    up its own app instance with the limiter left on to confirm the
    decorator is actually wired up.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    was_enabled = app.state.limiter.enabled
    app.state.limiter.enabled = True
    try:
        last_status = None
        for _ in range(35):
            last_status = client.get(
                "/check-username", params={"username": "ratelimitcheck"}
            ).status_code
            if last_status == 429:
                break
        assert last_status == 429
    finally:
        app.state.limiter.enabled = was_enabled
