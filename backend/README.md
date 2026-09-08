# AI Auth Demo — Backend

FastAPI backend providing signup, login, session ("me"), and password-reset
(forgot/reset) endpoints, backed by Postgres.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy + Postgres (psycopg2)
- Argon2 password hashing
- JWT (HS256) bearer auth via `python-jose`
- SMTP email for password-reset links

## Local setup

1. Install dependencies (uses [uv](https://docs.astral.sh/uv/), or plain pip):
   ```bash
   uv sync
   # or: pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in real values (JWT secret,
   local Postgres URL, SMTP credentials). Never commit `.env`.
3. Make sure a local Postgres instance is running and the database in
   `DATABASE_URL` exists. Tables are created automatically on startup.
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
   API will be available at `http://localhost:8000`, interactive docs at
   `http://localhost:8000/docs`.

## API endpoints

| Method | Path               | Auth       | Description                              |
|--------|--------------------|------------|-------------------------------------------|
| GET    | `/`                | —          | Health check                              |
| POST   | `/signup`          | —          | Create account (`201` on success)         |
| POST   | `/login`           | —          | Log in, returns a JWT access token        |
| GET    | `/me`              | Bearer JWT | Get the current authenticated user        |
| POST   | `/logout`          | Bearer JWT | Log out (invalidates the current token)   |
| POST   | `/delete-account`  | Bearer JWT | Delete the current account                |
| POST   | `/forgot-password` | —          | Request a password-reset email            |
| POST   | `/reset-password`  | —          | Reset password using the emailed token    |

Every protected route (`/me`, `/logout`, `/delete-account`, and any future
one) expects `Authorization: Bearer <token>`.

### Request bodies (summary)

- `POST /signup`: `{ username, email, create_password, confirm_password }`
- `POST /login`: `{ email, password }`
- `POST /logout`: no body
- `POST /delete-account`: `{ password }` — current password, required to confirm
- `POST /forgot-password`: `{ email }`
- `POST /reset-password`: `{ token, new_password, confirm_password }`

Passwords must be 8+ characters, include at least one digit and one
special character.

### Notes on `/logout` and `/delete-account`

- Access tokens are stateless JWTs, so there's nothing to revoke server-side
  on its own. `/logout` invalidates the token by bumping the user's
  `token_version` (the same mechanism already used when a password is
  reset) — every token issued before the logout call stops working, and the
  user must log in again to get a new one.
- `/delete-account` requires the current password in the body as a
  confirmation step, deletes any pending password-reset tokens for that
  user, then deletes the user row.

## CORS

Allowed frontend origins are controlled by env vars, not hardcoded:

- `CORS_ORIGINS` — comma-separated list of allowed origins (preferred).
- Falls back to `FRONTEND_URL`, then `http://localhost:3000`.

When testing against a deployed frontend, add its URL to `CORS_ORIGINS`
in the environment (Render dashboard or `.env` locally).

## Deploying to Render

This repo includes a `render.yaml` blueprint (web service + free Postgres
instance):

1. Push this repo to GitHub (see workflow below).
2. In Render, choose **New > Blueprint**, point it at the repo, and it will
   read `render.yaml` and provision the web service + database together.
3. In the Render dashboard, set the secret env vars flagged `sync: false`
   in `render.yaml`:
   - `JWT_SECRET_KEY` — generate a fresh one for this environment.
   - `FRONTEND_URL` / `CORS_ORIGINS` — your deployed frontend's URL.
   - `SMTP_USERNAME` / `SMTP_PASSWORD` — your SMTP/Gmail App Password.
   - `DATABASE_URL` is wired automatically from the provisioned Postgres.
4. Deploy. Render builds with `pip install -r requirements.txt` and runs
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

(No blueprint? You can instead create the Web Service and Postgres
instance manually in the Render dashboard using the same build/start
commands and env vars above.)

## Git workflow for this project

```bash
# from the backend/ folder, with git already initialized
git add .
git commit -m "Backend: auth API ready for review/deploy"

# create the branch, if not already on it
git checkout -b backend

# add your GitHub remote (only needed once)
git remote add origin <your-repo-url>

git push -u origin backend
```

Then open a PR from `backend` into `main` on GitHub (or merge directly if
you're working solo), and deploy `main` on Render as above.
