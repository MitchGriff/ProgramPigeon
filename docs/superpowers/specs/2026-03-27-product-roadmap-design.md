# ProgramPigeon — Product Roadmap & Planning Design

**Date:** 2026-03-27
**Status:** Approved

---

## Vision

ProgramPigeon is a fitness coaching platform built to be a full one-stop shop for the fitness coaching space. The core differentiator is combining personalized coach-client delivery with community/group workout tracking and client-owned metrics — in a single platform, at lower cost to coaches.

**Primary paying customer:** Coaches pay a subscription to use ProgramPigeon. Client billing and gym subscription management (via Stripe) come in a later phase.

**Platform:** Web app first. Mobile app (React Native) follows after the MVP is real-user tested.

**Philosophy:** Low fees, high usability. Coaches should choose ProgramPigeon because it does the job better, not because they're locked in.

---

## Long-Term Product Phases

Phases are sequential. A phase does not begin until the previous phase is real-user tested and automated tests are passing in CI/CD.

| Phase | Name | Description |
|-------|------|-------------|
| 1 | Coach-Client Core (MVP) | Workout delivery, client logging, and messaging between coaches and clients |
| 2 | Organizations | Coaches group under gyms/orgs; gym owner role manages coaching staff |
| 3 | Group/Community Workouts | Gyms post daily WODs; members comment and post scores |
| 4 | Metrics Tracking | Coaches and clients track performance metrics over time |
| 5 | Mobile App | React Native app with push notifications, workout completion, messaging |
| 6 | Payments | Stripe integration — coach subscriptions, client billing, gym memberships |

---

## Phase 1: Coach-Client Core (MVP)

Target: Real-user testing with friends/known coaches and clients by summer 2026.

### Coach-Client Relationship Model

- Clients own their accounts — they self-register independently
- Coaches send a coaching invite to a client (by email)
- Client accepts the invite to establish the relationship
- Either party can sever the relationship at any time — no permission needed from the other side
- Data is preserved for both parties after a relationship ends — coaches keep historical client data, clients keep historical workout/coach data

### Workout Structure

Workouts use a hybrid free-text + structured block model:

- A workout contains ordered **exercise blocks** labeled A, B, C...
- Each block has a **title** (e.g., "Bench Press") and a **free-text description** (e.g., "5x5, rest 3 min between sets")
- **Supersets** are supported: blocks labeled B1, B2 indicate exercises performed in alternating fashion
- Coaches write descriptions freely — no rigid form fields or dropdowns

### Client Workout Experience

At MVP, clients can:
- View their assigned workout plans and individual workouts
- Log actual weights, reps, and sets completed per exercise block
- Leave a comment on each individual exercise block
- Leave a comment on the workout as a whole
- Mark a workout as complete

### Phase 1 Milestones

| Milestone | Name | Definition of Done |
|-----------|------|--------------------|
| M0 | Infrastructure Setup | Railway project live, PostgreSQL connected, health check returns 200 in production |
| M1 | CI/CD + Observability | GitHub Actions pipeline (lint/test/build/deploy) green; Grafana Cloud showing FastAPI metrics and logs |
| M2 | Auth & Accounts | Self-serve registration, JWT auth, coach/client roles, coaching invite system, relationship management |
| M3 | Workout Builder | Coach creates plans → workouts → exercise blocks (single + supersets), assigns plans to clients |
| M4 | Client Workout Experience | Client views workouts, logs weights/reps, comments per exercise + whole workout, marks complete |
| M5 | Messaging | Per-workout threaded messages + general coach-client direct messaging |
| M6 | Dashboard & Polish | Coach sees client roster and activity; client sees upcoming/past workouts; app is end-to-end testable |

Each milestone is complete when: all Issues are closed, automated tests pass in CI, and the feature is manually verified end-to-end.

See [Infrastructure Design](2026-03-27-infrastructure-design.md) for full details on hosting, database, observability, and CI/CD decisions.

---

## Development Standards (Cross-Cutting)

These apply to every milestone across all phases.

### Automated Testing

- Tests are written alongside every feature — not added after the fact
- Testing is part of the definition of done for every issue
- Test types: unit tests for services/business logic, integration tests for API endpoints

### CI/CD — GitHub Actions

- Every PR to `master` runs: lint (`ruff`, ESLint), tests (pytest, vitest), and build
- PRs cannot merge if CI fails
- Concepts transfer from GitLab CI/CD: stages → jobs, `.gitlab-ci.yml` → `.github/workflows/`

### Branch Strategy

- One feature branch per issue: `feature/<issue-number>-<short-description>`
- PRs target `master`
- CI must pass before merge — no bypassing with `--no-verify`

### PR Format

```
## Summary
- **Story:** [GitHub Issue reference]
- **Changes:** [what was changed]
- **Design Decision:** [why it was done this way]

## Testing
- **Tests performed:** [what was tested]
- **Outcome:** [results / how to validate]
```

### GitHub Issue Labels

| Label | Purpose |
|-------|---------|
| `feature` | New functionality |
| `bug` | Defects found during development or testing |
| `chore` | Non-feature work (CI config, dependencies, refactoring) |
| `test` | Adding automated test coverage |

### GitHub Milestones

GitHub Milestones map 1:1 with M0–M6 (and future phases). Issues are attached to their milestone. A milestone closes when all its issues are closed and CI is green.

---

## Future Phases — High-Level Notes

### Phase 2: Organizations
- Coaches can operate solo or join an org/gym
- Gym owner role: manages which coaches are in their org
- Head coach/gym owner pays for the org's coach seats

### Phase 3: Group/Community Workouts
- Gym posts daily WODs visible to all gym members
- Members (not necessarily coached) can view, comment, and post scores

### Phase 4: Metrics Tracking
- Coaches track client performance metrics (body weight, PRs, benchmarks)
- Clients track their own metrics

### Phase 5: Mobile App
- React Native (web-first, then mobile)
- Features: view workouts, log metrics/goals, workout feedback, messaging, push notifications for messages and new workouts

### Phase 6: Payments (Stripe)
- Coach subscription billing
- Coach charges clients through ProgramPigeon (small platform cut)
- Gym subscription management (auto-pay for gym memberships)
- No sensitive financial data stored in-house — Stripe handles everything
