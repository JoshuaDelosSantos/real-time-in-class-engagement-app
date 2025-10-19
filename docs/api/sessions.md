# Sessions API

API documentation for frontend contributors integrating with the session creation flow.

## Base URL

- Local development via Docker: `http://localhost:8000`
- All endpoints are served under the same host; no version prefix is currently applied.

## Authentication

- Authentication is not required. Clients must supply the host display name and session title in the request body.

## Endpoints

| Method | Path                             | Description                                             |
| ------ | -------------------------------- | ------------------------------------------------------- |
| POST   | `/sessions`                      | Create a new classroom session                          |
| GET    | `/sessions`                      | Retrieve recent joinable sessions                       |
| GET    | `/sessions/{code}`               | Fetch detailed information for a single session         |
| GET    | `/sessions/{code}/participants`  | Retrieve the session participant roster                 |
| GET    | `/sessions/{code}/questions`     | Retrieve questions for a session (optionally filtered)  |
| POST   | `/sessions/{code}/join`          | Join a session as a participant                         |

---

## POST /sessions

Create a new classroom session and return a summary payload that includes the generated join code.

### Request

- **Headers**: `Content-Type: application/json`
- **Body (JSON)**:
  ```json
  {
    "title": "Literature Seminar",
    "host_display_name": "Prof. Bloom"
  }
  ```

#### Body Fields

| Field               | Type   | Required | Rules                                    |
| ------------------- | ------ | -------- | ---------------------------------------- |
| `title`             | string | Yes      | 1-200 characters                          |
| `host_display_name` | string | Yes      | 1-100 characters; identifies the session host |

### Successful Response

- **Status**: `201 Created`
- **Body (JSON)**:
  ```json
  {
    "id": 123,
    "code": "X4TZQF",
    "title": "Literature Seminar",
    "status": "draft",
    "host": {
      "id": 45,
      "display_name": "Prof. Bloom"
    },
    "created_at": "2025-10-12T07:10:12.345678Z"
  }
  ```

#### Response Fields

| Field         | Type   | Notes                                            |
| ------------- | ------ | ------------------------------------------------ |
| `id`          | int    | Session identifier                               |
| `code`        | string | Six-character join code, unique across sessions  |
| `title`       | string | Echo of the input title                          |
| `status`      | string | Initial value is `draft`                         |
| `host.id`     | int    | User identifier for the host                     |
| `host.display_name` | string | Echo of the input host display name            |
| `created_at`  | string | ISO 8601 timestamp in UTC                        |

### Error Responses

| Status | When it Occurs                               | Body Example |
| ------ | --------------------------------------------- | ------------ |
| 409    | Host already has three active sessions        | `{ "detail": "Host has reached the active session limit." }` |
| 422    | Validation error (empty title or display name)| `{ "detail": [ { "loc": ["body", "title"], "msg": "String should have at least 1 characters", "type": "string_too_short" } ] }` |

Validation is enforced by FastAPI/Pydantic. Provide non-empty strings for both fields to avoid 422 responses.

### Idempotency & Retries

- The endpoint is not idempotent; repeated calls create new sessions with different join codes.
- Join-code collisions are retried automatically until a unique code is generated.

### Testing Notes

You can exercise the endpoint locally with curl:

```bash
curl -X POST http://localhost:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"title": "Literature Seminar", "host_display_name": "Prof. Bloom"}'
```

Expect a `201` response with the JSON payload described above.

---

## GET /sessions

Retrieve a list of recent joinable sessions ordered by creation time (most recent first).

### Request

- **Query Parameters**:
  
  | Parameter | Type | Required | Default | Notes                                      |
  | --------- | ---- | -------- | ------- | ------------------------------------------ |
  | `limit`   | int  | No       | 10      | Maximum number of sessions to return (≥1)  |

### Successful Response

- **Status**: `200 OK`
- **Body (JSON)**:
  ```json
  [
    {
      "id": 124,
      "code": "Y7PQRS",
      "title": "History 202",
      "status": "active",
      "host": {
        "id": 46,
        "display_name": "Prof. Carter"
      },
      "created_at": "2025-10-12T08:15:30.123456Z"
    },
    {
      "id": 123,
      "code": "X4TZQF",
      "title": "Literature Seminar",
      "status": "draft",
      "host": {
        "id": 45,
        "display_name": "Prof. Bloom"
      },
      "created_at": "2025-10-12T07:10:12.345678Z"
    }
  ]
  ```

#### Response Fields

Each session object contains:

| Field                | Type   | Notes                                         |
| -------------------- | ------ | --------------------------------------------- |
| `id`                 | int    | Session identifier                            |
| `code`               | string | Six-character join code                       |
| `title`              | string | Session title                                 |
| `status`             | string | Either `draft` or `active` (ended sessions excluded) |
| `host.id`            | int    | Host user identifier                          |
| `host.display_name`  | string | Host display name                             |
| `created_at`         | string | ISO 8601 timestamp in UTC                     |

### Empty Result

If no sessions are available, the endpoint returns an empty array:

```json
[]
```

### Error Responses

| Status | When it Occurs              | Body Example                      |
| ------ | --------------------------- | --------------------------------- |
| 422    | Invalid limit parameter     | `{ "detail": [...] }`             |

### Filtering

- Only sessions with status `draft` or `active` are returned.
- Ended sessions are excluded from the list.

### Testing Notes

You can exercise the endpoint locally with curl:

```bash
# Fetch default limit (10 sessions)
curl http://localhost:8000/sessions

# Fetch with custom limit
curl http://localhost:8000/sessions?limit=5
```

```

Expect a `200` response with an array of session objects.

---

## GET /sessions/{code}

Retrieve the full details for a single session using its join code.

### Request

- **Path Parameters**:
  
  | Parameter | Type   | Required | Notes                           |
  | --------- | ------ | -------- | ------------------------------- |
  | `code`    | string | Yes      | Six-character session join code |

### Successful Response

- **Status**: `200 OK`
- **Body (JSON)**:
  ```json
  {
    "id": 123,
    "code": "X4TZQF",
    "title": "Literature Seminar",
    "status": "active",
    "host": {
      "id": 45,
      "display_name": "Prof. Bloom"
    },
    "created_at": "2025-10-12T07:10:12.345678Z"
  }
  ```

#### Response Fields

The payload matches the `SessionSummary` structure used elsewhere in this guide.

### Error Responses

| Status | When it Occurs          | Body Example               |
| ------ | ----------------------- | -------------------------- |
| 404    | Session code not found  | `{ "detail": "Session not found" }` |

### Testing Notes

```bash
curl http://localhost:8000/sessions/X4TZQF
```

Expect a `200` response with the session summary JSON payload when the session exists.

---

## GET /sessions/{code}/participants

List every participant registered for a session. The host always appears first, followed by the remaining participants ordered by their join time.

### Request

- **Path Parameters**:
  
  | Parameter | Type   | Required | Notes                           |
  | --------- | ------ | -------- | ------------------------------- |
  | `code`    | string | Yes      | Six-character session join code |

### Successful Response

- **Status**: `200 OK`
- **Body (JSON)**:
  ```json
  [
    {
      "id": 45,
      "display_name": "Prof. Bloom",
      "role": "host",
      "joined_at": "2025-10-12T07:10:12.345678Z"
    },
    {
      "id": 201,
      "display_name": "Student Alice",
      "role": "participant",
      "joined_at": "2025-10-12T07:12:00.123456Z"
    }
  ]
  ```

#### Response Fields

| Field         | Type   | Notes                                      |
| ------------- | ------ | ------------------------------------------ |
| `id`          | int    | Participant identifier                     |
| `display_name`| string | Participant display name                   |
| `role`        | string | Either `host` or `participant`             |
| `joined_at`   | string | ISO 8601 timestamp in UTC in join order    |

### Empty Result

New sessions return a single entry for the host until additional participants join.

### Error Responses

| Status | When it Occurs          | Body Example               |
| ------ | ----------------------- | -------------------------- |
| 404    | Session code not found  | `{ "detail": "Session not found" }` |

### Testing Notes

```bash
curl http://localhost:8000/sessions/X4TZQF/participants
```

Expect a `200` response with the ordered participant list.

---

## GET /sessions/{code}/questions

Fetch the list of questions submitted for a session. Questions are sorted oldest-first and can be filtered by status.

### Request

- **Path Parameters**:
  
  | Parameter | Type   | Required | Notes                           |
  | --------- | ------ | -------- | ------------------------------- |
  | `code`    | string | Yes      | Six-character session join code |

- **Query Parameters** (optional):
  
  | Parameter | Type   | Allowed Values       | Notes                                      |
  | --------- | ------ | -------------------- | ------------------------------------------ |
  | `status`  | string | `pending`, `answered`| Filter questions by moderation status      |

### Successful Response

- **Status**: `200 OK`
- **Body (JSON)**:
  ```json
  [
    {
      "id": 301,
      "body": "How will this impact the final exam?",
      "status": "pending",
      "created_at": "2025-10-12T07:13:11.654321Z",
      "author": {
        "id": 201,
        "display_name": "Student Alice"
      }
    },
    {
      "id": 302,
      "body": "Will slides be available afterwards?",
      "status": "answered",
      "created_at": "2025-10-12T07:14:05.000000Z",
      "author": null
    }
  ]
  ```

#### Response Fields

| Field             | Type   | Notes                                                          |
| ----------------- | ------ | -------------------------------------------------------------- |
| `id`              | int    | Question identifier                                            |
| `body`            | string | Question text                                                  |
| `status`          | string | Either `pending` or `answered`                                 |
| `created_at`      | string | ISO 8601 timestamp in UTC                                      |
| `author`          | object | Name and id of the submitter; `null` when no author is stored |
| `author.id`       | int    | Present when the author exists                                 |
| `author.display_name` | string | Present when the author exists                              |

### Empty Result

Returns an empty array when the session has no questions or none match the requested status filter.

### Error Responses

| Status | When it Occurs                  | Body Example               |
| ------ | ------------------------------- | -------------------------- |
| 404    | Session code not found          | `{ "detail": "Session not found" }` |
| 422    | Invalid status filter provided  | `{ "detail": [...] }`     |

### Testing Notes

```bash
# All questions
curl http://localhost:8000/sessions/X4TZQF/questions

# Only pending questions
curl "http://localhost:8000/sessions/X4TZQF/questions?status=pending"
```

Expect a `200` response with the filtered question list.

---

## POST /sessions/{code}/join

Join an existing classroom session as a participant using the session's join code.

### Request

- **Path Parameters**:
  
  | Parameter | Type   | Required | Notes                                      |
  | --------- | ------ | -------- | ------------------------------------------ |
  | `code`    | string | Yes      | Six-character session join code            |

- **Headers**: `Content-Type: application/json`
- **Body (JSON)**:
  ```json
  {
    "display_name": "Student Alice"
  }
  ```

#### Body Fields

| Field          | Type   | Required | Rules                                    |
| -------------- | ------ | -------- | ---------------------------------------- |
| `display_name` | string | Yes      | 1-100 characters; identifies the participant |

### Successful Response

- **Status**: `200 OK`
- **Body (JSON)**:
  ```json
  {
    "id": 123,
    "code": "X4TZQF",
    "title": "Literature Seminar",
    "status": "draft",
    "host": {
      "id": 45,
      "display_name": "Prof. Bloom"
    },
    "created_at": "2025-10-12T07:10:12.345678Z"
  }
  ```

#### Response Fields

Returns a `SessionSummary` object with the following fields:

| Field                | Type   | Notes                                         |
| -------------------- | ------ | --------------------------------------------- |
| `id`                 | int    | Session identifier                            |
| `code`               | string | Six-character join code                       |
| `title`              | string | Session title                                 |
| `status`             | string | Current session status (draft/active/ended)   |
| `host.id`            | int    | Host user identifier                          |
| `host.display_name`  | string | Host display name                             |
| `created_at`         | string | ISO 8601 timestamp in UTC                     |

### Error Responses

| Status | When it Occurs                               | Body Example |
| ------ | -------------------------------------------- | ------------ |
| 400    | Display name is whitespace-only              | `{ "detail": "Display name is required" }` |
| 404    | Session code does not exist                  | `{ "detail": "Session not found" }` |
| 409    | Session has ended and is no longer joinable  | `{ "detail": "Session has ended and is no longer joinable" }` |
| 422    | Validation error (empty or null display name)| `{ "detail": [ { "loc": ["body", "display_name"], "msg": "String should have at least 1 characters", "type": "string_too_short" } ] }` |

### Behavior Notes

- **User Creation**: If a user with the provided display name doesn't exist, one is created automatically.
- **Idempotency**: Joining the same session multiple times with the same display name is safe and returns success. The participant record is updated if it already exists.
- **Role Protection**: If the host joins their own session (matching display name), their role remains "host" rather than being downgraded to "participant".
- **Status Filtering**: Only sessions with status "draft" or "active" can be joined. Attempting to join an "ended" session returns 409.

### Testing Notes

You can exercise the endpoint locally with curl:

```bash
# First, create a session to get a join code
curl -X POST http://localhost:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"title": "Literature Seminar", "host_display_name": "Prof. Bloom"}'

# Then join the session using the code from the response
curl -X POST http://localhost:8000/sessions/X4TZQF/join \
  -H 'Content-Type: application/json' \
  -d '{"display_name": "Student Alice"}'
```

Expect a `200` response with the session summary JSON payload.
