#!/usr/bin/env bash
# Control the Postiz stack and the FastAPI wrapper.
# Thin wrapper over `systemctl --user` so systemd stays the only owner of the
# processes. Set POSTIZ_API_URL to the public API base and POSTIZ_API_KEY to the
# owner key from the Postiz UI.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_UNIT=postiz-stack.service
API_UNIT=postiz-fastapi.service
USER_UNITS="$HOME/.config/systemd/user"

usage() {
  cat <<'EOF'
Usage: postiz.sh <command>

  start      Start the Postiz stack, then the API
  stop       Stop the API, then the Postiz stack
  restart    Restart both
  status     Show systemd status and container state
  logs       Follow API and stack logs (Ctrl-C to stop)
  url        Print the local and tailnet URLs
  install    Install/refresh the systemd units and enable them at boot
  doctor     Check the whole path and report what is wrong
EOF
}

cmd_start() {
  systemctl --user start "$STACK_UNIT"
  systemctl --user start "$API_UNIT"
  echo "Started. Run 'postiz.sh doctor' to confirm, 'postiz.sh url' for URLs."
}

cmd_stop() {
  systemctl --user stop "$API_UNIT" || true
  systemctl --user stop "$STACK_UNIT" || true
  echo "Stopped."
}

cmd_status() {
  systemctl --user --no-pager --lines=0 status "$API_UNIT" "$STACK_UNIT" || true
  echo
  docker compose -f "$REPO/../postiz-stack/postiz-docker-compose/docker-compose.yaml" \
    --project-directory "$REPO/../postiz-stack/postiz-docker-compose" ps 2>/dev/null || true
}

cmd_logs() {
  journalctl --user -u "$API_UNIT" -u "$STACK_UNIT" -f
}

cmd_url() {
  local host
  host="$(tailscale status --json 2>/dev/null | python3 -c \
    'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)"
  echo "local : http://127.0.0.1:8000"
  if [[ -n "$host" ]]; then
    echo "tailnet: https://$host"
  else
    echo "tailnet: (tailscale not available)"
  fi
}

cmd_install() {
  install -d "$USER_UNITS"
  install -m 644 "$REPO/deploy/$STACK_UNIT" "$USER_UNITS/$STACK_UNIT"
  install -m 644 "$REPO/deploy/$API_UNIT" "$USER_UNITS/$API_UNIT"
  systemctl --user daemon-reload
  systemctl --user enable "$STACK_UNIT" "$API_UNIT"
  echo "Installed and enabled at boot. Start now with: postiz.sh start"
}

case "${1:-}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_stop; cmd_start ;;
  status) cmd_status ;;
  logs) cmd_logs ;;
  url) cmd_url ;;
  install) cmd_install ;;
  doctor) exec "$REPO/doctor.sh" ;;
  "" | -h | --help | help) usage ;;
  *) echo "Unknown command: $1" >&2; usage >&2; exit 2 ;;
esac
