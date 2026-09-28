# Postiz FastAPI

A small FastAPI service in front of a self-hosted [Postiz](https://postiz.com)
instance. Postiz itself is installed separately via the official Docker Compose
deployment and is never modified by this project.

```
Tailscale
   |
   v
FastAPI   (this repo)
   |
   v
Postiz   (~/postiz-stack, official Docker Compose)
   |
   +-- PostgreSQL
   +-- Redis
   +-- Temporal
```

## Prerequisites

Postiz must be running first. See `~/postiz-stack/README.md` for how that stack is
installed, and `~/postiz-stack/credentials.md` for the login and API key.

## Setup

```bash
cd ~/postiz-fastapi
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install pytest ruff

cp .env.example .env    # then paste POSTIZ_API_KEY into it
```

## Run

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

## Test and lint

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Tests never need Docker, Postgres, Redis, Temporal or Tailscale.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness of this service only. Never calls Postiz. |
| GET | `/api/posts` | List Postiz posts in a date range. |
| POST | `/api/posts` | Create or schedule a post. |

Interactive API docs are at http://127.0.0.1:8000/docs.

## Configuration

All settings come from environment variables, read from `.env`. See
`.env.example`. `.env` is gitignored and must never be committed.

## Remote access

FastAPI binds to `127.0.0.1`. Remote devices reach it through Tailscale:

```bash
tailscale serve --bg http://127.0.0.1:8000
```

No router port forwarding and no public internet endpoint.

## Design rules

- One feature per folder; one reason to change per file.
- Every source file stays under 100 lines.
- Routes never call Postiz directly: `routes.py` -> `service.py` -> `postiz/client.py`.
- Postiz failures surface as `502`; the API key and internal URLs are never
  returned to callers or written to logs.
