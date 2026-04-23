# Task: Fix the Broken OrderFlow Service

## Background

You are a backend engineer who has just been handed a Python microservice called **OrderFlow**.
It was written by a developer who left the company last week. The service is supposed to be
a simple order processing API backed by Redis, with a Celery worker that handles async jobs.

Nothing works. Your job is to make it work.

---

## Service Layout

All files live under `/app/`:

```
/app/
├── app/
│   ├── __init__.py        # Flask application factory
│   ├── routes.py          # REST API route handlers
│   ├── models.py          # Order data access layer (Redis)
│   ├── worker.py          # Celery application instance
│   └── tasks.py           # Celery background tasks
├── config.py              # Centralised configuration
├── run.py                 # Flask entry point
├── requirements.txt       # Pinned Python dependencies
└── docker-compose.yml     # Local dev stack (redis + web + worker)
```

---

## What the Service Should Do

**`POST /orders`**
Accepts JSON `{"item": "<string>", "quantity": <positive int>}`.
Saves the order to Redis, enqueues a background Celery task, returns:
```json
{"order_id": "<uuid>", "status": "queued"}
```
with HTTP **202**.

**`GET /orders/<order_id>`**
Fetches the order from Redis.
Returns HTTP **200** on success, **404** if the order does not exist.

**`GET /health`**
Returns `{"status": "ok"}` with HTTP **200**.

**Celery worker**
Picks up queued tasks, waits 1 second (simulated processing), then updates
the order's status in Redis from `"queued"` to `"processed"`.

---

## Your Job

The codebase has multiple bugs introduced across different files. Find and fix all of them.

- Edit files **in-place** under `/app/` — do not rewrite the whole codebase from scratch.
- Redis is available at the hostname `redis` on port `6379`.
- The Flask app must start cleanly on **port 5000**.
- The Celery worker must be able to start and connect to Redis.
- Do **not** install packages that are not already in `requirements.txt`.
- All output files must stay under `/app/`.

---

## Acceptance Criteria

- `GET /health` → `200 {"status": "ok"}`
- `POST /orders` (valid payload) → `202 {"order_id": "...", "status": "queued"}`
- `POST /orders` (missing or invalid fields) → `400`
- `GET /orders/<id>` (exists) → `200` with full order data
- `GET /orders/<id>` (unknown) → `404`
- `app.tasks` module can be imported without errors
- Celery is configured with a valid Redis broker URL and result backend
