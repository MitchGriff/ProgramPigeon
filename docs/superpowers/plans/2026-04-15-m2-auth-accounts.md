# M2: Auth & Accounts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add token refresh, coach-adds-client-by-email endpoint, and a dedicated Clients page — all with tests.

**Architecture:** Feature-by-feature (end-to-end slices). Each feature is: write failing tests → implement → verify tests pass → commit. Backend first, then frontend. TDD throughout.

**Tech Stack:** FastAPI, SQLAlchemy async, python-jose, pytest, pytest-asyncio, React, TypeScript, Axios

---

## File Map

**New files:**
- `backend/app/services/users.py` — user-management service (add_client_by_email)
- `backend/tests/test_auth.py` — auth endpoint tests
- `backend/tests/test_users.py` — user endpoint tests
- `frontend/src/hooks/useClients.ts` — hook for client roster + add-by-email
- `frontend/src/pages/ClientsPage.tsx` — dedicated coach clients page
- `frontend/src/pages/ClientsPage.module.css` — styles for clients page

**Modified files:**
- `backend/tests/conftest.py` — add shared test fixtures
- `backend/app/services/auth.py` — add refresh_tokens()
- `backend/app/api/v1/auth.py` — add POST /auth/refresh route
- `backend/app/schemas/user.py` — add ClientByEmailRequest schema
- `backend/app/api/v1/users.py` — add POST /users/clients/by-email route
- `frontend/src/api/client.ts` — upgrade 401 interceptor to try refresh before redirect
- `frontend/src/api/users.ts` — add addClientByEmail()
- `frontend/src/App.tsx` — add /clients route
- `frontend/src/components/Navbar.tsx` — add Clients link (coaches only)
- `frontend/src/pages/DashboardPage.tsx` — update My Clients card to link to /clients

---

## Feature 1: Token Refresh

---

### Task 1: Update conftest.py with shared test fixtures

**Files:**
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Replace conftest.py**

```python
"""
Shared test fixtures for the ProgramPigeon backend test suite.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole


@pytest.fixture(autouse=True)
def mock_migrations():
    """
    Patch run_migrations for every test so Alembic never tries to reach a real database.
    """
    with patch("app.main.run_migrations"):
        yield


@pytest.fixture
def coach_user():
    """A mock coach User — use wherever a logged-in coach is needed."""
    from datetime import datetime
    user = User()
    user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user.email = "coach@test.com"
    user.name = "Test Coach"
    user.role = UserRole.coach
    user.created_at = datetime(2026, 1, 1, 0, 0, 0)
    user.clients = []
    return user


@pytest.fixture
def client_user():
    """A mock client User — use wherever a target client is needed."""
    from datetime import datetime
    user = User()
    user.id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    user.email = "client@test.com"
    user.name = "Test Client"
    user.role = UserRole.client
    user.created_at = datetime(2026, 1, 1, 0, 0, 0)
    user.clients = []
    return user


def make_mock_db(return_value=None):
    """
    Build a mock AsyncSession that returns `return_value` for any .execute() call.
    commit() and refresh() are no-ops by default.

    Args:
        return_value: What scalar_one_or_none() returns. Pass None to simulate not found.
    """
    session = AsyncMock()
    result = AsyncMock()
    result.scalar_one_or_none.return_value = return_value
    session.execute.return_value = result
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session
```

- [ ] **Step 2: Verify the file imports cleanly**

```bash
cd backend && python -c "import tests.conftest; print('OK')"
```

Expected: `OK`

---

### Task 2: Write failing tests for POST /auth/refresh

**Files:**
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Create the test file**

```python
"""
Tests for POST /api/v1/auth/refresh.

Strategy: token decode and type-checking happens in the service before any DB call.
Tests that exercise invalid tokens let the real service run (no DB needed).
The success case mocks the DB to return the coach user.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_refresh_token, create_access_token
from tests.conftest import make_mock_db


def _make_expired_refresh_token(user_id: str) -> str:
    """Create a refresh token that is already expired."""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() - timedelta(seconds=1),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def http():
    """Plain TestClient with no dependency overrides."""
    return TestClient(app)


@pytest.fixture
def http_with_coach_db(coach_user):
    """
    TestClient with get_db overridden to return the coach when queried.
    Used for the success case where the service needs to look up the user.
    """
    mock_db = make_mock_db(return_value=coach_user)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Failure cases (no DB needed — token validation fails before DB is hit) ---

def test_refresh_missing_cookie_returns_401(http):
    """No refresh_token cookie → 401."""
    response = http.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_refresh_invalid_token_returns_401(http):
    """Garbage string in the cookie → 401."""
    response = http.post("/api/v1/auth/refresh", cookies={"refresh_token": "not.a.jwt"})
    assert response.status_code == 401


def test_refresh_expired_token_returns_401(http, coach_user):
    """Expired refresh token → 401."""
    token = _make_expired_refresh_token(str(coach_user.id))
    response = http.post("/api/v1/auth/refresh", cookies={"refresh_token": token})
    assert response.status_code == 401


def test_refresh_wrong_type_returns_401(http, coach_user):
    """Access token used in place of refresh token → 401."""
    access_token = create_access_token(str(coach_user.id), "coach")
    response = http.post("/api/v1/auth/refresh", cookies={"refresh_token": access_token})
    assert response.status_code == 401


# --- Success case (DB mock needed to return the user) ---

def test_refresh_valid_token_returns_200_and_sets_cookies(http_with_coach_db, coach_user):
    """Valid refresh token → 200 and both auth cookies refreshed."""
    token = create_refresh_token(str(coach_user.id))
    response = http_with_coach_db.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": token},
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_response_body_contains_user(http_with_coach_db, coach_user):
    """Valid refresh token → response body is the user object."""
    token = create_refresh_token(str(coach_user.id))
    response = http_with_coach_db.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": token},
    )
    body = response.json()
    assert body["email"] == coach_user.email
    assert body["role"] == "coach"
    assert "password" not in body
    assert "password_hash" not in body
```

- [ ] **Step 2: Run the tests — verify they all fail**

```bash
cd backend && python -m pytest tests/test_auth.py -v
```

Expected output: All tests FAIL — `ModuleNotFoundError` or `404 Not Found` (the endpoint doesn't exist yet).

---

### Task 3: Implement refresh_tokens() in services/auth.py

**Files:**
- Modify: `backend/app/services/auth.py`

- [ ] **Step 1: Add refresh_tokens() to the bottom of the file**

```python
async def refresh_tokens(db: AsyncSession, refresh_token: str) -> User:
    """
    Validate a refresh token and return the associated user.

    Args:
        db: Async database session.
        refresh_token: The JWT refresh token string from the cookie.

    Returns:
        The User associated with the token.

    Raises:
        HTTPException 401: If the token is missing, invalid, expired, or the wrong type.
    """
    from fastapi import HTTPException, status
    from jose import JWTError
    from sqlalchemy import select
    from app.core.security import decode_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception

    return user
```

Note: imports are intentionally inline here to avoid circular imports since `services/auth.py` already imports from `core/security`. Move them to the top of the file alongside the existing imports if they aren't already there:

The full import block at the top of `services/auth.py` should be:

```python
from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, decode_token
from app.models.user import User
from app.schemas.user import UserCreate
```

---

### Task 4: Add POST /auth/refresh route and verify tests pass

**Files:**
- Modify: `backend/app/api/v1/auth.py`

- [ ] **Step 1: Add the refresh endpoint to auth.py**

Add this import at the top (alongside existing imports):

```python
from app.services.auth import authenticate_user, register_user, refresh_tokens
```

Add this route after the `logout` handler:

```python
@router.post("/refresh", response_model=UserResponse)
async def refresh(
    response: Response,
    refresh_token: str = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Issue a new access token and refresh token using the existing refresh token cookie.

    Both tokens are rotated on each call. Returns the current user's profile.
    Returns 401 if the refresh token is missing, invalid, expired, or the wrong type.
    """
    if not refresh_token:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    user = await refresh_tokens(db, refresh_token)
    new_access_token = create_access_token(subject=str(user.id), role=user.role.value)
    new_refresh_token = create_refresh_token(subject=str(user.id))
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return user
```

Clean up the inline import by adding this to the top-level imports in the file:

```python
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
```

(Just add `Cookie` and `HTTPException` to the existing `from fastapi import ...` line.)

- [ ] **Step 2: Run the tests — verify they all pass**

```bash
cd backend && python -m pytest tests/test_auth.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 3: Run the full test suite to check nothing is broken**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass (health check + auth tests).

- [ ] **Step 4: Commit**

```bash
cd backend && git add app/services/auth.py app/api/v1/auth.py tests/conftest.py tests/test_auth.py
git commit -m "feat: add POST /auth/refresh endpoint with token rotation"
```

---

### Task 5: Upgrade frontend 401 interceptor

**Files:**
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Replace the interceptor in client.ts**

```typescript
/**
 * Axios instance used for all API calls.
 *
 * - baseURL points to /api so the Vite proxy (dev) and nginx (prod) both route correctly
 * - withCredentials: true is required so httpOnly auth cookies are sent with every request
 * - On 401 responses, silently attempts a token refresh before redirecting to /login
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Send cookies with every request (required for httpOnly JWT cookies)
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attempt a silent token refresh on 401, then retry the original request.
// If the refresh also fails, redirect to /login.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const is401 = error.response?.status === 401
    const isRefreshEndpoint = originalRequest?.url === '/auth/refresh'

    // Only attempt refresh once, and never for the refresh endpoint itself
    if (is401 && !isRefreshEndpoint && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        await apiClient.post('/auth/refresh')
        // Cookies updated — retry the original request
        return apiClient(originalRequest)
      } catch {
        // Refresh failed — fall through to redirect
      }
    }

    // Redirect to login for unrecoverable 401s
    if (is401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

export default apiClient
```

- [ ] **Step 2: Start the app locally and verify login still works**

```bash
# Terminal 1
docker-compose up

# Terminal 2
cd frontend && npm run dev
```

Open `http://localhost:3000/login`. Log in with a test account. Verify you land on the dashboard without errors in the browser console.

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/api/client.ts
git commit -m "feat: upgrade 401 interceptor to attempt silent token refresh"
```

---

## Feature 2: Add Client by Email

---

### Task 6: Write failing tests for POST /users/clients/by-email

**Files:**
- Create: `backend/tests/test_users.py`

- [ ] **Step 1: Create the test file**

```python
"""
Tests for POST /api/v1/users/clients/by-email.

Strategy: override get_current_user to simulate a coach, override get_db to
return the mock client user. Each test sets up overrides independently.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from tests.conftest import make_mock_db


@pytest.fixture
def http_as_coach(coach_user, client_user):
    """
    TestClient acting as coach_user, with DB returning client_user on lookup.
    """
    mock_db = make_mock_db(return_value=client_user)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_empty_db(coach_user):
    """
    TestClient acting as coach_user, with DB returning None (no user found).
    """
    mock_db = make_mock_db(return_value=None)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_db_returns_another_coach(coach_user):
    """
    TestClient acting as coach_user, with DB returning a user who is also a coach.
    Used to verify that adding a coach-role user is rejected.
    """
    from app.models.user import User, UserRole
    import uuid

    another_coach = User()
    another_coach.id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    another_coach.email = "another@coach.com"
    another_coach.name = "Another Coach"
    another_coach.role = UserRole.coach
    another_coach.clients = []

    mock_db = make_mock_db(return_value=another_coach)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_coach_client_already_added(coach_user, client_user):
    """
    TestClient acting as coach_user who already has client_user on their roster.
    """
    coach_user.clients = [client_user]
    mock_db = make_mock_db(return_value=client_user)

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: coach_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def http_as_client(client_user):
    """
    TestClient acting as a client (not a coach). Used to verify 403 enforcement.
    """
    mock_db = make_mock_db()

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: client_user
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Tests ---

def test_add_client_by_email_success(http_as_coach, client_user):
    """Coach adds a client by valid email → 201 and client data returned."""
    response = http_as_coach.post(
        "/api/v1/users/clients/by-email",
        json={"email": client_user.email},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == client_user.email
    assert body["role"] == "client"
    assert "password_hash" not in body


def test_add_client_email_not_found_returns_404(http_as_coach_empty_db):
    """Email doesn't match any account → 404."""
    response = http_as_coach_empty_db.post(
        "/api/v1/users/clients/by-email",
        json={"email": "ghost@nowhere.com"},
    )
    assert response.status_code == 404


def test_add_client_coach_email_returns_404(http_as_coach_db_returns_another_coach):
    """Email belongs to a coach, not a client → 404 (no role leakage)."""
    response = http_as_coach_db_returns_another_coach.post(
        "/api/v1/users/clients/by-email",
        json={"email": "another@coach.com"},
    )
    assert response.status_code == 404


def test_add_client_already_linked_returns_400(http_as_coach_client_already_added, client_user):
    """Client already on roster → 400."""
    response = http_as_coach_client_already_added.post(
        "/api/v1/users/clients/by-email",
        json={"email": client_user.email},
    )
    assert response.status_code == 400


def test_add_client_by_client_returns_403(http_as_client, client_user):
    """Only coaches can add clients → 403 for client callers."""
    response = http_as_client.post(
        "/api/v1/users/clients/by-email",
        json={"email": client_user.email},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run the tests — verify they all fail**

```bash
cd backend && python -m pytest tests/test_users.py -v
```

Expected: All tests FAIL — `404 Not Found` (the endpoint doesn't exist yet).

---

### Task 7: Add ClientByEmailRequest schema to schemas/user.py

**Files:**
- Modify: `backend/app/schemas/user.py`

- [ ] **Step 1: Add the new schema at the bottom of the file**

```python
class ClientByEmailRequest(BaseModel):
    """Request body for POST /users/clients/by-email."""
    email: EmailStr
```

---

### Task 8: Create services/users.py with add_client_by_email()

**Files:**
- Create: `backend/app/services/users.py`

- [ ] **Step 1: Create the file**

```python
"""
User management service: business logic for coach-client relationship operations.

Route handlers in api/v1/users.py call these functions — keeping business logic
out of the route layer makes it easier to test and reuse.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def add_client_by_email(db: AsyncSession, coach: User, email: str) -> User:
    """
    Link a client account to a coach by the client's email address.

    Args:
        db: Async database session.
        coach: The authenticated coach performing the action.
        email: Email address of the client account to link.

    Returns:
        The linked client User.

    Raises:
        HTTPException 404: If no client account exists with that email.
            The same error is returned when the email belongs to a coach, to
            avoid leaking role information.
        HTTPException 400: If the client is already on this coach's roster.
    """
    result = await db.execute(select(User).where(User.email == email))
    client = result.scalar_one_or_none()

    # Same error for "not found" and "wrong role" — avoids leaking role info
    if not client or client.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if client in coach.clients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client already added",
        )

    coach.clients.append(client)
    await db.commit()
    await db.refresh(client)
    return client
```

---

### Task 9: Add POST /users/clients/by-email route and verify tests pass

**Files:**
- Modify: `backend/app/api/v1/users.py`

- [ ] **Step 1: Add the import and new route to users.py**

Replace the existing `from app.schemas.user import UserResponse` line with:

```python
from app.schemas.user import UserResponse, ClientByEmailRequest
```

Add a new import line below the existing imports:

```python
from app.services.users import add_client_by_email as add_client_by_email_service
```

Add this route before the existing `add_client` route:

```python
@router.post("/clients/by-email", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_client_by_email(
    data: ClientByEmailRequest,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Link a client to this coach's roster by email address.

    Args:
        data: Request body containing the client's email address.

    Raises:
        HTTPException 404: If no client account exists with that email.
        HTTPException 400: If the client is already on this coach's roster.
        HTTPException 403: If the caller is not a coach.
    """
    return await add_client_by_email_service(db, coach, data.email)
```

- [ ] **Step 2: Run the users tests — verify they all pass**

```bash
cd backend && python -m pytest tests/test_users.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Run the full test suite**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
cd backend && git add app/schemas/user.py app/services/users.py app/api/v1/users.py tests/test_users.py
git commit -m "feat: add POST /users/clients/by-email endpoint"
```

---

### Task 10: Add addClientByEmail() to frontend API layer

**Files:**
- Modify: `frontend/src/api/users.ts`

- [ ] **Step 1: Add the new function to users.ts**

```typescript
/**
 * User management API functions: coach-client relationship management.
 */

import apiClient from './client'
import type { User } from '@/types/user'

/**
 * Fetch all clients linked to the authenticated coach.
 */
export async function getClients(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/users/clients')
  return data
}

/**
 * Add a client to the authenticated coach's roster by user ID.
 */
export async function addClient(clientId: string): Promise<User> {
  const { data } = await apiClient.post<User>(`/users/clients/${clientId}`)
  return data
}

/**
 * Remove a client from the authenticated coach's roster.
 */
export async function removeClient(clientId: string): Promise<void> {
  await apiClient.delete(`/users/clients/${clientId}`)
}

/**
 * Add a client to the authenticated coach's roster by email address.
 * Throws if the email is not found or belongs to a non-client account.
 */
export async function addClientByEmail(email: string): Promise<User> {
  const { data } = await apiClient.post<User>('/users/clients/by-email', { email })
  return data
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend && git add src/api/users.ts
git commit -m "feat: add addClientByEmail API function"
```

---

## Feature 3: Clients Page

---

### Task 11: Create useClients hook

**Files:**
- Create: `frontend/src/hooks/useClients.ts`

- [ ] **Step 1: Create the hook**

```typescript
/**
 * useClients: manages the coach's client roster.
 *
 * Fetches clients on mount and exposes an addClient function that
 * calls the by-email endpoint and appends the result to local state
 * without requiring a refetch.
 */

import { useState, useEffect } from 'react'
import { getClients, addClientByEmail } from '@/api/users'
import type { User } from '@/types/user'

interface UseClientsResult {
  /** The coach's current client roster. */
  clients: User[]
  /** True while the initial fetch is in progress. */
  loading: boolean
  /** Error message if the initial fetch failed, otherwise null. */
  error: string | null
  /**
   * Add a client by email. Appends to the roster on success.
   * Throws on failure so the caller can display the error.
   */
  addClient: (email: string) => Promise<void>
}

export function useClients(): UseClientsResult {
  const [clients, setClients] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getClients()
      .then(setClients)
      .catch(() => setError('Failed to load clients.'))
      .finally(() => setLoading(false))
  }, [])

  async function addClient(email: string): Promise<void> {
    const newClient = await addClientByEmail(email)
    setClients((prev) => [...prev, newClient])
  }

  return { clients, loading, error, addClient }
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend && git add src/hooks/useClients.ts
git commit -m "feat: add useClients hook"
```

---

### Task 12: Create ClientsPage

**Files:**
- Create: `frontend/src/pages/ClientsPage.tsx`
- Create: `frontend/src/pages/ClientsPage.module.css`

- [ ] **Step 1: Create ClientsPage.tsx**

```tsx
/**
 * ClientsPage: coach-only page for managing the client roster.
 *
 * Shows the full client list and an add-by-email form.
 * Redirects non-coach users to /dashboard.
 */

import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useClients } from '@/hooks/useClients'
import styles from './ClientsPage.module.css'

export default function ClientsPage() {
  const { user } = useAuth()
  const { clients, loading, error, addClient } = useClients()

  const [email, setEmail] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Redirect non-coaches — they have no business here
  if (user?.role !== 'coach') return <Navigate to="/dashboard" replace />

  async function handleAddClient(e: FormEvent) {
    e.preventDefault()
    setAddError(null)
    setSuccessMessage(null)
    setAdding(true)
    try {
      await addClient(email)
      setSuccessMessage(`${email} added to your roster.`)
      setEmail('')
    } catch (err: unknown) {
      const detail =
        err instanceof Error ? err.message : 'No client account found with that email.'
      setAddError(detail)
    } finally {
      setAdding(false)
    }
  }

  if (loading) return <div className={styles.loading}>Loading clients...</div>
  if (error) return <div className={styles.error}>{error}</div>

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>My Clients</h1>

      {/* Add client form */}
      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Add a client</h2>
        <p className={styles.cardDescription}>
          Enter the email address of an existing client account.
        </p>
        <form onSubmit={handleAddClient} className={styles.form}>
          <input
            type="email"
            className={styles.input}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="client@example.com"
            required
            autoComplete="off"
          />
          <button type="submit" className={styles.button} disabled={adding}>
            {adding ? 'Adding...' : 'Add client'}
          </button>
        </form>
        {addError && <p className={styles.addError}>{addError}</p>}
        {successMessage && <p className={styles.success}>{successMessage}</p>}
      </section>

      {/* Client roster */}
      <section className={styles.card}>
        <h2 className={styles.cardTitle}>
          Client roster
          <span className={styles.count}>{clients.length}</span>
        </h2>
        {clients.length === 0 ? (
          <p className={styles.empty}>No clients yet. Add your first client above.</p>
        ) : (
          <ul className={styles.list}>
            {clients.map((client) => (
              <li key={client.id} className={styles.listItem}>
                <Link to={`/messages/${client.id}`} className={styles.clientLink}>
                  <span className={styles.clientName}>{client.name}</span>
                  <span className={styles.clientEmail}>{client.email}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
```

- [ ] **Step 2: Create ClientsPage.module.css**

```css
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.heading {
  font-size: 1.75rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 1.5rem;
}

.card {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.cardTitle {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.count {
  background: #f97316;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 0 0.5rem;
  line-height: 1.5rem;
}

.cardDescription {
  color: #9ca3af;
  font-size: 0.875rem;
  margin: 0 0 1rem 0;
}

.form {
  display: flex;
  gap: 0.75rem;
}

.input {
  flex: 1;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  outline: none;
}

.input:focus {
  border-color: #f97316;
}

.button {
  background: #f97316;
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.5rem 1.25rem;
  white-space: nowrap;
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.addError {
  color: #f87171;
  font-size: 0.875rem;
  margin: 0.75rem 0 0;
}

.success {
  color: #4ade80;
  font-size: 0.875rem;
  margin: 0.75rem 0 0;
}

.empty {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.listItem {
  border-radius: 6px;
  overflow: hidden;
}

.clientLink {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  text-decoration: none;
  transition: border-color 0.15s;
}

.clientLink:hover {
  border-color: #f97316;
}

.clientName {
  color: #fff;
  font-weight: 500;
  font-size: 0.9rem;
}

.clientEmail {
  color: #9ca3af;
  font-size: 0.8rem;
}

.loading {
  color: #9ca3af;
  padding: 2rem;
  text-align: center;
}

.error {
  color: #f87171;
  padding: 2rem;
  text-align: center;
}
```

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/pages/ClientsPage.tsx src/pages/ClientsPage.module.css
git commit -m "feat: add ClientsPage with roster and add-by-email form"
```

---

### Task 13: Wire routing, navbar, and dashboard

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Navbar.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Add the /clients route to App.tsx**

Add the import at the top with the other page imports:

```typescript
import ClientsPage from '@/pages/ClientsPage'
```

Add the route after the `/messages/:userId` route (before the redirect catches):

```tsx
<Route
  path="/clients"
  element={
    <ProtectedRoute>
      <AuthenticatedLayout>
        <ClientsPage />
      </AuthenticatedLayout>
    </ProtectedRoute>
  }
/>
```

- [ ] **Step 2: Add Clients link to Navbar.tsx**

In the `<div className={styles.links}>` block, add a Clients link that only renders for coaches, between the Plans and Messages links:

```tsx
{user?.role === 'coach' && (
  <NavLink
    to="/clients"
    className={({ isActive }) => (isActive ? styles.linkActive : styles.link)}
  >
    Clients
  </NavLink>
)}
```

- [ ] **Step 3: Update DashboardPage.tsx — My Clients card**

In the coaches-only `<section className={styles.card}>` block (the "My Clients" section), replace the full section content with a simple link to `/clients`:

```tsx
{isCoach && (
  <section className={styles.card}>
    <div className={styles.cardHeader}>
      <h2>My Clients</h2>
      <Link to="/clients" className={styles.linkButton}>
        Manage clients →
      </Link>
    </div>
    {clients.length === 0 ? (
      <p className={styles.empty}>No clients yet.</p>
    ) : (
      <ul className={styles.list}>
        {clients.map((client) => (
          <li key={client.id}>
            <Link to={`/messages/${client.id}`} className={styles.listItem}>
              <span className={styles.planTitle}>{client.name}</span>
              <span className={styles.planMeta}>{client.email}</span>
            </Link>
          </li>
        ))}
      </ul>
    )}
  </section>
)}
```

- [ ] **Step 4: Verify the app in browser**

With `docker-compose up` and `npm run dev` running:
1. Log in as a coach → confirm "Clients" appears in the navbar
2. Click "Clients" → confirm the `/clients` page loads with the add form
3. Log in as a client → confirm "Clients" does NOT appear in the navbar
4. Manually navigate to `/clients` as a client → confirm redirect to `/dashboard`

- [ ] **Step 5: Commit**

```bash
cd frontend && git add src/App.tsx src/components/Navbar.tsx src/pages/DashboardPage.tsx
git commit -m "feat: wire /clients route, navbar link, and dashboard card"
```

---

## Final check

- [ ] Run the full backend test suite one more time:

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass.

- [ ] Open a PR against master targeting the feature branch with M2 changes.
