#!/usr/bin/env sh
set -eu

echo "[entrypoint] starting..."

# --- migrations ---
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] migrate..."
  python manage.py migrate --noinput
fi

# --- collectstatic ---
if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  echo "[entrypoint] collectstatic..."
  python manage.py collectstatic --noinput
fi

# --- create superuser (optional) ---
if [ "${CREATE_SUPERUSER:-0}" = "1" ]; then
  echo "[entrypoint] create default superuser..."
  python manage.py create_default_superuser || true
fi

echo "[entrypoint] exec: $*"
exec "$@"
