# M0: Infrastructure Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get ProgramPigeon deployed to Railway with a live PostgreSQL database and a passing health check at `GET /health`.

**Architecture:** Backend and frontend are deployed as separate Railway services from their existing Dockerfiles. PostgreSQL runs as a Railway-managed database. Alembic migrations run automatically on backend startup (already implemented). The frontend nginx proxies `/api/` to the backend via Railway's private internal network.

**Tech Stack:** Railway (hosting), PostgreSQL 16 (managed DB), FastAPI + uvicorn (backend), React + nginx (frontend), pytest + httpx (backend testing), GitHub Actions (CI — wired up in M1).

**Related Issues:** #5, #6, #7, #8

---

## File Map

| Action | File | Purpose |
|--------|------|---------|
| Create | `backend/requirements-dev.txt` | Test dependencies (pytest, httpx) |
| Create | `backend/pytest.ini` | Pytest configuration |
| Create | `backend/tests/__init__.py` | Makes tests a package |
| Create | `backend/tests/conftest.py` | Shared test fixtures (mock migrations) |
| Create | `backend/tests/test_health.py` | Health check endpoint test |
| Rename | `frontend/nginx.conf` → `frontend/nginx.conf.template` | Templatize backend URL |
| Modify | `frontend/Dockerfile` | Use envsubst to inject backend URL at startup |
| Modify | `docker-compose.prod.yml` | Pass `BACKEND_INTERNAL_URL` for local prod testing |

---

## Task 1: Set Up Backend Test Infrastructure

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/pytest.ini`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create `backend/requirements-dev.txt`**

```text
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

- [ ] **Step 2: Create `backend/pytest.ini`**

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

- [ ] **Step 3: Create `backend/tests/__init__.py`**

Empty file — makes `tests/` a Python package so pytest can import from `app/`.

```python
```

- [ ] **Step 4: Create `backend/tests/conftest.py`**

This fixture runs automatically for every test and prevents Alembic from trying to connect to a real database.

```python
"""
Shared test fixtures for the ProgramPigeon backend test suite.
"""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_migrations():
    """
    Patch run_migrations for every test so Alembic never tries to reach a real database.
    Tests that need a database will override this with their own fixtures in a later milestone.
    """
    with patch("app.main.run_migrations"):
        yield
```

- [ ] **Step 5: Install dev dependencies**

Run inside the `backend/` directory (with your venv activated):

```bash
pip install -r requirements-dev.txt
```

- [ ] **Step 6: Commit**

```bash
git add backend/requirements-dev.txt backend/pytest.ini backend/tests/__init__.py backend/tests/conftest.py
git commit -m "chore: set up backend test infrastructure"
```

---

## Task 2: Write Health Check Test (Issue #6)

**Files:**
- Create: `backend/tests/test_health.py`

The `GET /health` endpoint already exists in `backend/app/main.py`. This task writes the test for it.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_health.py`:

```python
"""
Tests for the /health endpoint.
"""

from fastapi.testclient import TestClient
from app.main import app


def test_health_check_returns_200():
    """GET /health should return 200 with status ok."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_body():
    """GET /health should return {"status": "ok"}."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the tests to verify they pass**

Run from inside `backend/`:

```bash
pytest tests/test_health.py -v
```

Expected output:
```
tests/test_health.py::test_health_check_returns_200 PASSED
tests/test_health.py::test_health_check_response_body PASSED
2 passed in 0.XXs
```

If either test fails, check that `GET /health` exists in `app/main.py` and returns `{"status": "ok"}`.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_health.py
git commit -m "test: add health check endpoint tests (closes #6)"
```

---

## Task 3: Make nginx Backend URL Configurable for Railway

On Railway, the frontend nginx container can't reach the backend via `http://backend:8000` (that's a Docker Compose hostname). Railway uses an internal DNS like `http://<private-domain>:8000`. We need the backend URL to be injectable at container startup.

**Files:**
- Rename: `frontend/nginx.conf` → `frontend/nginx.conf.template`
- Modify: `frontend/Dockerfile`
- Modify: `docker-compose.prod.yml`

- [ ] **Step 1: Rename `frontend/nginx.conf` to `frontend/nginx.conf.template` and templatize the backend URL**

Delete the old file and create the template:

```bash
git rm frontend/nginx.conf
```

Create `frontend/nginx.conf.template` with this content:

```nginx
server {
    listen 80;

    root /usr/share/nginx/html;
    index index.html;

    # Route all requests to index.html so React Router handles client-side navigation
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to the backend — URL injected at container startup via envsubst
    location /api/ {
        proxy_pass ${BACKEND_INTERNAL_URL};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 2: Update `frontend/Dockerfile` to use envsubst**

Replace the contents of `frontend/Dockerfile` with:

```dockerfile
# --- Build stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


# --- Runtime stage: serve with nginx, injecting backend URL at startup ---
FROM nginx:alpine

# gettext provides envsubst, used to inject BACKEND_INTERNAL_URL into nginx config at startup
RUN apk add --no-cache gettext

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

EXPOSE 80

# At startup: substitute env vars into the nginx config template, then start nginx
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_INTERNAL_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
```

- [ ] **Step 3: Update `docker-compose.prod.yml` to pass `BACKEND_INTERNAL_URL`**

In Docker Compose, services communicate via their service name (`backend`), so the URL is `http://backend:8000`.

Replace the contents of `docker-compose.prod.yml` with:

```yaml
version: "3.9"

# Production overrides — use alongside docker-compose.yml:
#   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

services:

  backend:
    # Use the optimised multi-stage build; no bind mount or hot reload
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    volumes: []  # No bind mount in production
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - BACKEND_INTERNAL_URL=http://backend:8000
    ports:
      - "80:80"
    restart: unless-stopped

  db:
    restart: unless-stopped
```

- [ ] **Step 4: Commit**

```bash
git add frontend/nginx.conf.template frontend/Dockerfile docker-compose.prod.yml
git commit -m "chore: templatize nginx backend URL for Railway deployment"
```

---

## Task 4: Open PR, Get CI Green, and Merge

- [ ] **Step 1: Push the feature branch**

```bash
git push origin <your-branch-name>
```

- [ ] **Step 2: Open a PR targeting `master`**

```bash
gh pr create --title "M0 code changes: test infrastructure and nginx template" --body "$(cat <<'EOF'
## Summary
- **Story:** #5, #6, #7, #8 (M0: Infrastructure Setup)
- **Changes:** Added backend test infrastructure (pytest, conftest, dev requirements). Added health check tests. Templatized nginx config so backend URL is injectable at container startup for Railway deployment.
- **Design Decision:** nginx uses envsubst to inject BACKEND_INTERNAL_URL at container startup rather than build time — this allows the same Docker image to work in both Docker Compose (backend:8000) and Railway (private domain URL) without rebuilding.

## Testing
- **Tests performed:** pytest tests/test_health.py -v
- **Outcome:** 2 tests pass — health check returns 200 with {"status": "ok"}
EOF
)"
```

- [ ] **Step 3: Merge the PR after review**

Once merged, pull master locally:

```bash
git checkout master && git pull origin master
```

---

## Task 5: Create Railway Project and Configure Services (Issue #5)

These are manual steps in the Railway dashboard. No code changes.

- [ ] **Step 1: Create a Railway account**

Go to [railway.com](https://railway.com) and sign up with your GitHub account.

- [ ] **Step 2: Create a new project**

In the Railway dashboard: click **New Project** → **Deploy from GitHub repo** → select `MitchGriff/ProgramPigeon`.

Railway will create a default service. We'll configure it in the next steps.

- [ ] **Step 3: Add a PostgreSQL database**

In the project dashboard: click **+ New** → **Database** → **PostgreSQL**.

Railway will provision a managed PostgreSQL instance and automatically make `DATABASE_URL` available as an environment variable to services in the same project.

- [ ] **Step 4: Configure the backend service**

Click the default service Railway created → **Settings** → set:
- **Root Directory:** `backend`
- **Dockerfile Path:** `backend/Dockerfile`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`

Under **Networking** → click **Generate Domain** to give the backend a public URL.

- [ ] **Step 5: Add the frontend service**

In the project dashboard: click **+ New** → **GitHub Repo** → select `MitchGriff/ProgramPigeon` again.

Configure this second service:
- **Service Name:** `frontend`
- **Root Directory:** `frontend`
- **Dockerfile Path:** `frontend/Dockerfile`

Under **Networking** → click **Generate Domain** to give the frontend a public URL.

---

## Task 6: Set Environment Variables in Railway (Issue #7)

- [ ] **Step 1: Set backend environment variables**

In Railway dashboard → backend service → **Variables** tab. Add each variable:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Already injected automatically from the PostgreSQL service — verify it appears here |
| `SECRET_KEY` | Any long random string (e.g., run `python -c "import secrets; print(secrets.token_hex(32))"` locally to generate one) |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `ALLOWED_ORIGINS` | `["https://<your-frontend-railway-domain>"]` — use the Railway-generated frontend domain from Task 5 Step 5 |

- [ ] **Step 2: Set frontend environment variables**

In Railway dashboard → frontend service → **Variables** tab. Add:

| Variable | Value |
|----------|-------|
| `BACKEND_INTERNAL_URL` | `http://<backend-private-domain>:8000` — find the backend's private domain under backend service → **Settings** → **Private Networking**. It will look like `backend.railway.internal`. |

- [ ] **Step 3: Trigger a redeploy of both services**

After setting variables, Railway may redeploy automatically. If not, click **Deploy** on each service to force a fresh deploy with the new variables.

---

## Task 7: Verify Production Deploy (Issues #5, #8)

- [ ] **Step 1: Confirm backend is live**

Open the backend's Railway-generated public domain in your browser or run:

```bash
curl https://<backend-railway-domain>/health
```

Expected response:
```json
{"status": "ok"}
```

- [ ] **Step 2: Confirm migrations ran**

Check the backend deploy logs in Railway dashboard. You should see Alembic output near startup, e.g.:

```
INFO  [alembic.runtime.migration] Running upgrade -> <revision>, initial
```

If no migration files exist yet in `backend/alembic/versions/`, Alembic will log that there's nothing to run — this is fine for M0.

- [ ] **Step 3: Confirm frontend loads**

Open the frontend's Railway-generated domain in your browser. The login page should load.

- [ ] **Step 4: Confirm the API proxy works**

Open browser DevTools on the frontend domain and check that requests to `/api/v1/...` are not returning network errors (404 from nginx means the proxy is misconfigured — verify `BACKEND_INTERNAL_URL` is set correctly).

---

## Task 8: Close M0 GitHub Issues

- [ ] **Step 1: Close all M0 issues**

```bash
gh issue close 5 --comment "Railway project live. Backend and frontend deployed. Closes #5."
gh issue close 6 --comment "Health check tests passing. Closes #6."
gh issue close 7 --comment "All environment variables configured in Railway dashboard. Closes #7."
gh issue close 8 --comment "Alembic migrations run automatically on backend startup. Verified in Railway deploy logs. Closes #8."
```
