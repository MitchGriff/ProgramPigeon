"""
Main FastAPI application entrypoint.
Registers middleware, mounts all API routers, and exposes a health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config
from alembic import command

from app.core.config import settings
from app.api.v1 import auth, users, plans, messages


def run_migrations() -> None:
    """
    Run any pending Alembic migrations on startup.

    This ensures the database schema is always up to date when the app starts,
    so you never need to run 'alembic upgrade head' manually.
    """
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


app = FastAPI(
    title="ProgramPigeon",
    description="Fitness coaching platform API — coaches deliver workout plans and message clients.",
    version="0.1.0",
)

# Allow the React frontend (and any configured origins) to make cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,  # Required for httpOnly cookie auth
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all versioned API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["plans"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])


@app.on_event("startup")
async def startup_event() -> None:
    """
    Runs on application startup.
    Applies any pending database migrations so tables always exist before the app serves requests.
    """
    run_migrations()


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        A simple status dict used by Docker and load balancers to verify the app is running.
    """
    return {"status": "ok"}
