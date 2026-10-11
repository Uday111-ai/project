# Feature: live username-availability check

Added `GET /check-username?username=...` so the signup form can show
"available"/"taken" (with alternative suggestions) as the user types,
before they finish the form. Full write-up:

- **New files:** `app/core/username_suggestions.py` (candidate
  generation, pure string logic, no DB access) and
  `tests/test_check_username.py` (7 tests: available, taken-with-real-
  suggestions, case-insensitivity, length-bound 422s, no-DB-write,
  never-suggest-a-taken-name via a monkeypatched deterministic
  generator, and rate-limit tripping).
- **Changed files:** `app/main.py` (new route), `app/schemas/user.py`
  (new `CheckUsernameResponse`), `README.md`.
- **No new database index or migration.** Confirmed via
  `EXPLAIN QUERY PLAN` against the resulting query
  (`SEARCH users USING INDEX ix_users_username_lower (<expr>=?)`) — it
  reuses the case-insensitive functional index on `LOWER(username)`
  added in the hardening pass, exactly as instructed. No index-related
  change of any kind was made in this pass.
- **Query cost is bounded and low:** one indexed lookup for the
  availability check itself; only when taken, one *additional* batched
  `IN (...)` query against 5–8 generated candidates (never one query per
  candidate). Verified live: a taken-username request returned real,
  currently-free suggestions, each independently re-checked against the
  DB by the test suite (not just trusted from the endpoint's own claim).
- **Rate limit: `30/minute` per IP, same key function as the rest of the
  API (`get_remote_address`).** Reasoning (also inline in `main.py`
  above the decorator, so it doesn't need re-deriving later): a 300–
  500ms frontend debounce means a fast typist triggers roughly one
  request per half-second of pause — well under 30/min for a single
  signup attempt. The ceiling exists to blunt scripted enumeration, not
  to interfere with real typing. Chosen deliberately more generous than
  `/signup`'s `5/hour`, since this is read-only and designed for
  repeated calls, unlike an actual signup attempt. Live-tested by firing
  35 rapid requests: the 30th tripped `429`, confirming the limit is
  actually wired up and firing at roughly the configured threshold (not
  just present-but-inert).
- **Honest trade-off, stated explicitly per the task's ask:** this
  endpoint is a username-enumeration oracle by design — "check if a
  name is taken" and "let you enumerate names" are the same capability.
  The rate limit is the *only* mitigation, and that's accepted as
  standard for this class of UX feature (most signup forms with live
  checks work this way), not an oversight. No attempt was made to
  obscure results, add CAPTCHA, or otherwise disguise this, since doing
  so would break the feature's actual purpose.
- **Did not touch `/signup`'s contract or behavior.** It still performs
  its own case-insensitive existence check and still relies on the
  database's unique index + `IntegrityError` handling (from the earlier
  TOCTOU fix) as the real source of truth. A race between a "the name's
  free!" check here and a signup submitted seconds later is expected —
  this endpoint was never meant to be authoritative, and nothing about
  its addition changes what already handles that race downstream.

Live-tested end to end against a real `uvicorn` process, in addition to
the automated tests: signup → available check → taken check → case-
insensitive taken check → both length-bound 422s → 35-request rate-limit
run → `EXPLAIN QUERY PLAN` on the underlying query. Full test suite
(22 tests total, including the 15 from the hardening pass) passes.

---

# Security hardening changelog

Full independent review of `app/` plus the itemized list from the task
brief. Organized the same way the brief was: High / Medium / Low, plus
things found independently. Every item below was implemented and
exercised — either by the automated test suite (`tests/test_auth.py`,
15 tests, all passing) or by a live run against `uvicorn` (signup →
verify → login → `/me`, wrong-password/nonexistent-user timing
comparison, lockout, forgot/reset-password round trip) during this
review.

## High priority

1. **Timing side-channel on `/login` — fixed.**
   `password_hash_to_check` is now always set (to the real hash if the
   user exists, to a fixed dummy Argon2 hash computed once at import time
   if not), and `verify_password()` runs unconditionally before either
   branch is decided. Live-tested: nonexistent-user and wrong-password
   requests came back in the same ~150–190ms band (dominated by the
   Argon2 verify itself), instead of the near-instant vs. hundreds-of-ms
   gap in the original.

2. **Timing/behavior side-channel on `/forgot-password` — fixed.**
   The SMTP send now runs via `BackgroundTasks` on both branches, so the
   response returns before any email send happens either way. The
   "user doesn't exist" branch also does an equivalent-cost dummy hash
   computation instead of returning immediately, to avoid leaking
   existence through the (much smaller) remaining gap of "no DB insert."

3. **Case-sensitive username/email lookups — fixed.**
   `User.username`/`User.email` are compared via `func.lower(...)`
   everywhere (signup uniqueness check, login lookup, forgot-password,
   resend-verification). Uniqueness is enforced by the database itself
   via case-insensitive **expression indexes**
   (`CREATE UNIQUE INDEX ... ON users (lower(username))`, same for
   email) rather than only checked in application code — this also
   closes a narrower race that a plain app-level check alone wouldn't
   (see #4). Original casing is preserved for display.

4. **Signup race condition (TOCTOU) — fixed.**
   The pre-commit existence check remains (fast path, good error
   message), but `db.commit()` on `/signup` is now wrapped in
   `try/except IntegrityError`, which rolls back and returns a clean
   `409` instead of an unhandled `500`. Verified with a dedicated test
   that forces the first `commit()` to raise `IntegrityError` and
   confirms the response is `409`, not a crash.

5. **No email verification — added.**
   New `email_verified` column, new `email_verification_tokens` table
   (same hashed-token/expiry/used pattern as password reset), new
   `POST /verify-email` and `POST /resend-verification-email` endpoints.
   **Decision:** `/login` blocks unverified accounts (`403`) by default,
   controlled by `REQUIRE_EMAIL_VERIFICATION` (default `true`) — chosen
   over "allow login but flag it" because this is explicitly a
   production-grade auth hardening pass, and blocking is the safer
   default; teams that need the softer behavior can flip the env var.
   **This is a breaking change** — flagged in the README with what the
   frontend needs (a `/verify-email` page that POSTs the token).

6. **`verify_password` only caught `VerifyMismatchError` — fixed.**
   Now catches `VerifyMismatchError` (→ `False`) and any other exception
   (→ logged via `logger.exception`, then `False`) so a malformed stored
   hash can never surface as an unhandled `500`.

## Medium priority

7. **No index on `password_reset_tokens.user_id` — fixed.**
   Added `index=True` on the column, and the same on the new
   `email_verification_tokens.user_id`. Present in the Alembic migration.

8. **No cleanup of expired/used tokens — fixed.**
   `scripts/cleanup_expired_tokens.py`, meant to run on a schedule (wired
   into `render.yaml` as a daily Cron Job) rather than the request path.
   Deletes expired-or-used rows from both token tables. Tested directly:
   seeded an expired row, ran the script, confirmed it was removed.

9. **No migrations tool — fixed.**
   Alembic is now set up (`alembic.ini`, `migrations/env.py`, initial
   migration `migrations/versions/0001_initial_schema.py`). Since this
   app has no production data yet, the initial migration creates the
   full current schema directly (including the fields added in this
   pass) rather than replaying incremental history — see the migration
   file's docstring. Verified: `alembic upgrade head` runs cleanly
   against a fresh SQLite DB and produces the expected tables/indexes.
   `render.yaml`'s build command now runs `alembic upgrade head`; the
   app's own `Base.metadata.create_all()` is now gated behind
   `DB_AUTO_CREATE_TABLES` (default `true` for local/dev convenience,
   `false` in `render.yaml`) so the two mechanisms can't disagree in
   production.

10. **No per-account lockout — fixed.**
    New `failed_login_attempts` / `locked_until` columns on `User`.
    After `ACCOUNT_LOCKOUT_MAX_ATTEMPTS` (default 5) consecutive failed
    logins, the account locks for `ACCOUNT_LOCKOUT_DURATION_MINUTES`
    (default 15) regardless of source IP — `/login` returns `423`.
    Resets on successful login or successful password reset. Live-tested
    and covered by an automated test.

11. **No audit/security logging — fixed.**
    `app/core/audit.py` emits structured (JSON-line) log events via the
    standard `logging` module for: signup, login success/failure (with
    reason), account lockout, blocked-while-locked, blocked-unverified,
    logout, account deletion, password reset request/completion, email
    verification, and verification-email resend. Only IDs, booleans, and
    short reason codes are logged — never passwords, tokens, or token
    hashes.

## Low priority / polish

- **Signup existence leak — resolved by making both messages generic.**
  `/signup` now returns one message ("An account with this username or
  email already exists") for both collisions, closing the enumeration
  vector where an attacker could distinguish "email taken" from
  "username taken" to test guessed emails.
- **HaveIBeenPwned check — added, opt-in.** `is_password_pwned()` in
  `app/core/security.py` uses the k-anonymity range API (only a 5-char
  hash prefix ever leaves the server). Off by default
  (`CHECK_PASSWORD_PWNED=false`) since it's a live network call on the
  request path and some environments can't reach it; fails open (never
  blocks signup) if the API is unreachable.
- **Refresh tokens — deliberately not implemented.** The brief asked to
  "consider" this, not to build it. Sessions still hard-expire after 30
  minutes. Adding refresh tokens is a real architectural addition
  (rotation, revocation, storage) that changes the client contract
  significantly; it's flagged here as a genuine open question for the
  product rather than folded into this pass. If it turns out to be
  needed, the existing `token_version` mechanism generalizes reasonably
  well to it.
- **Dead `Header` import — removed.**
- **No automated test suite — added.** `tests/test_auth.py` (15 tests)
  covers signup (success, case-insensitive duplicate, weak password,
  mismatched passwords, the TOCTOU race path), login (blocked before
  verification, nonexistent-user/wrong-password status parity,
  case-insensitive identifier, lockout after repeated failures), `/me`
  auth requirement, logout token invalidation, account deletion, and the
  full forgot-password → reset-password round trip including rejecting a
  reused token. Uses an isolated SQLite DB and a disabled rate limiter so
  it doesn't depend on Postgres or trip production rate limits.
- **No standard security headers — added.** Middleware sets
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and
  `Strict-Transport-Security` on every response.

## Found independently (not in the original list)

- **`/me` didn't expose `email_verified`.** Added, since the frontend
  needs it to prompt "please verify your email" states.
- **Password-reset and email-verification tokens weren't cleared on
  account deletion for the new token table.** `/delete-account` now also
  deletes any pending `email_verification_tokens` rows for that user
  (mirroring the existing cleanup of `password_reset_tokens`), so it
  doesn't leave orphaned FK rows behind (SQLite/Postgres would both
  reject the user delete otherwise once the FK is enforced).
- **Successful password reset didn't clear lockout state.** A user who
  gets locked out and then legitimately resets their password via email
  would otherwise stay locked until the timer expired even though
  they've just proven account ownership. `/reset-password` now clears
  `failed_login_attempts` and `locked_until`.
- **`.env.example` / `pyproject.toml` / `requirements.txt` / `uv.lock`**
  updated for the new dependencies (`alembic`, `httpx`) and new env vars;
  `uv.lock` was regenerated (not hand-edited) to stay consistent.

## Final verdict

**Materially closer to production-ready than the MVP, and safe to deploy
behind the caveats below — but I wouldn't call it fully "production-ready
with nothing left to decide" without a human sign-off on a few product
questions baked into this review:**

What's solid now: no known timing/enumeration leak on login or
forgot-password, the signup race is handled cleanly, case-insensitive
identity is enforced at the DB level (not just app code), email
ownership is verified before login, brute force is mitigated at both the
IP and account level, malformed-hash and duplicate-key edge cases can't
crash the process, schema changes go through Alembic instead of an
unversioned `create_all()`, token tables no longer grow unbounded, and
there's a real automated test suite plus a live-tested run of every
changed endpoint.

What still needs a human decision, not more code:

- **Whether blocking login on unverified email is the right call for
  this product.** I made a judgment call (see #5) — a founder/PM should
  confirm it, since it changes the signup funnel.
- **Refresh tokens** — genuinely unresolved, flagged above.
- **SMTP reliability**: the app degrades gracefully (logs, doesn't crash,
  doesn't reveal account existence) if SMTP is unreachable, but a user
  who signs up during an SMTP outage will not be able to verify until
  someone notices and they use `/resend-verification-email`. There's no
  alerting on repeated send failures — worth adding once this has real
  traffic (e.g. an audit-log-based alert on a burst of email-send
  failures).
- **This was tested against SQLite, not Postgres.** The code targets
  Postgres-specific behavior correctly as far as I can verify statically
  (the expression indexes, `IntegrityError` handling, and Alembic
  migration all use portable SQL and were chosen specifically to work
  identically on both), but I don't have a Postgres instance available
  in this environment to run the suite against directly. Recommend
  running `pytest` once against a real Postgres `DATABASE_URL` before
  the first production deploy, and definitely before relying on the
  Render blueprint's `alembic upgrade head` build step in anger.
- **Load/concurrency testing under real traffic** hasn't been done —
  the fixes here address the specific race and DoS-shaped issues named
  in the brief, not a general load test.
