# M2: Auth & Accounts — Design Spec

**Date:** 2026-04-15
**Milestone:** M2: Auth & Accounts
**Approach:** Feature by feature (end-to-end slices)

---

## Scope

Three features, built in order:

1. **Token Refresh** — `POST /auth/refresh` endpoint + frontend silent refresh interceptor
2. **Add Client by Email** — `POST /users/clients/by-email` endpoint
3. **Clients Page** — Dedicated `/clients` frontend page for coaches

Each feature ships with backend, frontend (where applicable), and tests before the next begins.

---

## Current State

The skeleton already has:
- `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
- JWT in httpOnly cookies (access + refresh tokens created, but no refresh endpoint)
- `require_coach` / `require_client` dependency guards
- `POST /users/clients/{client_id}` (link by UUID — stays, but not used by UI)
- `GET /users/clients`, `DELETE /users/clients/{client_id}`
- Login, Register pages, AuthContext, ProtectedRoute, Dashboard shell

---

## Feature 1: Token Refresh

### Backend

**New endpoint:** `POST /auth/refresh`

- Reads `refresh_token` from httpOnly cookie
- Decodes and verifies `type == "refresh"`
- Fetches user from DB to get current role (role may have changed since token was issued)
- Issues a new access token and a new refresh token (token rotation — refresh token is single-use)
- Writes both as new httpOnly cookies on the response
- Returns 401 if cookie is missing, token is invalid/expired, or token type is wrong

**Service layer:** Logic lives in `services/auth.py` as `refresh_tokens(db, refresh_token_str) -> User`.

**Token rotation rationale:** Rotating the refresh token on every use means a stolen token can only be used once before it's invalidated by the next legitimate refresh. Industry standard for httpOnly cookie auth.

**MVP caveat:** True single-use rotation requires a token blacklist (e.g. storing invalidated JTIs in the DB or Redis) so the old refresh token is actually revoked. With stateless JWTs we can't do this without a store. For MVP we issue a new refresh token on each refresh but the old one remains technically valid until it expires naturally. Acceptable for now; a token blacklist can be added later if security requirements demand it.

### Frontend

**File:** `src/api/client.ts`

Add a 401 interceptor to the base fetch wrapper:
1. On 401 response: call `POST /auth/refresh`
2. If refresh succeeds: retry the original request (new cookies are set automatically)
3. If refresh fails: clear auth state in `AuthContext`, redirect to `/login`

This is transparent to all page components — they never handle token expiry themselves.

### Tests

`backend/tests/test_auth.py`:

| Case | Expected |
|------|----------|
| Valid refresh token in cookie | 200, new access + refresh cookies set |
| No refresh token cookie | 401 |
| Tampered / invalid token | 401 |
| Expired refresh token | 401 |
| Access token used instead of refresh token (wrong `type`) | 401 |

---

## Feature 2: Add Client by Email

### Backend

**New endpoint:** `POST /users/clients/by-email`

Request body:
```json
{ "email": "client@example.com" }
```

Logic:
1. Requires `require_coach` dependency (403 if caller is not a coach)
2. Look up user by email
3. If not found, or found user is not a `client` → 404 ("Client not found") — same error for both to avoid leaking role information
4. If client is already linked to this coach → 400 ("Client already added")
5. Create `coach_client` link, return `UserResponse`

**New schema:** `ClientByEmailRequest` in `schemas/user.py` — just `{ email: EmailStr }`.

**Service layer:** New `services/users.py` with `add_client_by_email(db, coach, email) -> User`. Separates user-management logic from auth logic.

The existing `POST /users/clients/{client_id}` (link by UUID) stays — it's not removed.

### Tests

`backend/tests/test_users.py`:

| Case | Expected |
|------|----------|
| Valid email, client exists, not yet linked | 201, UserResponse |
| Email not found | 404 |
| Email belongs to a coach | 404 (same error — no role leakage) |
| Client already on this coach's roster | 400 |
| Caller is a client (not a coach) | 403 |

---

## Feature 3: Clients Page

### Frontend

**New page:** `src/pages/ClientsPage.tsx` at route `/clients`

- Coach-only route: non-coaches are redirected to `/dashboard`
- Two sections:
  - **Roster:** List of linked clients (name + email), each linking to `/messages/{client.id}`
  - **Add client:** Email input + "Add" button; on success appends client to roster inline; on error shows inline message (e.g. "No client account found with that email")

**New hook:** `src/hooks/useClients.ts`
- Fetches client roster on mount via `GET /users/clients`
- Exposes `addClient(email: string)` that calls `POST /users/clients/by-email`
- On success, appends the returned client to local state (no refetch needed)
- Handles loading and error state

**New API function:** `addClientByEmail(email: string)` in `src/api/users.ts`

**Navbar:** "Clients" link added, visible only when `user.role === 'coach'`

**Dashboard:** "My Clients" card updated to link to `/clients` instead of listing inline (keeps the dashboard clean now that there's a dedicated page).

---

## Out of Scope for M2

- Email-based invite flow (Option C) — additive, deferred
- Password reset / forgot password
- Profile editing
- Admin roles

---

## Implementation Order

1. Feature 1: Token refresh (backend → tests → frontend interceptor)
2. Feature 2: Add client by email (backend → tests)
3. Feature 3: Clients page (frontend → hook → navbar → dashboard update)
