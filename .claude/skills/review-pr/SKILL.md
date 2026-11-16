---
name: review-pr
description: Review a teammate's pull request for a given issue with an independent verifier, then approve and merge it or request changes, only on my word.
argument-hint: [issue number, e.g. 19]
disable-model-invocation: true
---

Review the open pull request in `hannaroth/project-southern-glitter` that closes issue #$ARGUMENTS. I am the reviewer named in that issue. If `gh pr` commands fail (cloud sessions block GitHub's GraphQL API), use the REST API: `gh api repos/hannaroth/project-southern-glitter/...`.

1. Find the open pull request whose body contains "Closes #$ARGUMENTS". If there is none, tell me and stop. If its author is me (`gh api user --jq .login`), stop: nobody reviews or merges their own pull request.
2. Delegate to a fresh `verifier` subagent: the pull request's branch, issue #$ARGUMENTS, and the contract section named in the issue. If the change calls an outside service (an LLM, a recipe API), also have it confirm that:
   - the tests mock that service
   - it is called only from the server
   - a missing key falls back gracefully
   - no key or token is in the diff
3. Show me a verdict of at most 5 lines: blockers with file:line, or "no blockers", plus the pull request's CI status.
4. Wait for one word from me:
   - "approve": post an APPROVE review ("Reviewed with Claude Code: tests re-run locally on Postgres and checked against the sprint plan's contract", plus any nice-to-haves as bullets). Merge through the GitHub API only if the required `tests` check is green, then re-fetch the pull request to confirm it is merged.
   - "changes": post a REQUEST_CHANGES review listing the blockers.

Never approve or merge without my word.
