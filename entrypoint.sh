#!/bin/sh
set -e

echo "==> Seeding database..."
python scripts/seed_test_data.py

echo "==> Starting CDM Portal..."
exec python -m reflex run --loglevel warning
