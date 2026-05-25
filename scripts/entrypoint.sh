#!/bin/sh
set -e

echo "[entrypoint] Running workflow template seed..."
python scripts/seed_workflow_templates.py --idempotent

echo "[entrypoint] Generating demo DOCX artifacts..."
python scripts/generate_demo_artifact.py

exec "$@"
