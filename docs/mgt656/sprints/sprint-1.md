# Sprint 1: walking skeleton

**Sprint goal:** a running-dinner app on staging with accounts, a Postgres database, demo data from a seed command, a list of upcoming dinners, and a working A/B test page.

**Status:** On track — all six Sprint 1 stories are merged and live on staging.

## What shipped

- A/B test page at `/c6a680e`: #3, PR #35
- A/B stats at `/c6a680e/stats`: #4, PR #35
- Base app: sign up, log in and log out, with roles: #5, PR #36
- Seed command for demo data and grader accounts: #6, PR #38
- Upcoming dinners on the home page: #7, PR #37
- Staging on Render with a Neon Postgres database: #8 (set up directly on Render; no pull request)

## What works on staging now

Staging: https://running-dinner-staging.onrender.com

- Visitors see upcoming dinners on the home page.
- Students can sign up, log in and log out; the seeded admin can open the admin area.
- `/c6a680e` shows a sticky `kudos` or `thanks` button and records impressions and clicks; `/c6a680e/stats` returns the live counts and the preferred variant.

## Working with our agents

<!-- One concrete thing per person: what worked or didn't, and what you changed. -->
- **Nicola:** the agent's first pass on the base app treated `Ada@Example.com` and `ada@example.com` as two different logins. We caught it reviewing the pull request, had it store emails lowercase, and added two tests so it can't regress.
- **Jason:** TODO
- **Hanna:** TODO

## Backlog changes for Sprint 2

- We switched to the running dinner idea, which Kyle approved on Nov 7.
- We added Kyle's suggestions to the backlog: a recipe database for menus, sharing, friends and calendar export.
- Everyone logs in with a password for now; signing in with a one-time email link moved to later.
- Sprint 2 commits to: admins creating dinners, team sign-up with a partner and a waitlist, sharing a dinner, and a production environment.
