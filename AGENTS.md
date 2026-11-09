# Instructions for AI agents

Team southern-glitter (Yale MGT 656) is building a running-dinner web app for Yale and New Haven: teams of two sign up for a dinner, each team hosts one course and eats the other two at other teams' homes, and everyone meets at an after-party. These rules apply to every AI agent working in this repo, whichever tool it runs in.

## Read first

- The course's project requirements, which are the grading rules: https://www.656.mba/#/assignments/project-final-submission
- `docs/backlog.md`: every user story with its acceptance criteria. The GitHub issues are created from it.
- `docs/proposal.md`: the approved idea ("New Idea 1: Running dinner for New Haven").
- `docs/decisions.md`: what the team decided and what Kyle told us, with dates. Follow it; if your issue conflicts with it, ask.

## Team

| Person | Course nickname | GitHub |
|---|---|---|
| Nicola | magnificent-aardvark | nicode656 |
| Hanna (repo owner) | stormy-zebra | hannaroth |
| Jason | delightful-crocodile | kawaiibunny202 |

## Stack

- Django and PostgreSQL. Pages are rendered on the server with a CSS framework (Bootstrap or Pico); no single-page front-end framework.
- Hosting: Render for the app, Neon for the database. Staging deploys `main` automatically; production arrives in Sprint 2. Each environment has its own database.
- AI features call an LLM through OpenRouter from the server, never from browser JavaScript.

## How to work

1. Work on exactly one GitHub issue at a time (`gh issue view <number>`). Its acceptance criteria are your spec. If something is unclear or looks wrong, stop and ask the person you are working with instead of guessing.
2. Start from the latest `main`. Name the branch `<issue number>-<short-name>`, for example `7-ab-test-page`.
3. Change only what the issue needs. Don't reformat or restructure unrelated files, and don't add dependencies or change settings unless the issue asks for it; if you need one, say why first.
4. Write tests for every acceptance criterion. Tests never call the real LLM or any outside service; mock them. Run the whole test suite before you open a pull request.
5. Never put passwords, API keys or other secrets in code, commits, issues, pull requests or chat. Configuration comes from environment variables; list every variable name, without a value, in `.env.example`.
6. Change the database only through migrations.
7. Open a pull request into `main`:
   - Title: the issue title.
   - Body: `Closes #<issue number>` on the first line, then a short summary, how to test it, and a section "What the AI produced / what we changed or rejected" that the human fills in.
   - Request a review from the reviewer named in the issue.
8. Never push to `main`, never force-push, never merge your own pull request, and don't change other people's branches, issues or pull requests.

## App rules

- **Logins:** Django's built-in authentication, with email as the login name. Two roles from day one: admin (`is_staff`) and participant. No email verification and no two-factor, because graders log in with a username and password.
- **A/B test page:** exactly `/c6a680e` (no trailing slash, no redirect) and its stats at `/c6a680e/stats`. Both are public, with no login and no pop-up or cookie banner. The full spec is in `docs/backlog.md`. Don't change these routes unless your issue is about them.
- **Configuration (12-factor):** the app reads `DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` and `PORT` from the environment (later also `OPENROUTER_API_KEY`), listens on `$PORT`, logs to stdout and keeps no lasting data on local disk.
- **Seed command:** `python manage.py seed` creates the demo data and the grader accounts, is safe to run twice, takes the grader passwords from `SEED_ADMIN_PASSWORD` and `SEED_MEMBER_PASSWORD`, and uses fake names and `@example.com` emails only.

## Commands

The base app pull request fills this in: how to install, run the server, run the tests, run migrations and seed.

## Course documents (graded on `main`)

- `docs/mgt656/team.yaml`: team and stack
- `docs/mgt656/sprints/sprint-N.md`: one short report per sprint, screenshots in `docs/mgt656/sprints/img/`
- `docs/mgt656/technical.md`: technical-challenge items and testing strategy
- `docs/mgt656/retrospective.md`: final retrospective
