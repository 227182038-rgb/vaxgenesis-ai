#!/usr/bin/env bash
set -euo pipefail
echo "=== VaxGenesis AI Setup ==="
cp -n .env.example .env 2>/dev/null || true
cd apps/backend && pip install -e ".[dev]" && cd ../..
cd apps/frontend && npm install --legacy-peer-deps && cd ../..
echo "Done. Run: make dev"
