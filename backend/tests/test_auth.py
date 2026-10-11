from hashlib import sha256

from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User

VALID_PASSWORD = "Str0ng!Passw0rd"


def signup_payload(username="testuser", email="test@example.com", password=VALID_PASSWORD):
    return {
        "username": username,
        "email": email,
        "create_password": password,
        "confirm_password": password,
    }


def _extract_latest_token_row(db_session, model, user_id):
    return (
        db_session.query(model)
        .filter(model.user_id == user_id)
        .order_by(model.id.desc())
        .first()
    )


def test_signup_success(client, db_session):
    resp = client.post("/signup", json=signup_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True

    user = db_session.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.email_verified is False


def test_signup_duplicate_is_generic_and_case_insensitive(client):
    resp1 = client.post("/signup", json=signup_payload())
    assert resp1.status_code == 201

    # Same username, different case + different email -> still rejected.
    resp2 = client.post(
        "/signup",
        json=signup_payload(username="TestUser", email="other@example.com"),
    )
    assert resp2.status_code == 409
    detail = resp2.json()["detail"]
    assert "username" in detail.lower() and "email" in detail.lower()

    # Same email, different case + different username -> still rejected.
    resp3 = client.post(
        "/signup",
        json=signup_payload(username="anotheruser", email="TEST@EXAMPLE.COM"),
    )
    assert resp3.status_code == 409


def test_signup_rejects_weak_password(client):
    resp = client.post(
        "/signup",
        json=signup_payload(password="alllowercaseletters"),
    )
    assert resp.status_code == 422


def test_signup_rejects_mismatched_passwords(client):
    payload = signup_payload()
    payload["confirm_password"] = "SomethingElse!123"
    resp = client.post("/signup", json=payload)
    assert resp.status_code == 422


def test_login_blocked_before_verification(client):
    client.post("/signup", json=signup_payload())
    resp = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    assert resp.status_code == 403


def test_login_nonexistent_user_matches_wrong_password_status(client):
    """Both should be 401 with the same generic detail — this is the
    behavior that keeps /login from being usable to enumerate accounts."""
    resp_no_user = client.post(
        "/login", json={"identifier": "nobody@example.com", "password": "whatever123!"}
    )
    client.post("/signup", json=signup_payload())
    resp_wrong_pw = client.post(
        "/login", json={"identifier": "testuser", "password": "wrongpass123!"}
    )

    assert resp_no_user.status_code == 401
    assert resp_wrong_pw.status_code == 401
    assert resp_no_user.json()["detail"] == resp_wrong_pw.json()["detail"]


def test_verify_email_then_login_and_me(client, db_session):
    client.post("/signup", json=signup_payload())
    user = db_session.query(User).filter(User.username == "testuser").first()

    token_row = _extract_latest_token_row(db_session, EmailVerificationToken, user.id)
    assert token_row is not None

    # We only have the token's hash stored (by design). Simulate "clicking
    # the emailed link" by minting a token with a known raw value and
    # overwriting the stored hash to match, which is equivalent from the
    # endpoint's point of view (it only ever sees token -> hash -> lookup).
    raw_token = "test-raw-verification-token"
    token_row.token_hash = sha256(raw_token.encode()).hexdigest()
    db_session.commit()

    verify_resp = client.post("/verify-email", json={"token": raw_token})
    assert verify_resp.status_code == 200

    login_resp = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_resp.status_code == 200
    me_body = me_resp.json()
    assert me_body["username"] == "testuser"
    assert me_body["email_verified"] is True


def _signup_and_verify(client, db_session, **kwargs):
    from sqlalchemy import func

    payload = signup_payload(**kwargs)
    client.post("/signup", json=payload)
    user = (
        db_session.query(User)
        .filter(func.lower(User.email) == payload["email"].lower())
        .first()
    )
    user.email_verified = True
    db_session.commit()
    return user


def test_case_insensitive_login(client, db_session):
    _signup_and_verify(client, db_session, username="MixedCase", email="Mixed@Example.com")

    resp = client.post(
        "/login", json={"identifier": "mixedcase", "password": VALID_PASSWORD}
    )
    assert resp.status_code == 200

    resp2 = client.post(
        "/login", json={"identifier": "MIXED@EXAMPLE.COM", "password": VALID_PASSWORD}
    )
    assert resp2.status_code == 200


def test_account_lockout_after_repeated_failures(client, db_session):
    _signup_and_verify(client, db_session)

    # ACCOUNT_LOCKOUT_MAX_ATTEMPTS is set to 3 in tests/conftest.py.
    for _ in range(3):
        resp = client.post(
            "/login", json={"identifier": "testuser", "password": "wrongpass123!"}
        )
        assert resp.status_code == 401

    locked_resp = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    assert locked_resp.status_code == 423


def test_logout_invalidates_token(client, db_session):
    _signup_and_verify(client, db_session)
    login_resp = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/me", headers=headers).status_code == 200

    logout_resp = client.post("/logout", headers=headers)
    assert logout_resp.status_code == 200

    assert client.get("/me", headers=headers).status_code == 401


def test_delete_account(client, db_session):
    _signup_and_verify(client, db_session)
    login_resp = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/delete-account", json={"password": VALID_PASSWORD}, headers=headers
    )
    assert resp.status_code == 200

    login_again = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    assert login_again.status_code == 401


def test_forgot_password_nonexistent_email_is_generic(client):
    resp = client.post("/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 200
    assert "if an account exists" in resp.json()["message"].lower()


def test_forgot_password_and_reset_flow(client, db_session):
    user = _signup_and_verify(client, db_session)

    resp = client.post("/forgot-password", json={"email": "test@example.com"})
    assert resp.status_code == 200

    token_row = _extract_latest_token_row(db_session, PasswordResetToken, user.id)
    assert token_row is not None

    raw_token = "test-raw-reset-token"
    token_row.token_hash = sha256(raw_token.encode()).hexdigest()
    db_session.commit()

    new_password = "N3w!StrongPassword"
    reset_resp = client.post(
        "/reset-password",
        json={
            "token": raw_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )
    assert reset_resp.status_code == 200

    # Reusing the same (now-used) token must fail.
    reuse_resp = client.post(
        "/reset-password",
        json={
            "token": raw_token,
            "new_password": "AnotherOne!234",
            "confirm_password": "AnotherOne!234",
        },
    )
    assert reuse_resp.status_code == 400

    # Old password no longer works, new one does.
    old_login = client.post(
        "/login", json={"identifier": "testuser", "password": VALID_PASSWORD}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/login", json={"identifier": "testuser", "password": new_password}
    )
    assert new_login.status_code == 200


def test_me_requires_auth(client):
    resp = client.get("/me")
    assert resp.status_code in (401, 403)


def test_signup_race_condition_is_handled_cleanly(client):
    """Simulates the TOCTOU race directly: force the *first* commit inside
    /signup to raise IntegrityError (as Postgres's unique index would if a
    concurrent request won the race after both passed the pre-commit
    existence check), and confirm the endpoint turns that into a clean
    409 instead of an unhandled 500.
    """
    from sqlalchemy.exc import IntegrityError

    from app.database import SessionLocal
    from app.main import app, get_db

    class FailFirstCommitSession:
        """Wraps a real Session; the first commit() raises IntegrityError,
        every call after that behaves normally."""

        def __init__(self, real_session):
            self._real = real_session
            self._raised = False

        def __getattr__(self, name):
            return getattr(self._real, name)

        def commit(self):
            if not self._raised:
                self._raised = True
                raise IntegrityError("duplicate key", None, None)
            return self._real.commit()

    real_session = SessionLocal()
    fake_session = FailFirstCommitSession(real_session)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        resp = client.post("/signup", json=signup_payload())
    finally:
        app.dependency_overrides.pop(get_db, None)
        real_session.close()

    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()
