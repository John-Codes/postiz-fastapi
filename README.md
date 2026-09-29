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

## Day-to-day use

Both the Postiz stack and this API start automatically at boot. To check them,
restart them, or see the URLs:

```bash
cd ~/postiz-fastapi
./postiz.sh doctor     # check everything and name any problem
./postiz.sh restart    # if something looks wrong
./postiz.sh url        # local and phone URLs
```

Your phone reaches the API at `https://pop-os.tailff6725.ts.net` (Tailscale
must be on). The Postiz UI stays laptop-only at `http://localhost:4007`.

**Phone and script usage, iOS Shortcuts, and troubleshooting: see
[USAGE.md](USAGE.md).**

## Setup

One-time, from a fresh clone:

```bash
cd ~/postiz-fastapi
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install pytest ruff

cp .env.example .env    # then paste POSTIZ_API_KEY into it
chmod 600 .env

./postiz.sh install     # install systemd units, enable at boot
./postiz.sh start
```

To run the API by hand instead (for development, not needed normally):

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

## How it is run

Two systemd **user** units, matching the existing `rag-api.service` on this
machine. `postiz-stack.service` brings up the containers and waits for the
Postiz API to answer; `postiz-fastapi.service` runs uvicorn and waits for
`/health`. Both are enabled at `default.target`, and `linger` is on, so they
run at boot without you logging in. The unit sources live in `deploy/` and are
copied into `~/.config/systemd/user/` by `./postiz.sh install`.

`postiz.sh` is a thin wrapper over `systemctl --user`; systemd stays the only
owner of the processes, so there is no PID file to drift out of sync.

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
| GET | `/api/posts` | List Postiz posts. Both bounds default to a 30 day window. |
| POST | `/api/posts` | Create or schedule a post. |

Interactive API docs are at http://127.0.0.1:8000/docs.

### GET /api/posts

```bash
curl "http://127.0.0.1:8000/api/posts?startDate=2026-09-01T00:00:00Z&endDate=2026-09-30T00:00:00Z"
```

```json
{"posts": [{"id": "...", "content": "...", "publishDate": "...", "state": "QUEUE",
            "releaseURL": null, "integration_id": "...", "integration_name": "..."}]}
```

### POST /api/posts

```bash
curl -X POST http://127.0.0.1:8000/api/posts \
  -H 'Content-Type: application/json' \
  -d '{
        "content": "Hello from the API",
        "integration_ids": ["<integration-id-from-postiz>"],
        "scheduled_at": null,
        "settings": {"__type": "threads"}
      }'
```

* `scheduled_at` omitted or `null` publishes immediately; a value schedules it.
* `settings.__type` is **required** and must be the Postiz platform identifier
  (`threads`, `bluesky`, `x`, `linkedin`, `instagram`, ...). It cannot be
  inferred — see the official
  [create post docs](https://docs.postiz.com/public-api/posts/create).
* `integration_ids` come from the Postiz UI, or
  `GET /api/public/v1/integrations` on the Postiz instance directly.

Response is `201` with `{"posts": [{"postId": "...", "integration": "..."}]}`.

## Configuration

All settings come from environment variables, read from `.env`. See
`.env.example`. `.env` is gitignored and must never be committed.

## Remote access

FastAPI binds to `127.0.0.1`. Remote devices reach it through Tailscale, which
gives you a tailnet-only HTTPS URL. No router port forwarding, no public
internet endpoint, and Funnel is never used.

This needs your sudo password, once:

```bash
sudo tailscale set --operator=$USER
tailscale serve --bg http://127.0.0.1:8000
```

The serve config lives inside `tailscaled`, so it survives reboots. Until it is
set, the API is reachable on localhost only. See [USAGE.md](USAGE.md).

## Security model

There is no authentication on this API. Access control is the tailnet itself:
any device signed into your tailnet can create posts on your social accounts.
That is a deliberate choice, and it is only safe while the tailnet contains
only your own devices. It currently also contains a device named `john`.

If that changes, either `tailscale logout` that device or add an `X-API-Key`
check (see the end of [USAGE.md](USAGE.md)).

## Known limitations

- **Creating a post needs a connected channel.** Postiz rejects an
  `integration_ids` value that is not connected, and this instance has no
  channels yet. Connect one in the Postiz UI, then re-run the POST example.
- **The Postiz UI stays local.** It is bound to `127.0.0.1:4007` and is not
  reachable from the phone. Serving it over Tailscale would also require
  setting `MAIN_URL`, `FRONTEND_URL` and `NEXT_PUBLIC_BACKEND_URL` to the
  Tailscale hostname, otherwise Postiz sets its login cookie for
  `Domain=localhost` and the session silently fails to apply.
- **The Postiz API can lag its container health** for a few seconds after a
  restart. `postiz.sh start` waits for the API, not the container, so this only
  shows up if you stop and start things by hand.

## Design rules

- One feature per folder; one reason to change per file.
- Every source file stays under 100 lines.
- Routes never call Postiz directly: `routes.py` -> `service.py` -> `postiz/client.py`.
- Postiz failures surface as `502`; the API key and internal URLs are never
  returned to callers or written to logs.
