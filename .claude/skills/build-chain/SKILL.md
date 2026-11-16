---
name: build-chain
description: Build one or more GitHub issues in order (each on top of the previous one when needed), verify each independently and open its pull request.
argument-hint: "[issue numbers in order, e.g. 12 26 27]"
disable-model-invocation: true
---

Build these issues of `hannaroth/project-southern-glitter`, in this order: $ARGUMENTS

You are the coordinator. Delegate the building and the checking to subagents and keep your own context small: plan, delegate, read their summaries, open the pull requests, report. Work on your own and come back to me only at the end, unless something is truly blocked or a decision isn't covered by `AGENTS.md`, the issue or the sprint plan.

**Setup, once.** Read `AGENTS.md`, the newest `docs/sprint-*-plan.md`, and every listed issue together with its parent issue. Make sure a local Postgres and a Python virtualenv work (ask me before installing system packages). If `gh issue view` or `gh pr create` fails (cloud sessions block GitHub's GraphQL API), use the REST API instead: `gh api repos/hannaroth/project-southern-glitter/...`.

**For each issue N, in the order given:**
1. Branch `N-<short-name>`. Start from the latest `main` if N is first or the previous issue in this list is already merged; otherwise start on top of the previous issue's branch.
2. Delegate to the `issue-builder` subagent: the issue number, the branch, its starting point, and the contract section named in the issue.
3. Delegate to a fresh `verifier` subagent: the branch and the issue. If it finds blockers, send them to a new `issue-builder` run that fixes them on the same branch, then check again with a fresh `verifier`. At most 3 rounds; after that, stop and ask me.
4. Push the branch. If another open issue says it builds on this branch (for example "Builds on #N's branch"), comment on that issue with the branch name as soon as the shared part (models and migrations) passes its tests, even before the rest is finished, so its owner doesn't have to wait.
5. Open the pull request into `main`:
   - title: the issue title
   - body: `Closes #N` on the first line, then a short summary, how to test it, "Builds on #X" if it started on another branch, and the section "What the AI produced / what we changed or rejected", filled in honestly (what the builder made, what the verifier caught and what was fixed, anything left out on purpose)
   - review requested from the person in the issue's "Reviewer (approves and merges)" line
   Then re-fetch the pull request from GitHub to confirm it exists. Never merge.

**At the end, give me only:** one line per pull request (link, tests passed, verifier rounds), anything I must decide, and one short WhatsApp line for the team.
