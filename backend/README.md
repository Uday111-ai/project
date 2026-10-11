# AI Auth Demo — Backend

FastAPI backend providing signup, email verification, login, session
("me"), logout, account deletion, and password-reset endpoints, backed by
Postgres. Hardened for production use — see `CHANGELOG.md` for the full
security review and what changed.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy + Postgres (psycopg2) + Alembic migrations
- Argon2 password hashing
- JWT (HS256) bearer auth via `python-jose`
- SMTP email for verification and password-reset links
- slowapi for per-IP rate limiting

## Local setup

1. Install dependencies (uses [uv](https://docs.astral.sh/uv/), or plain pip):
   ```bash
   uv sync
   # or: pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in real values (JWT secret,
   local Postgres URL, SMTP credentials). Never commit `.env`.
3. Make sure a local Postgres instance is running and the database in
   `DATABASE_URL` exists.
4. Create the schema. Two options:
   - **Quick start**: leave `DB_AUTO_CREATE_TABLES=true` (the default) and
     just run the server — tables are created automatically on startup.
   - **Recommended** (matches production): run the Alembic migration
     instead, and set `DB_AUTO_CREATE_TABLES=false`:
     ```bash
     alembic upgrade head
     ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
   API will be available at `http://localhost:8000`, interactive docs at
   `http://localhost:8000/docs`.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run against an isolated SQLite file (`tests/test.db`, recreated
each run) and don't touch your real `DATABASE_URL`. They also disable the
per-IP rate limiter, since several tests deliberately send more requests
to one endpoint than production limits would allow (e.g. testing account
lockout).

## Database migrations (Alembic)

Schema changes now go through Alembic instead of relying on
`Base.metadata.create_all()` (which only creates missing tables and can
never alter existing ones).

```bash
# apply all pending migrations
alembic upgrade head

# after changing a model, generate a new migration
alembic revision --autogenerate -m "describe the change"
# then review the generated file before committing — autogenerate is a
# starting point, not a guarantee, especially for the case-insensitive
# expression indexes on users.username/email (see migrations/versions/0001).
```

`DB_AUTO_CREATE_TABLES` (env var, default `true`) is a dev/test
convenience fallback that runs `Base.metadata.create_all()` on startup
instead. Production (`render.yaml`) sets this to `false` and runs
`alembic upgrade head` in the build step instead, so the two mechanisms
never disagree.

## API endpoints

| Method | Path                        | Auth       | Description                                     |
|--------|-----------------------------|------------|--------------------------------------------------|
| GET    | `/`                         | —          | Health check                                     |
| GET    | `/check-username`           | —          | Live username-availability check for the signup form |
| POST   | `/signup`                   | —          | Create account (`201` on success)                |
| POST   | `/verify-email`             | —          | Verify an account using the emailed token        |
| POST   | `/resend-verification-email`| —          | Re-send the verification email                   |
| POST   | `/login`                    | —          | Log in, returns a JWT access token               |
| GET    | `/me`                       | Bearer JWT | Get the current authenticated user               |
| POST   | `/logout`                   | Bearer JWT | Log out (invalidates the current token)          |
| POST   | `/delete-account`           | Bearer JWT | Delete the current account                       |
| POST   | `/forgot-password`          | —          | Request a password-reset email                   |
| POST   | `/reset-password`           | —          | Reset password using the emailed token           |

Every protected route (`/me`, `/logout`, `/delete-account`, and any future
one) expects `Authorization: Bearer <token>`.

### Request bodies (summary)

- `GET /check-username?username=...`: query param, 3–30 chars
- `POST /signup`: `{ username, email, create_password, confirm_password }`
- `POST /verify-email`: `{ token }`
- `POST /resend-verification-email`: `{ email }`
- `POST /login`: `{ identifier, password }` — `identifier` is either the account's email or username, matched case-insensitively
- `POST /logout`: no body
- `POST /delete-account`: `{ password }` — current password, required to confirm
- `POST /forgot-password`: `{ email }`
- `POST /reset-password`: `{ token, new_password, confirm_password }`

Passwords must be 8–128 characters, include at least one digit and one
special character. Optionally (see `CHECK_PASSWORD_PWNED` below), they're
also checked against known-breached passwords.

### ⚠️ Breaking change: email verification

**New accounts must verify their email before they can log in.** On
signup, a verification link (`{FRONTEND_URL}/verify-email?token=...`) is
emailed to the address given; `POST /login` returns `403` with
`"Please verify your email address before logging in."` until the account
verifies via `POST /verify-email`. If the frontend doesn't have a
`/verify-email` page yet, it needs one before this deploys — it should
read the `token` query param and `POST` it to this endpoint.

If this friction isn't acceptable for your product, set
`REQUIRE_EMAIL_VERIFICATION=false` — accounts are still tagged
`email_verified` (returned from `/me`), just not gated on it.

### Account lockout

In addition to the existing per-IP rate limits, each **account** now
locks for `ACCOUNT_LOCKOUT_DURATION_MINUTES` (default 15) after
`ACCOUNT_LOCKOUT_MAX_ATTEMPTS` (default 5) consecutive failed logins,
regardless of which IP the attempts come from. `POST /login` returns
`423 Locked` while an account is locked. A successful login, or a
successful password reset, clears the counter.

### Rate limits

To slow down brute-force and spam abuse, these endpoints are rate-limited
per IP address and return `429 Too Many Requests` once exceeded:

| Endpoint | Limit |
|---|---|
| `POST /signup` | 5 per hour |
| `POST /login` | 10 per minute |
| `POST /forgot-password` | 5 per hour |
| `POST /reset-password` | 10 per hour |
| `POST /resend-verification-email` | 5 per hour |
| `GET /check-username` | 30 per minute |

If your frontend testing hits these while iterating quickly, either wait
it out or temporarily raise the limits in `main.py`.

### Notes on `/logout` and `/delete-account`

- Access tokens are stateless JWTs, so there's nothing to revoke server-side
  on its own. `/logout` invalidates the token by bumping the user's
  `token_version` (the same mechanism already used when a password is
  reset) — every token issued before the logout call stops working, and the
  user must log in again to get a new one.
- `/delete-account` requires the current password in the body as a
  confirmation step, deletes any pending password-reset and
  email-verification tokens for that user, then deletes the user row.

### Scheduled cleanup

`password_reset_tokens` and `email_verification_tokens` accumulate rows
over time. `scripts/cleanup_expired_tokens.py` deletes expired/used rows
from both tables and is meant to run on a schedule, not in the request
path. `render.yaml` wires this up as a daily Render Cron Job; if you're
not on Render, run it via a regular crontab entry instead:

```bash
0 3 * * * cd /path/to/backend && /path/to/venv/bin/python scripts/cleanup_expired_tokens.py
```

### Live username-availability check

`GET /check-username?username=...` supports the signup form showing
"available"/"taken" as the user types, with alternative suggestions when
taken.

- Public, read-only, no DB writes — one indexed lookup for the
  availability check, plus (only when taken) **one** additional batched
  query checking 5–8 server-generated candidate variations
  (`app/core/username_suggestions.py`), returning the first 3–4 that come
  back free. Never more than two queries total, regardless of how many
  candidates are generated.
- Reuses the existing case-insensitive functional index on
  `LOWER(username)` from the hardening pass — **no new index or
  migration** was needed or added for this feature.
- Rate-limited at 30/minute per IP — more generous than `/signup` since
  it's read-only and meant to be called on nearly every debounced typing
  pause. See the inline comment above the route in `main.py` for the
  full reasoning if this ever needs retuning.
- **Accepted trade-off, not an oversight:** an availability-check
  endpoint is inherently a username-enumeration oracle — that's what
  "check if X is taken" means. The only mitigation here is the rate
  limit; there's no attempt to obscure results or add per-account
  lockout (which wouldn't make sense for an unauthenticated, no-signup
  lookup anyway). This is standard and expected for this class of UX
  feature (most signup forms with live-availability checks work the same
  way) — flagging it explicitly rather than silently.
- This endpoint is UX only. `/signup` still performs its own
  case-insensitive check and still relies on the database's unique index
  + `IntegrityError` handling as the actual source of truth — a race
  between a "the name's free!" check and a real signup a few seconds
  later is expected and already handled there.

**Frontend contract this endpoint is designed around** (for whichever
client wires up the form): debounce 300–500ms after typing stops before
calling it; cancel any in-flight request when a newer one starts so a
slow stale response can't overwrite a fresher result; never block
moving to the next field or further typing on this check; treat a
network failure on this endpoint as silent/neutral, not a hard error.

## Environment variables

See `.env.example` for the full list with defaults and explanations.
New in this hardening pass:

| Variable | Default | Purpose |
|---|---|---|
| `REQUIRE_EMAIL_VERIFICATION` | `true` | Gate `/login` on `email_verified` |
| `ACCOUNT_LOCKOUT_MAX_ATTEMPTS` | `5` | Failed logins before an account locks |
| `ACCOUNT_LOCKOUT_DURATION_MINUTES` | `15` | How long a lockout lasts |
| `CHECK_PASSWORD_PWNED` | `false` | Opt-in HaveIBeenPwned check on new passwords |
| `DB_AUTO_CREATE_TABLES` | `true` | Dev-only `create_all()` fallback — see Migrations above |

## CORS

Allowed frontend origins are controlled by env vars, not hardcoded:

- `CORS_ORIGINS` — comma-separated list of allowed origins (preferred).
- Falls back to `FRONTEND_URL`, then `http://localhost:3000`.

When testing against a deployed frontend, add its URL to `CORS_ORIGINS`
in the environment (Render dashboard or `.env` locally).

## Security headers

Every response includes `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and
`Strict-Transport-Security`. Belt-and-suspenders since this API already
sits behind Render's HTTPS edge, but cheap to set explicitly.

## Deploying to Render

This repo includes a `render.yaml` blueprint (web service + Postgres
instance + a daily cron job for token cleanup):

1. Push this repo to GitHub (see workflow below).
2. In Render, choose **New > Blueprint**, point it at the repo, and it will
   read `render.yaml` and provision the web service, database, and cron
   job together.
3. In the Render dashboard, set the secret env vars flagged `sync: false`
   in `render.yaml`:
   - `JWT_SECRET_KEY` — generate a fresh one for this environment. The app
     will refuse to start without a value at least 32 characters long.
   - `FRONTEND_URL` / `CORS_ORIGINS` — your deployed frontend's URL.
   - `SMTP_USERNAME` / `SMTP_PASSWORD` — your SMTP/Gmail App Password.
   - `DATABASE_URL` is wired automatically from the provisioned Postgres.
4. Deploy. Render builds with
   `pip install -r requirements.txt && alembic upgrade head` and runs
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

   **If you're deploying this update on top of an existing database** that
   was created via the old `Base.metadata.create_all()` path (i.e. it
   already has `users` and `password_reset_tokens` but never ran a
   migration before), running `alembic upgrade head` cold will try to
   create tables that already exist. In that case, before the first
   deploy of this version, run once against that database:
   ```bash
   alembic stamp head
   ```
   then edit `migrations/versions/0001_initial_schema.py`'s `upgrade()`
   to only add what's actually missing (the new columns, the new
   `email_verification_tokens` table, the new indexes) rather than
   creating `users` from scratch — or, simpler, just apply those specific
   `ALTER TABLE` / `CREATE INDEX` statements by hand once, then stamp.
   (This repo has no production data yet, so this path is included for
   completeness rather than because it's needed right now.)

(No blueprint? You can instead create the Web Service, Postgres instance,
and Cron Job manually in the Render dashboard using the same
build/start commands and env vars above.)

## Git workflow for this project

```bash
# from the backend/ folder, with git already initialized
git add .
git commit -m "Backend: harden auth to production grade"

# create the branch, if not already on it
git checkout -b backend

# add your GitHub remote (only needed once)
git remote add origin <your-repo-url>

git push -u origin backend
```

Then open a PR from `backend` into `main` on GitHub (or merge directly if
you're working solo), and deploy `main` on Render as above.

