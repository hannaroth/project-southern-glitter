# Sprint 1: walking skeleton

**Sprint goal:** a running-dinner app on staging with accounts, a Postgres database, demo data from a seed command, a list of upcoming dinners, and a working A/B test page.

**Status:** TODO (one line: on track / what slipped)

<!-- Kyle said in class on Nov 9 that he will add detail to this format; he mentioned project status,
this week's work, stories closed last week and a burn-up or burndown chart. Check the project page before
submitting. The GitHub Project's Insights tab has a burn-up chart: save a screenshot to img/ and link it here. -->
![Burn-up chart](img/sprint-1-burnup.png)

## What shipped

<!-- One line per closed issue, with its merged pull request. -->
- A/B test page at `/c6a680e`: #TODO, PR #TODO
- A/B stats at `/c6a680e/stats`: #TODO, PR #TODO
- Base app: sign up, log in and log out, with roles: #TODO, PR #TODO
- Seed command for demo data and grader accounts: #TODO, PR #TODO
- Upcoming dinners on the home page: #TODO, PR #TODO
- Staging on Render with a Neon Postgres database: #TODO, PR #TODO

## What works on staging now

Staging: TODO-URL

- Visitors see upcoming dinners on the home page.
- Students can sign up, log in and log out; the seeded admin can open the admin area.
- `/c6a680e` shows a sticky `kudos` or `thanks` button and records impressions and clicks; `/c6a680e/stats` returns the live counts and the preferred variant.

## Working with our agents

<!-- One concrete thing that worked or didn't, and what we changed. Example shape:
"The agent first put the A/B route at /c6a680e/, so Django redirected /c6a680e with a 301. We added
'GET /c6a680e returns 200 with no redirect' to the acceptance criteria and a test for it." -->
TODO

## Backlog changes for Sprint 2

- We switched to the running dinner idea, which Kyle approved on Nov 7.
- We added Kyle's suggestions to the backlog: a recipe database for menus, sharing, friends and calendar export.
- Everyone logs in with a password for now; signing in with a one-time email link moved to later.
- Sprint 2 commits to: admins creating dinners, team sign-up with a partner and a waitlist, sharing a dinner, and a production environment.
