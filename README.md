# Auth Module

Self-contained authentication service: FastAPI backend, React + TypeScript frontend, PostgreSQL, Alembic migrations.

## Structure
- `backend/` - FastAPI app, migrations, tests, scripts
- `frontend/` - React + Vite client
- `docker-compose.yml` - local PostgreSQL

## Setup

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in values
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
copy .env.example .env   # fill in values
npm run dev
```

### Tests
```bash
cd backend
pytest
```

## Configuration
Copy each `.env.example` to `.env`. Never commit `.env`.

See `backend/README.md` for API details and deployment.
