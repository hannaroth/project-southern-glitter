---
name: sprint-report
description: Write the sprint report docs/mgt656/sprints/sprint-N.md from GitHub data and open its pull request.
argument-hint: [sprint number, then optionally each person's agent lesson, e.g. 2 "Jason: ..."]
disable-model-invocation: true
model: haiku
---

Write the Sprint $0 report for `hannaroth/project-southern-glitter`. Work on your own. If `gh` commands fail (cloud sessions block GitHub's GraphQL API), use the REST API: `gh api repos/hannaroth/project-southern-glitter/...`. Anything I typed after the sprint number is input for the report, such as agent lessons: $ARGUMENTS

1. **Read:** `AGENTS.md`, `docs/sprint-$0-plan.md` (its sprint goal and its report section), the previous report in `docs/mgt656/sprints/`, and the sprint's report issue (its title contains "Sprint $0 report").
2. **Housekeeping first:** close any parent story whose sub-issues are all closed with merged pull requests, with a one-line comment saying so.
3. **Write** `docs/mgt656/sprints/sprint-$0.md`, about half a page, in the same structure as the previous report:
   - the goal and a one-line status
   - what shipped, with links to this sprint's closed issues and merged pull requests
   - what works on staging and production (URLs from `README.md`)
   - one agent lesson per person: use the ones I gave you; for anyone missing, draft one from their pull request descriptions, mark it "(draft, please confirm)" and tell me
   - backlog changes for the next sprint
   - no burndown chart and no story points
4. **Pull request:**
   - branch `<report issue number>-sprint-$0-report` from the latest `main`
   - push, then open a pull request into `main` with "Refs #<report issue>" on the first line (not "Closes": the course submission still has to happen)
   - fill in the "What the AI produced / what we changed or rejected" section honestly
   - request review from the reviewer named in the report issue
   - re-fetch it to confirm it exists; never merge

Give me the link and the list of draft lessons.
