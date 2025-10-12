# Sessions API

API documentation for frontend contributors integrating with the session creation flow.

## Base URL

- Local development via Docker: `http://localhost:8000`
- All endpoints are served under the same host; no version prefix is currently applied.

## Authentication

- Authentication is not required. Clients must supply the host display name and session title in the request body.

## Endpoints

| Method | Path        | Description                                    |
| ------ | ----------- | ---------------------------------------------- |
| POST   | `/sessions` | Create a new classroom session                 |
| GET    | `/sessions` | Retrieve recent joinable sessions              |

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

Expect a `200` response with an array of session objects.