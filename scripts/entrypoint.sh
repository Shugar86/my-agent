#!/bin/sh

echo "[entrypoint] Running workflow template seed..."
python scripts/seed_workflow_templates.py --idempotent || echo "[entrypoint] WARNING: seed failed (non-fatal, DB may not be ready yet)"

echo "[entrypoint] Generating demo DOCX artifacts..."
python scripts/generate_demo_artifact.py || echo "[entrypoint] WARNING: artifact generation failed (non-fatal)"

exec "$@"
