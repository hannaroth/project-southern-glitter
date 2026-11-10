# project-southern-glitter
MGT 656 team project (team southern-glitter)

A running-dinner web app for Yale and New Haven. Teams of two sign up for a dinner, each team hosts one course and eats the other two at other teams' homes, and everyone meets at an after-party.

Stack: Django 5.2 and PostgreSQL, server-rendered pages styled with [Pico CSS](https://picocss.com). Hosting: Render (app) and Neon (database). The rules for AI agents are in `AGENTS.md`; the backlog is in `docs/backlog.md`.

## Run it locally

Needs Python 3.13 and a PostgreSQL database.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then fill in DATABASE_URL and set DEBUG=true
set -a; source .env; set +a # load the variables into your shell

python manage.py migrate
python manage.py createsuperuser   # optional: an admin (email + password)
python manage.py runserver
```

Open http://localhost:8000. Sign up at `/signup/`, log in at `/login/`. Admins (users with `is_staff`) can open `/admin/`; everyone else is a participant and is refused there.

## Commands

| Task | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Run the server | `python manage.py runserver` |
| Run the tests | `python manage.py test` |
| Create or apply migrations | `python manage.py makemigrations` / `python manage.py migrate` |
| Check for missing migrations | `python manage.py makemigrations --check` |
| Production-style check | `python manage.py check --deploy` |
| Lint (same as CI) | `pip install ruff` then `ruff check .` |

Every pull request into `main` runs the linter, the missing-migrations check and the whole test suite on GitHub Actions against a throwaway Postgres (`.github/workflows/tests.yml`). The result shows as the **tests** check on the pull request.

The tests need a PostgreSQL database in `DATABASE_URL` whose user may create databases (Django creates and drops `test_<name>`). Run them with `DEBUG=true` (or a `SECRET_KEY`) set. `python manage.py seed` (demo data and grader accounts) arrives with issue #6.

## Environment variables

Names are listed in `.env.example`; never commit values.

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | Postgres connection URL |
| `SECRET_KEY` | Django secret key; required unless `DEBUG` is on |
| `DEBUG` | `true` for local development; unset or anything else means off |
| `ALLOWED_HOSTS` | Comma-separated host names |
| `CSRF_TRUSTED_ORIGINS` | Optional, comma-separated, e.g. `https://example.com` |
| `PORT` | Port to listen on (set by Render) |

On Render, `RENDER_EXTERNAL_HOSTNAME` is added to the allowed hosts and trusted origins automatically.

## Deploying on Render

- Build command: `./build.sh` (installs requirements, collects static files, runs migrations)
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Environment: `DATABASE_URL`, `SECRET_KEY`, and leave `DEBUG` unset.
