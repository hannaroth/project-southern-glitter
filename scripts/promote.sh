#!/usr/bin/env bash
# Move a tested commit from main to the production branch (fast-forward only).
# Render deploys the production branch automatically.
#
# Usage: scripts/promote.sh <commit>
# Run by .github/workflows/promote.yml; it can also be run by hand from a clone with push access.
# The workflow checks that the "tests" check passed on the commit before calling this script.
set -euo pipefail

REMOTE="${PROMOTE_REMOTE:-origin}"
SHA_INPUT="${1:?usage: scripts/promote.sh <commit>}"

fail() { echo "::error::$*" >&2; exit 1; }

git fetch --quiet "$REMOTE" main
SHA="$(git rev-parse --verify --quiet "${SHA_INPUT}^{commit}")" || fail "Unknown commit: $SHA_INPUT"

# 1. Only commits that are on main can go to production.
git merge-base --is-ancestor "$SHA" "$REMOTE/main" || fail "$SHA is not on main. Only commits on main can be promoted."

# 2. Fast-forward only: production must not have commits that this commit lacks.
if git ls-remote --exit-code --heads "$REMOTE" production >/dev/null; then
  git fetch --quiet "$REMOTE" production
  CURRENT="$(git rev-parse "$REMOTE/production")"
  if [ "$CURRENT" = "$SHA" ]; then
    echo "production is already at $SHA; nothing to do."
    exit 0
  fi
  git merge-base --is-ancestor "$CURRENT" "$SHA" \
    || fail "production ($CURRENT) has commits that $SHA does not contain. Promote a newer commit from main, or fix production by hand."
else
  CURRENT=""
  echo "production branch does not exist yet; creating it."
fi

# 3. Push without --force: git refuses anything that isn't a fast-forward.
git push "$REMOTE" "$SHA:refs/heads/production"
echo "Promoted $SHA to production (was ${CURRENT:-none})."
