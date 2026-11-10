#!/usr/bin/env bash
# Render build command: ./build.sh
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Render's free plan has no shell, so seed here whenever both seed passwords are set.
# The command is safe to run on every deploy.
if [ -n "${SEED_ADMIN_PASSWORD:-}" ] && [ -n "${SEED_MEMBER_PASSWORD:-}" ]; then
  python manage.py seed
fi
