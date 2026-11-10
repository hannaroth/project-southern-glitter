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

The tests need a PostgreSQL database in `DATABASE_URL` whose user may create databases (Django creates and drops `test_<name>`). Run them with `DEBUG=true` (or a `SECRET_KEY`) set.

## Seed data and grader accounts

`python manage.py seed` creates two accounts and three upcoming demo dinners ("Around the World", "Through the Eras", "No Theme, Just Dinner"):

| Account | Role |
|---|---|
| `admin@example.com` (Ada Admin) | admin: `is_staff` and `is_superuser`, can open `/admin/` |
| `member@example.com` (Max Member) | participant |

The passwords come from the environment, never from the repo: set `SEED_ADMIN_PASSWORD` and `SEED_MEMBER_PASSWORD` first (names are in `.env.example`). If either is missing or empty, the command stops with an error and creates nothing. It never prints the passwords.

```bash
export SEED_ADMIN_PASSWORD='<choose-one>' SEED_MEMBER_PASSWORD='<choose-another>'
python manage.py seed
```

It is safe to run again. On a re-run it creates no duplicates: accounts are found by email and dinners by title. Each account's password and role flags are reset to the seeded values (a password is only rewritten if it differs), so staging always matches what the graders were told. A dinner dated today or later keeps its date; one whose date has passed is moved to a new upcoming Saturday (the first is the next Saturday at least 7 days away, the others 14 and 28 days after it).

On staging, set the two variables on Render. `build.sh` then runs the seed on every deploy (Render's free plan has no shell to run it by hand), so after a database reset a redeploy brings the demo data back. Without the two variables, `build.sh` skips the seed.

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
| `SEED_ADMIN_PASSWORD` | Password for `admin@example.com`; only read by `seed` |
| `SEED_MEMBER_PASSWORD` | Password for `member@example.com`; only read by `seed` |

On Render, `RENDER_EXTERNAL_HOSTNAME` is added to the allowed hosts and trusted origins automatically.

## Deploying on Render

- Build command: `./build.sh` (installs requirements, collects static files, runs migrations)
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Environment: `DATABASE_URL`, `SECRET_KEY`, and leave `DEBUG` unset.
