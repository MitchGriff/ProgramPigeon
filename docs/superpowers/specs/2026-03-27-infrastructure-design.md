# ProgramPigeon — Infrastructure Design

**Date:** 2026-03-27
**Status:** Approved

---

## Overview

This document covers hosting, database, observability, and CI/CD decisions for ProgramPigeon. The guiding principle is to keep infrastructure simple and low-cost while the product is in development, with a clear migration path as the project grows.

---

## Hosting — Railway

**Platform:** [Railway](https://railway.com)

**Why Railway:**
- Deploys Docker Compose services directly — maps cleanly onto the existing `docker-compose.yml`
- Managed PostgreSQL add-on with automatic `DATABASE_URL` injection
- Simple dashboard with real-time logs, deploy history, and environment variable management
- GitHub integration — push to `master`, Railway deploys automatically
- Low cost for a side project with no users yet

**Trade-offs:**
- No SSH access into running containers
- Less configurable than AWS or Fly.io
- Acceptable at this stage — observability gaps are covered by Grafana Cloud

**Migration path:**
When ProgramPigeon grows (more users, more revenue, need for more control), the app is already fully containerized. Migration to Fly.io or AWS ECS is a matter of pointing at new infrastructure — no application code changes required.

### Services on Railway

| Service | Description |
|---------|-------------|
| backend | FastAPI app served via uvicorn |
| frontend | React app served via nginx |
| db | Managed PostgreSQL (Railway add-on) |

---

## Database — Managed PostgreSQL (Railway)

**Why managed PostgreSQL on Railway:**
- Zero configuration — Railway injects `DATABASE_URL` automatically
- No connection pooling, backup, or replication config required at this stage
- Same PostgreSQL version as local development (no environment parity issues)

**Schema migrations — Alembic:**
- All schema changes are versioned migration files in `backend/alembic/versions/`
- Deploying to a new database is: point at new `DATABASE_URL`, run `alembic upgrade head`
- Data migrations (moving rows between databases) use `pg_dump` / `pg_restore`

**Migration path:**
Switching databases between platforms is low-risk — connection string change + `alembic upgrade head`. Data portability is handled by standard PostgreSQL tooling.

---

## Observability — Grafana Cloud

**Platform:** [Grafana Cloud](https://grafana.com/products/cloud/) (free tier)

**Stack:**

| Tool | Role |
|------|------|
| Prometheus | Scrapes `/metrics` from the FastAPI app; stores time-series data |
| Loki | Log aggregation — ingests app logs (stdout/stderr) |
| Promtail | Ships logs from the app to Loki |
| Grafana | Unified dashboard for metrics, logs, and alerts |

**What we monitor:**
- Request latency (p50, p95, p99)
- Error rates and failed requests
- Traffic patterns and usage spikes
- How the app handles load over time

**How it works:**
```
FastAPI app → exposes /metrics endpoint → Prometheus scrapes → Grafana dashboards
FastAPI app → stdout/stderr logs → Promtail ships → Loki stores → Grafana log view
```

**FastAPI instrumentation:**
`prometheus-fastapi-instrumentator` — single import, auto-instruments all endpoints with request count, latency histograms, and error rates.

**Why Grafana Cloud over Elastic Stack:**
- Elastic Stack excels at log search — Grafana Cloud excels at time-series metrics + log correlation
- The monitoring goals (latency, error rates, traffic spikes) are a metrics problem, not a log search problem
- Grafana Cloud free tier covers everything needed at this stage
- No infrastructure to self-host

---

## CI/CD — GitHub Actions

**Why GitHub Actions:**
- Native to the GitHub repository
- Generous free tier
- Concepts transfer directly from GitLab CI/CD (stages → jobs, `.gitlab-ci.yml` → `.github/workflows/`)

**Pipeline (every PR to `master`):**
1. Lint — `ruff` (backend), ESLint (frontend)
2. Test — `pytest` (backend), `vitest` (frontend)
3. Build — Docker images for backend and frontend
4. Deploy — push to Railway (on merge to `master` only)

---

## Infrastructure Milestones

These milestones precede the feature milestones (M1–M5):

| Milestone | Name | Definition of Done |
|-----------|------|--------------------|
| M0 | Infrastructure Setup | Railway project created, services deployed, PostgreSQL connected, environment variables configured, basic health check endpoint returns 200 in production |
| M1 | CI/CD + Observability | GitHub Actions pipeline running lint/test/build/deploy on every PR; Grafana Cloud connected with basic FastAPI metrics and logs visible |

---

## Environment Variables

All secrets and environment-specific config are passed via environment variables — never hardcoded in Dockerfiles or committed to the repo.

| Variable | Where set |
|----------|-----------|
| `DATABASE_URL` | Railway dashboard (auto-injected for managed PostgreSQL) |
| `SECRET_KEY` | Railway dashboard |
| `ALGORITHM` | Railway dashboard |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Railway dashboard |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Railway dashboard |
| `GRAFANA_CLOUD_*` | Railway dashboard (API keys for metrics/log shipping) |
