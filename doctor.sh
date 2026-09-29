#!/usr/bin/env bash
# End-to-end health check for the Postiz stack and the FastAPI wrapper.
# Exits non-zero if anything is broken. Never prints the API key.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_DIR="$HOME/postiz-stack/postiz-docker-compose"
LOCAL="http://127.0.0.1:8000"
POSTIZ="http://127.0.0.1:4007/api/public/v1"
fails=0

ok()   { printf '  ok    %s\n' "$1"; }
warn() { printf '  warn  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fails=$((fails + 1)); }

api_key="$(sed -n 's/^POSTIZ_API_KEY=//p' "$REPO/.env" 2>/dev/null | head -1)"

echo "host"
if docker info >/dev/null 2>&1; then ok "docker daemon running"; else bad "docker daemon not running"; fi
if [[ "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null)" == "yes" ]]; then
  ok "linger enabled (services start without login)"
else
  bad "linger disabled; run: sudo loginctl enable-linger $USER"
fi

echo "postiz stack"
running="$(docker compose -f "$STACK_DIR/docker-compose.yaml" \
  --project-directory "$STACK_DIR" ps --status=running --format '{{.Service}}' 2>/dev/null | wc -l)"
if [[ "$running" -ge 8 ]]; then ok "8 containers up ($running found)"
else bad "only $running/8 containers up; try: postiz.sh start"; fi
unhealthy="$(docker ps --filter "health=unhealthy" --format '{{.Names}}' 2>/dev/null | wc -l)"
[[ "$unhealthy" -eq 0 ]] && ok "no unhealthy containers" || bad "$unhealthy unhealthy container(s)"

if [[ -n "$api_key" ]]; then
  connected="$(curl -fs --max-time 10 -H "Authorization: $api_key" "$POSTIZ/is-connected" 2>/dev/null)"
  if [[ "$connected" == *'"connected":true'* ]]; then ok "postiz API key accepted"
  else bad "postiz rejected the API key; regenerate it in the Postiz UI"; fi
  integrations="$(curl -fs --max-time 10 -H "Authorization: $api_key" "$POSTIZ/integrations" 2>/dev/null | grep -o '"id"' | wc -l)"
  [[ "$integrations" -gt 0 ]] && ok "$integrations connected channel(s)" \
    || warn "no channels connected; POST /api/posts will fail until you connect one"
else
  bad "POSTIZ_API_KEY missing from $REPO/.env"
fi

echo "fastapi"
if [[ "$(systemctl --user is-active postiz-fastapi.service 2>/dev/null)" == "active" ]]; then
  ok "postiz-fastapi.service active"
else
  bad "postiz-fastapi.service not active; try: postiz.sh start"
fi
api_ok() {
  local n=0
  while [ "$n" -lt 3 ]; do
    curl -fs --max-time 5 "$1" >/dev/null 2>&1 && return 0
    n=$((n + 1))
    sleep 1
  done
  return 1
}

if api_ok "$LOCAL/health"; then ok "GET /health"
else bad "GET /health failed"; fi

if api_ok "$LOCAL/api/posts"; then ok "GET /api/posts reaches postiz"
else bad "GET /api/posts failed; postiz may be down or the key wrong"; fi

echo "tailnet"
state="$(tailscale status --json 2>/dev/null | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["BackendState"])' 2>/dev/null)"
if [[ "$state" == "Running" ]]; then ok "tailscale running"
else bad "tailscale not running (state: ${state:-unknown})"; fi
if tailscale serve status 2>/dev/null | grep -q "No serve config"; then
  warn "tailscale serve not configured; run: sudo tailscale set --operator=\$USER then postiz.sh doctor"
else
  ok "tailscale serve configured"
fi

echo
if [[ "$fails" -eq 0 ]]; then
  echo "All checks passed."
else
  echo "$fails check(s) failed."
fi
exit $(( fails > 0 ? 1 : 0 ))
