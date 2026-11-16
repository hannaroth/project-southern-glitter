# Sprint 2: sign-up, production and a first AI feature

**Sprint goal:** students can sign up for a dinner as a team of two on production, and hosts get their first AI dish ideas from a real recipe database.

**Status:** <!-- TODO Tue: one line, e.g. "Done: all committed stories are merged and live on staging and production." -->

## What shipped

<!-- TODO Tue: keep only what is merged, and fill in the missing pull request numbers. -->
- Admins create and edit dinners: #12, PR #44
- Sign up for a dinner as a team of two: #13, made of the sign-up form #26 (PR #48), the partner invite link #27 (PR #50) and the waitlist #28 (PR #…)
- Share a dinner: #14, PR #…
- Production environment: #16. A separate Render service and Neon database (set up directly on Render; no pull request), and a "Promote to production" workflow that moves a tested `main` commit to production (PR #…)
- Recipe database imported from TheMealDB: #19, PR #47
- AI dish ideas, first slice: #20, PR #49
- Also: the Sprint 2 plan and decisions (PR #41), Claude Code subagents and team commands (PR #45), and the first version of `technical.md` (#43, PR #…)

## What works on staging and production now

Staging: https://running-dinner-staging.onrender.com
Production: <!-- TODO: production URL -->

<!-- TODO Tue: keep only what the check of both sites confirmed. -->
- Admins create and edit dinners in the admin area, with course times, the after-party and a sign-up deadline.
- Students sign up a team for a dinner with their address, dietary restrictions and preferred course. Each person can be on one team per dinner, and sign-ups close at the deadline.
- The team's creator shares an invite link; the team is complete when the partner accepts while logged in.
- Once the team cap is reached, new teams join a waitlist in sign-up order.
- Each dinner has a shareable page; logged-out visitors are asked to log in to join.
- Signed-up teams get three dish ideas from our recipe database, each with a reason, plus a shopping list.
- The Sprint 1 A/B test page and stats still work.

## Working with our agents

<!-- One concrete thing per person: what worked or didn't, and what you changed. -->
- **Nicola:** Running Claude Code locally needed a one-time 15-minute setup (Homebrew, gh, Python 3.13, Postgres 16). After that, an Opus coordinator with a Sonnet builder and an independent verifier subagent shipped #26 with 142 green tests in about 7 minutes. Lesson: give the agent the environment details up front, and always have a second agent verify.
- **Jason:** <!-- TODO: Jason's lesson -->
- **Hanna:** <!-- TODO: Hanna's lesson -->

## Backlog changes for Sprint 3

- We pulled the recipe database (#19) and the first slice of AI dish ideas (#20) forward from Sprint 3, because the course asked for the AI feature to start in Sprint 2 and Kyle had asked for a recipe database.
- Dish ideas are one-click suggestions from our own recipes, not a chat, so they can't invent recipes and are easy to test.
- Cancelling before the matching (#15) moved to Sprint 3, to keep the last day for production and documentation.
- We added a look-and-feel story (#52) after our smoke test: everything worked, but the design was very minimal. It goes at the start of Sprint 3, once Sprint 2's pull requests are merged, so it doesn't conflict with them.
- Planned for Sprint 3: matching teams when sign-ups close (#17, with #29–#34), the My Dinner page with the timed address reveal (#18), dish ideas for the actual guests once matching exists, and the design pass (#52).
