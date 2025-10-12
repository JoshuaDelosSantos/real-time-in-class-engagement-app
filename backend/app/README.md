# App Package

Core application code for the ClassEngage FastAPI service lives here.

- `main.py` configures the FastAPI application, middleware, static assets, and router wiring.
- `api/` contains modular FastAPI routers that translate HTTP requests into service calls.
- `services/` encapsulates business workflows and orchestrates repositories.
- `repositories/` performs data-access operations with parameterised queries.
- `schemas/` defines shared Pydantic request/response models.
- `db.py` houses lightweight helpers for connecting to PostgreSQL.
- `settings.py` centralises environment-dependent configuration such as `DATABASE_URL`.

## Example Flow

**Session Creation**

1. **Router** (`api/routes/sessions.py`):
   - Handles `POST /sessions` with a Pydantic schema (`SessionCreate`) validating `title` and optional `host_display_name`.
   - Calls `services.sessions.create_session()`.

2. **Service** (`services/sessions.py`):
   - Generates a unique 6-character join code using `secrets.token_urlsafe()`.
   - Validates that the host doesn't already have three active sessions (business rule).
   - Calls `repositories.sessions.insert_session()` and `repositories.session_participants.insert_participant()` to persist the session and host record.
   - Returns a `SessionSummary` schema.

3. **Repository** (`repositories/sessions.py`):
   - Executes parameterised SQL using `psycopg.sql.SQL` composition:
    ```python
    cur.execute(
       sql.SQL("INSERT INTO sessions (host_user_id, code, title, status) VALUES (%s, %s, %s, %s) RETURNING id"),
       (host_id, code, title, 'draft')
    )
    ```
   - Returns the inserted session ID.

**Question Submission**

1. **Router** (`api/routes/questions.py`):
   - Handles `POST /sessions/{code}/questions` with `QuestionCreate` schema (body ≤280 chars).
   - Calls `services.questions.submit_question()`.

2. **Service** (`services/questions.py`):
   - Validates the user hasn't exceeded three pending questions in this session.
   - Calls `repositories.questions.insert_question()`.
   - Returns a `QuestionRead` schema.

3. **Repository** (`repositories/questions.py`):
   - Inserts using parameterised SQL to prevent injection:
     ```python
     cur.execute(
         sql.SQL("INSERT INTO questions (session_id, author_user_id, body, status) VALUES (%s, %s, %s, %s) RETURNING id"),
         (session_id, author_id, body, 'pending')
     )
     ```

**Vote Toggle**

1. **Router** (`api/routes/votes.py`):
   - Handles `POST /sessions/{code}/questions/{question_id}/votes`.
   - Calls `services.question_votes.add_vote()`.

2. **Service** (`services/question_votes.py`):
   - Attempts to insert into `question_votes` with a unique constraint on `(question_id, voter_user_id)`.
   - On success, increments `questions.likes` transactionally.
   - Returns vote metadata.

3. **Repository** (`repositories/question_votes.py`):
   - Executes within a transaction to ensure `question_votes` insert and `questions.likes` update remain atomic.

Modules should avoid heavy framework logic; keep business rules and integrations in the appropriate layer so concerns remain separated as the project grows.