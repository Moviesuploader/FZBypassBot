#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "$EUID" -ne 0 ]]; then
  echo "Run this script as root: sudo bash scripts/deploy.sh" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Engine is missing. Install Docker Engine and the Compose plugin first." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is missing. Install the Docker Compose plugin first." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env from .env.example."
  echo "Edit .env and set BOT_TOKEN, API_ID, API_HASH and OWNER_ID, then rerun."
  exit 2
fi

for key in BOT_TOKEN API_ID API_HASH OWNER_ID; do
  if ! grep -Eq "^\${key}=.+$" .env; then
    echo "Required setting is missing or empty in .env: ${key}" >&2
    exit 2
  fi
done

chmod 600 .env
mkdir -p data
chown 10001:10001 data
chmod 700 data

echo "Building FZBypassBot image..."
docker compose build --pull

echo "Starting FZBypassBot..."
docker compose up -d

echo "Waiting for Telegram bot readiness..."
for _ in $(seq 1 45); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' fzbypassbot 2>/dev/null || true)"
  if [[ "$state" == "healthy" ]]; then
    echo "FZBypassBot is healthy."
    docker compose ps
    exit 0
  fi
  if [[ "$state" == "exited" || "$state" == "dead" ]]; then
    echo "Container exited before becoming healthy." >&2
    docker compose logs --tail=100 fzbypass
    exit 1
  fi
  sleep 2
done

echo "Bot did not become healthy within 90 seconds." >&2
docker compose ps
docker compose logs --tail=100 fzbypass
exit 1
