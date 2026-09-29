# Using the Postiz API from your phone and your scripts

Everything here assumes you have run the one-time setup in the README. You should
not need this file for day-to-day use: the API starts on its own when you log in.

## The short version

```bash
cd ~/postiz-fastapi
./postiz.sh doctor     # is everything healthy?
./postiz.sh restart    # something looks wrong
```

Your two URLs:

| Where | URL |
| --- | --- |
| This laptop | `http://127.0.0.1:8000` |
| Phone / other devices | `https://pop-os.tailff6725.ts.net` |

`./postiz.sh url` prints them, so you never have to remember.

The tailnet URL only works with the Tailscale app switched on, and only from a
device signed into your tailnet. Nothing is exposed to the public internet.

## Commands

| Command | What it does |
| --- | --- |
| `./postiz.sh start` | Start Postiz, wait until its API answers, then start FastAPI. |
| `./postiz.sh stop` | Stop the API, then the Postiz stack. |
| `./postiz.sh restart` | Stop and start both. Takes about 45 seconds. |
| `./postiz.sh status` | systemd status plus container state. |
| `./postiz.sh logs` | Follow all logs, Ctrl-C to exit. |
| `./postiz.sh url` | Print the local and tailnet URLs. |
| `./postiz.sh doctor` | Check every part of the path and name the fix. |
| `./postiz.sh install` | Reinstall the systemd units and re-enable them at boot. |

`start` and `restart` are not instant. They block until Postiz is genuinely
serving requests, so when the command returns the API is usable. That is
deliberate: it is much easier to trust than a start command that returns before
the thing works.

## What happens on boot

Nothing to do. Both services are systemd user units enabled at
`default.target`:

1. `postiz-stack.service` starts the 8 Docker containers and waits for the
   Postiz API to answer.
2. `postiz-fastapi.service` starts FastAPI and waits for `/health`.

Your account has `linger` enabled, so these start at boot even if you never log
in. You do not need to `cd` anywhere or run anything.

`postiz.sh stop` stops the containers, but Docker's own `restart: always`
policy means they come back at the next boot regardless. `stop` is for "I want
it quiet right now", not for "keep it off permanently".

## Calling it from your phone

Use a shell app (Termius, Blink, a-Shell) or the Shortcuts app. On iOS,
Tailscale must be on.

List posts:

```bash
curl https://pop-os.tailff6725.ts.net/api/posts
```

Schedule a post. Replace the id with a real `integration_ids` value from the
Postiz UI, and `__type` with the platform:

```bash
curl -X POST https://pop-os.tailff6725.ts.net/api/posts \
  -H 'Content-Type: application/json' \
  -d '{
        "content": "Posting from my phone",
        "integration_ids": ["PASTE-INTEGRATION-ID"],
        "scheduled_at": "2026-10-05T14:00:00Z",
        "settings": {"__type": "threads"}
      }'
```

Post immediately instead of scheduling by omitting `scheduled_at`.

### A shortcut worth setting up

In Shortcuts: **Get Contents of URL** with
`https://pop-os.tailff6725.ts.net/api/posts`, then show the result. That is the
whole integration.

## Calling it from a script or another app

There is no authentication on this API. Anyone who can reach it over your
tailnet can post to your social accounts. That currently means your iPhone,
this laptop, and the `john` device. If you ever share the tailnet, remove those
devices first with `tailscale logout`, or add a token (see "Adding a token
later").

For a quick manual request, do not use `-X POST` in a URL you paste into a
browser; use a tool that can send a JSON body.

## Troubleshooting

Run `./postiz.sh doctor` first. It names the problem and the fix.

**`GET /api/posts` returns 502 and doctor says Postiz is down.** The known
first-boot race: the Postiz frontend can report healthy before its API is ready.
Fix:

```bash
docker compose -f ~/postiz-stack/postiz-docker-compose/docker-compose.yaml \
  --project-directory ~/postiz-stack/postiz-docker-compose restart postiz
```

**`POST /api/posts` returns 502 saying an integration is not found.** You have
no channels connected yet. Connect one at `http://localhost:4007`.

**The tailnet URL does not load on your phone.** Tailscale is off, or the
device is not on your tailnet. Check with `tailscale status`. The laptop copy at
`http://127.0.0.1:8000` will still work.

**`tailscale serve` was never configured.** Run this once, with your password:

```bash
sudo tailscale set --operator=$USER
./postiz.sh doctor
```

If you skip that, the API is still reachable on the laptop; only remote access
is missing.

**`404` on every route, or the key is rejected.** The `.env` file may be
missing or unreadable, because settings are loaded from a path relative to the
working directory. Check `systemctl --user show postiz-fastapi.service -p
WorkingDirectory`, and confirm `~/postiz-fastapi/.env` still exists and is
mode 600.

**Two copies of the service.** If you ever started uvicorn by hand, the
systemd unit cannot bind port 8000. Find the stray process, kill it, then
`./postiz.sh restart`.

## Adding a token later

If you want the API to reject anything that is not explicitly authorised, the
change is small: a dependency that checks an `X-API-Key` header against a
secret in `.env`, applied to the `/api` routes only, plus tests. Not built
today because you chose tailnet-only access.

## Where things live

| Thing | Path |
| --- | --- |
| This API | `~/postiz-fastapi` |
| Postiz stack | `~/postiz-stack/postiz-docker-compose` |
| Installed units | `~/.config/systemd/user/postiz-{stack,fastapi}.service` |
| Postiz UI (laptop only) | `http://localhost:4007` |
| Postiz credentials | `~/postiz-stack/credentials.md`, mode 600 |
| API key in use | `~/postiz-fastapi/.env`, mode 600 |
