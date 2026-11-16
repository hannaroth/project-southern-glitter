# project-southern-glitter
MGT 656 team project (team southern-glitter)

A running-dinner web app for Yale and New Haven. Teams of two sign up for a dinner, each team hosts one course and eats the other two at other teams' homes, and everyone meets at an after-party.

Live app: **production** https://yale-running-dinner.onrender.com · **staging** https://running-dinner-staging.onrender.com

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

The tests need a PostgreSQL database in `DATABASE_URL` whose user may create databases (Django creates and drops `test_<name>`). Run them with `DEBUG=true` (or a `SECRET_KEY`) set.

## Claude Code shortcuts

The repo includes Claude Code subagents (`.claude/agents/`) and commands (`.claude/skills/`). Start a coordinating session in the repo with `claude --model opus`, then type one of these:

| Command | What it does |
|---|---|
| `/build-chain 12 26 27` | Builds the issues in order, each on top of the previous one when it isn't merged yet. A Sonnet `issue-builder` subagent writes each one, a separate `verifier` subagent re-runs the tests and checks it against the sprint plan, and then the pull request is opened with the reviewer from the issue. It never merges. |
| `/review-pr 19` | Reviews the open pull request that closes #19 with the `verifier`, shows a short verdict, and approves and merges only after you answer "approve" (or requests changes after "changes"). |
| `/sprint-report 2` | Writes `docs/mgt656/sprints/sprint-2.md` from GitHub data and opens its pull request. You can add agent lessons after the number. |

The same rules apply as everywhere: `AGENTS.md` and the current `docs/sprint-*-plan.md`.

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

## Deploying to production

We have two Render services with separate Neon databases:

| Environment | URL | Deploys | When |
|---|---|---|---|
| Staging | https://running-dinner-staging.onrender.com | branch `main` | automatically, on every merge |
| Production | https://yale-running-dinner.onrender.com (Render service `yale-running-dinner`) | branch `production` | only when someone runs **Promote to production** |

Nobody pushes to `production` by hand. To deploy, run the **Promote to production** workflow (`.github/workflows/promote.yml`):

- **In the browser:** repo → **Actions** tab → **Promote to production** (left list) → **Run workflow** → leave "Commit" empty for the latest `main` → **Run workflow**.
- **From a terminal:** `gh workflow run promote.yml` (or `gh workflow run promote.yml -f sha=<commit>` for a specific commit on `main`).

The workflow refuses to promote unless:

1. the commit is on `main`,
2. the **tests** check passed on that commit (if CI is still running, wait and run it again), and
3. `production` can move forward to it (fast-forward only, never a force-push; promoting an older commit than the one live is refused).

It then pushes the commit to `production`, and Render deploys it within a few minutes. The run's summary page shows which commit was promoted and what was live before. The same checks live in `scripts/promote.sh`, which the workflow calls.

After promoting, check production: the home page, both grader logins, and `/c6a680e/stats`.

If anyone protects the `production` branch later, allow GitHub Actions to push to it, or the workflow will fail at the push step.
