#!/bin/bash
# Meridian AI — Full Stack Startup Script
#
# This script:
#   1. Starts DataHub via Docker Compose
#   2. Waits for DataHub GMS to be healthy
#   3. Seeds the Meridian Commerce demo dataset
#   4. Starts the Meridian backend
#
# Usage:
#   bash scripts/start.sh              # start everything
#   bash scripts/start.sh --seed-only  # just seed data
#   bash scripts/start.sh --skip-seed  # skip seeding

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

SEED_ONLY=false
SKIP_SEED=false

for arg in "$@"; do
  case $arg in
    --seed-only) SEED_ONLY=true ;;
    --skip-seed) SKIP_SEED=true ;;
  esac
done

echo "============================================"
echo "  Meridian AI — Starting Full Stack"
echo "============================================"

# Step 1: Start Docker Compose
if [ "$SEED_ONLY" = false ]; then
  echo ""
  echo "[1/4] Starting Docker Compose..."
  docker compose up -d

  echo ""
  echo "[2/4] Waiting for DataHub GMS to be healthy..."
  for i in $(seq 1 60); do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
      echo "  DataHub GMS is ready!"
      break
    fi
    if [ $i -eq 60 ]; then
      echo "  ERROR: DataHub GMS did not start in 3 minutes"
      echo "  Check: docker compose logs datahub-gms"
      exit 1
    fi
    sleep 3
    echo -n "."
  done
fi

# Step 2: Seed DataHub
if [ "$SKIP_SEED" = false ]; then
  echo ""
  echo "[3/4] Seeding Meridian Commerce demo data..."
  DATAHUB_MOCK=false DATAHUB_GMS_URL=http://localhost:8080/api/gms \
    python scripts/seed_meridian.py
fi

# Step 3: Start Meridian Backend
if [ "$SEED_ONLY" = false ]; then
  echo ""
  echo "[4/4] Starting Meridian AI backend..."
  echo ""
  echo "  DataHub UI:   http://localhost:9002 (login: datahub / datahub)"
  echo "  Meridian API: http://localhost:8000/docs"
  echo "  Meridian UI:  http://localhost:3000"
  echo ""

  DATAHUB_MOCK=false \
    DATAHUB_GMS_URL=http://localhost:8080/api/gms \
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi

echo ""
echo "Done!"
