# Decisions and course guidance

Why things are the way they are. Add a line when the team decides something or Kyle tells us something; don't rewrite old lines, add a new one that replaces them. The rules for AI agents are in `AGENTS.md`, the work in `docs/backlog.md`.

## Decisions we've made

| Date | Decision | Choice | Why |
|---|---|---|---|
| Nov 9 | Framework | Django | Built-in login and admin area; Kyle's template uses it |
| Nov 9 | Database and hosting | Postgres on Neon, app on Render, staging now and production from Sprint 2, under Hanna's accounts | The course's recommendation; Render's auto-deploy connects through the repo owner's GitHub |
| Nov 9 | Logins | Django's built-in authentication, email as the login name, admin and participant roles from day one, no email verification | Graders need a username and password; Kyle: build auth in from the start |
| Nov 9 | Participant sign-in by one-time email link | Postponed to Sprint 4, optional | Password login covers Sprints 1 to 3 |
| Nov 9 | Working rules | A branch per issue, a pull request with `Closes #N`, a teammate reviews, nobody merges their own pull request | The course's process rules |
| Nov 9 | Who merges | The reviewer named in the issue approves the pull request, then merges it | Keeps the author from merging their own work; nobody has to wait for Hanna |
| Nov 9 | Sprint 1 owners | Hanna: GitHub Project setup, backlog issues, staging, submission. Nicola: base app, seed command, dinners list, report. Jason: A/B page and stats, tests on every pull request, check on staging. Each issue names its owner and reviewer. | Split at the Sprint 1 meeting; Hanna owns what needs the repo owner's account |
| Nov 9 | Check-in | Tuesday, TODO time | Catch blockers before the Wednesday deadline |

## What Kyle has told us

- **Nov 7, approval email:** approved the running dinner idea. Asked for a recipe database, sharing a dinner, friends, calendar export and proper authentication. All five are in the backlog.
- **Nov 9, lecture:**
  - Our AI agents can set up the GitHub Project and its issues through GitHub's API.
  - Build login and roles from the start; auth should never be added later.
  - He will add detail to the sprint report format: project status, this week's work, stories closed and a burn-up or burndown chart. Check the project page before each submission.
  - Render and Neon remain his recommended hosting.
