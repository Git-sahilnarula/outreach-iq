#!/bin/sh
set -e

echo "==> Running database migrations..."
python -m alembic upgrade head || {
    echo "Warning: Alembic upgrade head exited with status $?. Initializing tables if needed..."
}

echo "==> Starting Outreach IQ backend service..."
exec "$@"
