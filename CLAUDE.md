# ProgramPigeon — CLAUDE.md

ProgramPigeon is a fitness coaching platform (TrueCoach-inspired) that allows coaches to deliver workout plans to clients and communicate with them via messaging.

---

## Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Backend          | FastAPI (Python)                    |
| Frontend         | React (TypeScript)                  |
| Database         | PostgreSQL                          |
| Auth             | JWT (JSON Web Tokens)               |
| ORM              | SQLAlchemy (async)                  |
| Migrations       | Alembic                             |
| Containerization | Docker + Docker Compose             |

---

## Repo Structure

```
ProgramPigeon/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/           # Route handlers (grouped by feature)
│   │   ├── core/          # Config, security, JWT utilities
│   │   ├── db/            # Database session, base models
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic layer
│   │   └── main.py        # App entrypoint
│   ├── alembic/           # Database migrations
│   ├── tests/             # Backend tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/              # React application
│   ├── src/
│   │   ├── api/           # API client functions
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page-level components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── context/       # React context (auth, etc.)
│   │   └── types/         # TypeScript type definitions
│   ├── public/
│   │   └── images/        # Static images (logos, etc.)
│   └── package.json
├── docker-compose.yml         # Orchestrates all services locally
├── docker-compose.prod.yml    # Production overrides
├── CLAUDE.md
└── README.md
```

---

## Core Features (Phase 1 Scope)

1. **Accounts**
   - Two roles: `coach` and `client`
   - Coaches can invite clients (by email)
   - Clients are linked to one or more coaches

2. **Workout Plans**
   - Coaches create and assign workout plans to clients
   - Plans contain ordered workouts; workouts contain exercises
   - Clients can view their assigned plans

3. **Messaging**
   - Direct messaging between a coach and their client
   - Messages are scoped to the coach–client relationship

---

## Auth

- JWT-based authentication (access token + refresh token)
- Tokens are stored in `httpOnly` cookies on the frontend (not localStorage) for security
- Role-based access control: endpoints check whether the caller is a `coach` or `client`
- Passwords hashed with `bcrypt`

---

## Coding Conventions

### General
- Every function and class must have a docstring explaining what it does, its parameters, and its return value
- Inline comments for any logic that isn't immediately obvious
- No magic numbers or hardcoded strings — use named constants or config values

### Backend (Python)
- Use type hints everywhere
- Follow PEP 8; format with `black`, lint with `ruff`
- Keep route handlers thin — business logic lives in `services/`
- Pydantic schemas define all API inputs and outputs; never return raw ORM objects
- Use async/await throughout (async SQLAlchemy sessions)

### Frontend (TypeScript/React)
- Functional components only — no class components
- Custom hooks for any data-fetching or shared stateful logic
- TypeScript strict mode enabled
- API calls go through `src/api/` — components do not call `fetch` directly

---

## Development Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in DB credentials and JWT secret
alembic upgrade head       # run migrations
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables (backend/.env)

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/programpigeon
SECRET_KEY=your-jwt-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Containerization

Each service runs in its own Docker container, orchestrated with Docker Compose.

### Services
- **backend** — FastAPI app served via `uvicorn`
- **frontend** — React app served via `nginx` (production) or Vite dev server (development)
- **db** — PostgreSQL instance with a named volume for persistence

### Structure
```
backend/
└── Dockerfile

frontend/
└── Dockerfile

docker-compose.yml       # Local development (hot reload enabled)
docker-compose.prod.yml  # Production (optimized builds, no dev tools)
```

### Local Development with Docker
```bash
docker-compose up --build
```
- Backend available at `http://localhost:8000`
- Frontend available at `http://localhost:3000`
- FastAPI docs at `http://localhost:8000/docs`

### Key Principles
- Never hardcode secrets in Dockerfiles — always pass via environment variables or a `.env` file
- The `db` service data is persisted in a named Docker volume (not a bind mount)
- Production image uses multi-stage builds to keep image sizes small

---

## Key Decisions & Rationale

- **FastAPI over Flask** — better suited for a React frontend (REST API), has built-in OpenAPI docs, native async support, and Pydantic validation baked in
- **PostgreSQL over SQLite** — required for production deployment; supports concurrent connections and proper relational constraints
- **JWT in httpOnly cookies** — more secure than localStorage (not accessible to JavaScript, mitigates XSS)
- **Monorepo** — keeps backend and frontend together for easier development; can be split into separate repos later if needed
- **Docker** — containerizing all three services (backend, frontend, db) makes deployment consistent across environments and simplifies onboarding

---

## Planning & Bug Tracking

All planning and bug tracking is done via **GitHub Issues** on the MitchGriff/ProgramPigeon repository.

- **Bugs** — logged as GitHub Issues with the `bug` label
- **Features / Tasks** — logged as GitHub Issues with the `feature` label
- **Planning** — organized via GitHub Milestones (e.g., "Phase 1 MVP")

When a bug is found or a new task is identified during a session, create a GitHub Issue immediately using the `gh` CLI. When a bug is fixed or a task is completed, close the corresponding issue and reference it in the PR.

---

## Design

### Color Palette
The UI uses a black, gray, and orange color scheme.

| Role       | Color         |
|------------|---------------|
| Primary    | Orange        |
| Background | Black         |
| Surface    | Gray          |
