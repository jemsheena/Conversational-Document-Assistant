#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-latest}"
REGISTRY="${REGISTRY:-ghcr.io}"
REPO_OWNER="${REPO_OWNER:?REPO_OWNER is required (GitHub username or org)}"
APP_DIR="${APP_DIR:-$HOME/Conversational-Document-Assistant}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

mkdir -p "$APP_DIR/backend/data" "$APP_DIR/deploy/scripts"
cd "$APP_DIR"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: $COMPOSE_FILE not found in $APP_DIR"
  exit 1
fi

export BACKEND_IMAGE="${REGISTRY}/${REPO_OWNER}/conversational-document-assistant-backend:${IMAGE_TAG}"
export FRONTEND_IMAGE="${REGISTRY}/${REPO_OWNER}/conversational-document-assistant-frontend:${IMAGE_TAG}"

echo "Deploying backend:  $BACKEND_IMAGE"
echo "Deploying frontend: $FRONTEND_IMAGE"

# Log in on the server only — store GHCR_TOKEN in EC2 .env, not in GitHub.
if [ -f .env ] && grep -q '^GHCR_TOKEN=' .env 2>/dev/null; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [ -n "${GHCR_TOKEN:-}" ]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$REPO_OWNER" --password-stdin
fi

echo "Disk before cleanup:"
df -h / || true
docker system df || true

# Stop containers so old app images can be removed (postgres data stays in its volume).
docker compose -f "$COMPOSE_FILE" down --remove-orphans || true

BACKEND_REPO="${REGISTRY}/${REPO_OWNER}/conversational-document-assistant-backend"
FRONTEND_REPO="${REGISTRY}/${REPO_OWNER}/conversational-document-assistant-frontend"
for repo in "$BACKEND_REPO" "$FRONTEND_REPO"; do
  mapfile -t old_ids < <(docker images "$repo" -q | sort -u)
  if [ "${#old_ids[@]}" -gt 0 ]; then
    echo "Removing old images for $repo"
    docker rmi -f "${old_ids[@]}" || true
  fi
done

docker image prune -af >/dev/null 2>&1 || true
docker builder prune -af >/dev/null 2>&1 || true

echo "Disk after cleanup:"
df -h / || true
docker system df || true

MIN_FREE_KB=1500000
avail_kb="$(df / | tail -1 | awk '{print $4}')"
if [ "${avail_kb:-0}" -lt "$MIN_FREE_KB" ]; then
  echo "ERROR: Insufficient disk space (${avail_kb}KB free, need at least ${MIN_FREE_KB}KB)."
  echo "Free space on the EC2 root volume or increase the EBS volume size, then redeploy."
  exit 1
fi

docker compose -f "$COMPOSE_FILE" pull
docker compose -f "$COMPOSE_FILE" up -d
docker compose -f "$COMPOSE_FILE" ps
