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
| Nov 11 | Course requirements | The requirements repo (`yale-mgt-656-fall-2026/project-requirements`) replaces the old assignment page; no story points, velocity or burndown charts | Kyle moved the requirements there on Nov 11; this replaces his Nov 9 note about a burndown chart |
| Nov 15 | Who merges | The reviewer approves and merges right away once CI is green; the author never merges their own pull request | Confirms the Nov 9 rule; in Sprint 1, 5 of 6 pull requests were merged by their author, and we return to the rule |
| Nov 15 | Sprint 2 scope | #12, #13 (#26, #27, #28), #14, #16; #15 moved to Sprint 3; AI start = #19 recipe database plus #20 dish ideas (pulled from Sprint 3); matching (#17) stays in Sprint 3 | Course requires "AI feature started" in Sprint 2; Kyle asked for a recipe database (Nov 7) |
| Nov 15 | AI dish ideas | One-click suggestions from our own recipe table, no chat | Testable, cheap, can't invent recipes |
| Nov 15 | Recipe source | TheMealDB, key from `THEMEALDB_API_KEY` (test key `1` in development); ask Kyle about the supporter key for production | Its categories and cuisines fit our courses and themes |
| Nov 15 | Production | Separate Render service and Neon database; Render deploys branch `production`; the "Promote to production" workflow moves a tested `main` commit there | Deliberate, repeatable step that anyone or any agent can run (CD) |
| Nov 15 | Sprint 2 owners | Nicola: #12, #26, #27, report. Jason: promote workflow, #14, #28, promotion and checks, `technical.md`. Hanna: production setup, #19, #20, submission. Nicola also assigns the issues and updates the board. Reviews: Jason reviews Nicola's work and the report, Hanna reviews Jason's (including `technical.md`), Nicola reviews Hanna's | Split on Nov 15 for even load and few hand-offs |
| Nov 15 | OpenRouter credits | Hanna gets credits and a key from the Yale SOM Token Fund (fund.som.chat, Yale login) and stores the key only in Render | Course requires OpenRouter; no key passes between people |
| Nov 15 | Incomplete teams | A team holds its spot from sign-up, before the partner accepts | Partners usually agree to go together first |
| Nov 15 | Check-in | Monday after class, 10 minutes (replaces "Tuesday, TODO time") | Catch blockers before the Tuesday target |
| Nov 16 | AI model | `google/gemini-2.5-flash-lite` via `OPENROUTER_MODEL`, changeable without code | Cheap, fast enough for the 20-second timeout, reliable JSON; key spending stops at $20 of the team's $60 grant |
| Nov 16 | Diet tags | `vegetarian`/`vegan` also derived from ingredients (no meat/fish keywords; vegan also no dairy, egg or honey), not only from TheMealDB's category; existing recipes re-tagged by a data migration (changes contract 5.4) | Category-only tags were mains only, so one vegetarian team left starter and dessert hosts with no ideas (Nicola's review of #49) |
| Nov 16 | AI time limit | Each OpenRouter call waits at most 20 s, both attempts together at most 25 s; the retry only runs if 5 s are left (changes contract 5.5) | Render's gunicorn kills a request after 30 s, before the fallback could show (Nicola's review of #49) |

## What Kyle has told us

- **Nov 7, approval email:** approved the running dinner idea. Asked for a recipe database, sharing a dinner, friends, calendar export and proper authentication. All five are in the backlog.
- **Nov 9, lecture:**
  - Our AI agents can set up the GitHub Project and its issues through GitHub's API.
  - Build login and roles from the start; auth should never be added later.
  - He will add detail to the sprint report format: project status, this week's work, stories closed and a burn-up or burndown chart. Check the project page before each submission.
  - Render and Neon remain his recommended hosting.
