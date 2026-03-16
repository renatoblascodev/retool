#!/usr/bin/env bash
set -euo pipefail

echo "── Installing backend dependencies ──────────────────────────────────────"
cd /workspace/backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "── Running backend migrations ───────────────────────────────────────────"
alembic upgrade head

echo "── Installing frontend dependencies ─────────────────────────────────────"
cd /workspace/frontend
npm ci

echo "── Dev container ready ──────────────────────────────────────────────────"
echo "  Backend : cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
