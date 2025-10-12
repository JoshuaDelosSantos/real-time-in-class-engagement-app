# Data Model Overview

This document defines the relational schema we intend to introduce. Treat it as the source of truth during review—once approved, the corresponding migrations, repositories, and services should mirror the structure described here.

## Entity Summary

- **users** — Represents anyone interacting with the app. Any user can create or join sessions.
- **sessions** — A live classroom room keyed by a shareable join code.
- **session_participants** — Tracks which users have joined which sessions (including hosts).
- **questions** — Items submitted by participants that can gather likes and be marked as answered.
- **question_votes** — Records which users have liked which questions to prevent duplicate votes.

The schema uses UTC timestamps (`TIMESTAMPTZ`) and integer surrogate keys. Soft deletes are not included at this stage; archival can be handled in future iterations.

## users

| Column          | Type         | Constraints / Defaults                   | Notes |
| --------------- | ------------ | ---------------------------------------- | ----- |
| `id`            | `SERIAL`     | `PRIMARY KEY`                            | Surrogate key |
| `display_name`  | `TEXT`       | `NOT NULL`                               | UI-friendly name shown in sessions |
| `created_at`    | `TIMESTAMPTZ`| `NOT NULL DEFAULT now()`                 | Creation timestamp |

**Relationships**
- Any `user` can host sessions they create (`sessions.host_user_id`). Business rule: a user may host at most three active sessions at a time.
- A `user` may author many `questions` (`questions.author_user_id`), though this FK can be nullable to support anonymous submissions. Business rule: limit each user to three active questions per session to keep queues manageable.

## sessions

When a user creates a session they automatically become the host. The system generates a `code` that the host shares; any other user can enter the code to join without needing authentication.

| Column              | Type          | Constraints / Defaults                         | Notes |
| ------------------- | ------------- | ---------------------------------------------- | ----- |
| `id`                | `SERIAL`      | `PRIMARY KEY`                                  | |
| `host_user_id` | `INTEGER`     | `NOT NULL`, `REFERENCES users(id)`             | Creator who hosts the room |
| `code`              | `TEXT`        | `NOT NULL`, `UNIQUE`                           | Shared password/join key issued on creation |
| `title`             | `TEXT`        | `NOT NULL`                                     | Displayed to participants |
| `status`            | `TEXT`        | `NOT NULL`, `CHECK (status IN ('draft','active','ended'))`, default `'draft'` | Lifecycle control |
| `created_at`        | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()`                       | |
| `started_at`        | `TIMESTAMPTZ` | `NULL`                                         | Populated when activated |
| `ended_at`          | `TIMESTAMPTZ` | `NULL`                                         | Populated when closed |

**Relationships**
- One session has many questions (`questions.session_id`).
- Future enhancement: a join table (`session_participants`) if we need to track per-student presence/state.

## questions

| Column             | Type          | Constraints / Defaults                                               | Notes |
| ------------------ | ------------- | -------------------------------------------------------------------- | ----- |
| `id`               | `SERIAL`      | `PRIMARY KEY`                                                        | |
| `session_id`       | `INTEGER`     | `NOT NULL`, `REFERENCES sessions(id)`                                | Owning session |
| `author_user_id`   | `INTEGER`     | `NULL`, `REFERENCES users(id)`                                       | Nullable for anonymous mode |
| `body`             | `TEXT`        | `NOT NULL`, length validated in application (target ≤ 280 chars)     | Question content |
| `status`           | `TEXT`        | `NOT NULL`, `CHECK (status IN ('pending','answered'))`, default `'pending'` | Marks resolution |
| `likes`            | `INTEGER`     | `NOT NULL DEFAULT 0`, `CHECK (likes >= 0)`                            | Denormalised count maintained alongside `question_votes` |
| `created_at`       | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()`                                             | |
| `answered_at`      | `TIMESTAMPTZ` | `NULL`                                                               | Timestamp for host resolution |

**Relationships**
- Each question belongs to one session.
- Author FK allows linking back to the submitting user when available.

**Cardinality Constraints**
- `users → sessions`: max three concurrent sessions per host. Enforced in services and, once migrations exist, via a partial unique index on `(host_user_id, status)` filtering on `status IN ('draft','active')`.
- `users → questions`: max three non-answered questions per author per session. Enforced in services and, optionally, via a partial unique index on `(author_user_id, session_id, status)` with `status = 'pending'`.
- `users → session_participants`: a user can appear at most once per session. Enforced with a unique index on `(session_id, user_id)`.
- `users → question_votes`: a user can like a question only once. Enforced with a unique index on `(question_id, voter_user_id)`.

## session_participants

| Column         | Type          | Constraints / Defaults                  | Notes |
| -------------- | ------------- | --------------------------------------- | ----- |
| `id`           | `SERIAL`      | `PRIMARY KEY`                           | |
| `session_id`   | `INTEGER`     | `NOT NULL`, `REFERENCES sessions(id)`   | Owning session |
| `user_id`      | `INTEGER`     | `NOT NULL`, `REFERENCES users(id)`      | Participant (host is also tracked) |
| `role`         | `TEXT`        | `NOT NULL`, `CHECK (role IN ('host','participant'))` | Lightweight role for UI hints |
| `joined_at`    | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()`                | First join timestamp |

**Relationships**
- Links users to the sessions they have joined; the row for the host is inserted at session creation.
- Provides a foundation for attendance tracking and session analytics.

## question_votes

| Column           | Type          | Constraints / Defaults                       | Notes |
| ---------------- | ------------- | -------------------------------------------- | ----- |
| `id`             | `SERIAL`      | `PRIMARY KEY`                                | |
| `question_id`    | `INTEGER`     | `NOT NULL`, `REFERENCES questions(id)`       | Target question |
| `voter_user_id`  | `INTEGER`     | `NOT NULL`, `REFERENCES users(id)`           | User who liked the question |
| `created_at`     | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()`                     | Vote timestamp |

**Relationships**
- Each vote ties a user to a question. The unique index on `(question_id, voter_user_id)` prevents duplicate likes.
- The aggregate `likes` column on `questions` should be kept in sync via repository or database triggers (future consideration).

## Indexes & Constraints

- `sessions_code_key` (unique) — ensures join codes are one-to-one with sessions.
- `questions_session_status_idx` on `(session_id, status)` — speeds up fetching unanswered questions.
- `questions_session_likes_idx` on `(session_id, likes DESC)` — optional for ordering by popularity.
- Foreign keys should cascade deletes judiciously. Proposed behaviour: deleting a user should either be blocked when references exist, or handled via application-level archival; deleting a session should cascade to questions for cleanup.

## Integration Notes

- **Migrations**: store SQL migrations under `backend/migrations/` (e.g., `0001_initial.sql`) and add a lightweight runner script under `scripts/`. Ensure container startup applies migrations before serving traffic.
- **Repositories**: implement dedicated repository modules (`users.py`, `sessions.py`, `session_participants.py`, `questions.py`, `question_votes.py`) in `backend/app/repositories/`, each with parameterised psycopg queries for CRUD operations and constraint enforcement.
- **Services & Routers**: expose business flows (session creation, joining, question submission, like toggles, status updates) via services in `backend/app/services/` and route handlers in `backend/app/api/routes/` using Pydantic schemas from `backend/app/schemas/`.
- **Testing**: extend `backend/tests/` with fixtures that create/truncate the new tables and integration tests covering the main flows.
- **Configuration**: update `.env` and settings when we introduce new tunables like session code length or status enums exposed via config.
- **Join flow**: API services accept a session code from any user (no authentication required today) to attach them to the session context via the `session_participants` repository.
- **Vote flow**: Services must keep `questions.likes` consistent with `question_votes` (via transactional updates today, and potentially database triggers later).

_Next step_: agree on any tweaks here, then scaffold the initial migration and corresponding repository/service layers.
