# AERIS - Autonomous Emergency Response & Green Corridor System

**Problem Statement:** SIH-26205
**Theme:** Transportation & Logistics (Software Category)
**Team:** Port2Code (DS10)

AERIS dispatches ambulances through preempted green corridors, reroutes them around live traffic using Mappls, and warns only the drivers ahead of the ambulance in its specific lane. A fail-safe watchdog reverts signals to normal operation if GPS is lost. Citizens can file hazard reports; corroboration is scored and surfaced to operators.

## Repository structure

```
aeris/
  backend/             # FastAPI + Motor + SlowAPI + scikit-learn
    app/
      main.py          # FastAPI entrypoint with all 19 security checks
      config.py        # Pydantic settings + env var validation at startup
      database.py      # Motor async MongoDB + JSON schema validators
      models/          # Pydantic request/response models
      routes/          # auth, dispatch, routes_api, signals, hazards, citizens, ml, websocket
      security/        # JWT, RBAC, rate limiting, CSP, CSRF, sanitisation, security headers
      services/        # Mappls, Firebase, ML risk engine
    requirements.txt
    .env.example
  frontend/            # React 18 + Vite + TypeScript + Tailwind + TanStack Query
    src/
      App.tsx          # Router with lazy-loaded pages + role guards
      api/             # Typed API client (CSRF + JWT refresh built-in)
      components/       # Seo, Breadcrumbs, Loading
      context/         # AuthContext
      layouts/         # RootLayout (header, footer, nav)
      pages/           # Home, Login, Register, EmergencyHud, TrafficControl, CitizenReporting, Terms, Privacy, NotFound
    public/            # robots.txt, sitemap.xml, llms.txt, favicon.ico
    vite.config.ts
    package.json
  .gitignore
  README.md
```

## Prerequisites

- Python 3.11 or newer
- Node 18 or newer
- MongoDB 6 or newer running locally (or a MongoDB Atlas URI)
- Redis 6 or newer (used for rate limiting; optional in development)

## How to run locally

### 1. Start MongoDB and Redis

If you have Docker:

```
docker run -d --name aeris-mongo -p 27017:27017 mongo:7
docker run -d --name aeris-redis -p 6379:6379 redis:7
```

If you are on macOS with Homebrew:

```
brew services start mongodb-community
brew services start redis
```

### 2. Configure backend environment

```
cd aeris/backend
cp .env.example .env
# Fill in real values. Required for dev: SECRET_KEY, MONGO_URI.
# Required for prod: SECRET_KEY, CSRF_SECRET, MONGO_URI, MAPPLS_API_KEY, CORS_ALLOWED_ORIGINS.
```

Generate strong secrets:

```
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Install and run the backend

```
cd aeris/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API is now available at `http://127.0.0.1:8000`.
Swagger docs (dev only): `http://127.0.0.1:8000/api/docs`.
Health check: `http://127.0.0.1:8000/api/v1/health`.

### 4. Install and run the frontend

```
cd aeris/frontend
npm install
cp .env.example .env.local
npm run dev
```

The frontend is now available at `http://localhost:5173`.
The Vite dev server proxies `/api` and `/ws` to the backend.

### 5. Seed an admin user

There is no admin self-registration route. Use this Python one-liner from inside the backend virtualenv to create the first admin:

```
python -c "
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timezone

pwd = CryptContext(schemes=['argon2','bcrypt'], deprecated='auto')

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['aeris']
    await db.users.insert_one({
        'email': 'admin@aeris.local',
        'name': 'AERIS Admin',
        'role': 'admin',
        'password_hash': pwd.hash('ChangeMeNow!2026'),
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    })
    print('Admin seeded. Email: admin@aeris.local')

asyncio.run(main())
"
```

Sign in at `http://localhost:5173/login` with that account.

## API keys needed

To use the production-grade features you will need credentials for the following services. The application will run without them in development (the route endpoints return a 502 from the upstream provider).

| Service | Where to get it | What we use it for | Required env vars |
| --- | --- | --- | --- |
| Mappls API | https://www.mappls.com/api-sdk | Routing, traffic, ETA, geocoding | `MAPPLS_API_KEY`, `MAPPLS_CLIENT_ID`, `MAPPLS_CLIENT_SECRET` |
| Firebase Cloud Messaging | https://console.firebase.google.com | 500m heading-filtered push alerts | `FIREBASE_CREDENTIALS_PATH` (Admin SDK JSON) or `FCM_SERVER_KEY` (legacy) |
| MongoDB Atlas (optional) | https://www.mongodb.com/atlas | Hosted database if you do not run MongoDB locally | `MONGO_URI` |
| Redis Cloud (optional) | https://redis.com/cloud | Hosted rate limiting backend | `REDIS_URL` |

## How to provide the API keys

1. Get the credentials from each provider's console.
2. Open `aeris/backend/.env` in a text editor.
3. Paste each value into the matching variable. Do not wrap values in quotes.
4. Save the file and restart `uvicorn` so the new env vars are validated and loaded.
5. Never commit the `.env` file. The provided `.gitignore` already excludes it.

If you prefer to keep secrets out of disk entirely, export them as shell environment variables before running uvicorn:

```
export MAPPLS_API_KEY="..."
export MAPPLS_CLIENT_ID="..."
export MAPPLS_CLIENT_SECRET="..."
uvicorn app.main:app --reload
```

The Pydantic Settings layer will read from environment first, then fall back to `.env`.

## Images

The frontend currently does not require any images. The custom favicon is generated programmatically and stored in `frontend/public/favicon.ico`. If you want a custom logo:

1. Place an SVG file at `frontend/src/assets/aeris-logo.svg` (or PNG).
2. Update `frontend/src/layouts/RootLayout.tsx` to import it and render an `<img>` with descriptive alt text.
3. Do not use AI-generated raster images per the UI rules in the project context.

Hazard report photos uploaded by citizens are stored by the backend under `backend/uploads/`. Those are runtime artifacts, not committed assets.

## Production checklist

Before deploying:

- Set `APP_ENV=production` in the backend `.env`.
- Set `DEBUG=False`, `SECURE_COOKIES=True`, `ENABLE_SWAGGER=False`.
- Set `CORS_ALLOWED_ORIGINS` to the exact list of frontend origins (comma-separated).
- Set `PUBLIC_BASE_URL` and `BACKEND_BASE_URL` to the production HTTPS URLs.
- Configure Nginx (or equivalent) for SSL termination and HSTS. The backend already sets HSTS in production.
- Run the backend with multiple Uvicorn workers behind Gunicorn:

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

- Build the frontend with `npm run build`. Source maps are disabled (`sourcemap: false` in `vite.config.ts`).
- Deploy the contents of `frontend/dist/` to a static host with the canonical domain configured.
- Update `frontend/public/robots.txt` and `frontend/public/sitemap.xml` with the production domain.

## Security checklist mapping (all 19 enforced)

| # | Check | Where it lives |
| --- | --- | --- |
| 1 | Hide API keys | `backend/app/config.py`, `backend/.env` |
| 2 | Validate env vars at startup | `backend/app/config.py` `_validate_required` |
| 3 | Strict .gitignore | `aeris/.gitignore` |
| 4 | Protect admin routes | `backend/app/security/rbac.py` `require_roles(Role.ADMIN)` |
| 5 | JWT auth | `backend/app/security/jwt.py`, `backend/app/routes/auth.py` |
| 6 | RBAC | `backend/app/security/rbac.py` `Role` enum + `require_roles` |
| 7 | Input sanitisation | `backend/app/security/sanitize.py`, all Pydantic models in `backend/app/models/` |
| 8 | CSP / XSS protection | `backend/app/security/middleware.py` + `frontend/src/utils/sanitize.ts` (DOMPurify) |
| 9 | NoSQL injection protection | `backend/app/database.py` (Motor with parameterised queries) |
| 10 | DB schema validation | `backend/app/database.py` `COLLECTION_VALIDATORS` |
| 11 | Rate limiting | `backend/app/security/rate_limit.py` (SlowAPI + Redis) |
| 12 | Secure file uploads | `backend/app/routes/citizens.py` `upload_report_image` |
| 13 | CSRF protection | `backend/app/security/csrf.py`, applied via `frontend/src/api/client.ts` |
| 14 | Strict CORS | `backend/app/main.py` `CORSMiddleware` with `CORS_ALLOWED_ORIGINS` |
| 15 | HTTPS / HSTS | `backend/app/security/middleware.py` `Strict-Transport-Security` in prod |
| 16 | Security headers | `backend/app/security/middleware.py` `SecurityHeadersMiddleware` |
| 17 | Secure cookies | `backend/app/security/middleware.py` `set_auth_cookie` (HttpOnly, Secure, SameSite=Strict) |
| 18 | Disable debug mode | `backend/app/main.py` `__main__` block; `settings.DEBUG=False` in prod |
| 19 | Production settings | `backend/app/main.py` multi-worker via Gunicorn, `ENABLE_SWAGGER=False` in prod |

## Next steps

Tell me which feature module you want me to flesh out next. Suggested order:

1. The Mappls integration test (with real API key) end to end through `/api/v1/routes/route`.
2. The ML risk engine training pipeline (replace the deterministic fallback with a real scikit-learn model trained on MoRTH data).
3. The WebSocket telemetry handler so drivers see their preemption sequence update in real time.
4. The Firebase Cloud Messaging heading-filtered alert sender wired into the dispatch `create_trip` flow.
5. The Citizen Reporting image moderation pipeline (replace the simple sniff check with a real content scanner).
