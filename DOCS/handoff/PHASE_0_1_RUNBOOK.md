# Phase 0+1 Runbook

**Updated:** 2026-04-24 (Phase 0+1.5 hardening)

## Prerequisites
- Python 3.11+ (tested with 3.11.9)
- Node.js 20+
- Docker + Docker Compose (optional, for containerized startup)

---

## Option A: Local Development (no Docker required)

The backend defaults to SQLite for local dev. No PostgreSQL needed.

### 1. Start the backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run Alembic migration (creates tables)
alembic upgrade head

# Seed demo data
python -m seed

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 3. Run smoke tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Option B: Docker Compose

```bash
cd C:\Users\Rotem\projects\FINRLX

# Start all services (runs migrations + seed automatically)
docker compose up --build
```

Docker Compose runs `alembic upgrade head && python -m seed` before starting the backend.

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

---

## Option C: PostgreSQL (manual)

If you want to use PostgreSQL instead of SQLite:

```bash
# Start Postgres (via Docker or local install)
docker run -d --name finrlx-pg \
  -e POSTGRES_USER=finrlx \
  -e POSTGRES_PASSWORD=finrlx \
  -e POSTGRES_DB=finrlx \
  -p 5432:5432 \
  postgres:16-alpine

# Set DATABASE_URL in backend/.env
echo 'DATABASE_URL=postgresql+asyncpg://finrlx:finrlx@localhost:5432/finrlx' > backend/.env

# Then follow Option A steps 1-3
```

---

## Database Management

**Migrations are the source of truth for the schema.**

```bash
cd backend

# Apply migrations
alembic upgrade head

# Check current migration state
alembic current

# Downgrade (if needed)
alembic downgrade base
```

The seed script does NOT create tables. Run `alembic upgrade head` first.

---

## Seed Data

The seed script (`backend/seed.py`) creates:
- 10 large-cap US equities (AAPL, MSFT, GOOGL, AMZN, JPM, JNJ, XOM, PG, NVDA, V)
- 1 universe ("US Large Cap Core")
- 1 published recommendation with 10 target weights
- 1 selection run, 1 allocation result, 1 timing result, 1 risk overlay result

The seed is idempotent.

---

## URLs

| Service | URL |
|---|---|
| Frontend (Overview) | http://localhost:3000 |
| Backend Health | http://localhost:8000/health |
| API v1 Health | http://localhost:8000/api/v1/health |
| API Overview | http://localhost:8000/api/v1/overview |
| Current Recommendation | http://localhost:8000/api/v1/recommendations/current |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Verification Checklist

- [ ] `python -m pytest tests/ -v` — all 6 smoke tests pass
- [ ] `alembic upgrade head` — migration creates 18 tables
- [ ] `python -m seed` — seeds 10 assets + 1 recommendation
- [ ] `GET /health` returns `{"status": "ok", "version": "0.1.0"}`
- [ ] `GET /api/v1/health` returns `status=ok, database=connected`
- [ ] `GET /api/v1/overview` returns recommendation with 10 positions, confidence triplet
- [ ] `GET /api/v1/recommendations/current` returns weights for AAPL, MSFT, etc.
- [ ] `GET /docs` serves Swagger UI
- [ ] Frontend builds clean (`npx next build` — 7 routes, 0 errors)
- [ ] Frontend at http://localhost:3000 shows Overview page with data

---

## Troubleshooting

**Backend won't start:**
- Default uses SQLite (no external DB needed)
- For PostgreSQL, set `DATABASE_URL` in `backend/.env`
- Run `pip install -r requirements.txt` for all deps

**Migration fails:**
- Ensure you're in the `backend/` directory
- Ensure `alembic.ini` exists and `migrations/` folder is present

**Seed fails:**
- Run `alembic upgrade head` first — seed does not create tables

**Frontend won't start:**
- Run `npm install` in `frontend/`
- Ensure Node 20+ is installed

**Overview shows "Connection Error":**
- Backend must be running on port 8000
- Next.js rewrites `/api/*` to `http://localhost:8000/api/*`
