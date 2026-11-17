# Technical challenge and testing strategy

Team southern-glitter, running-dinner app. Repo: `hannaroth/project-southern-glitter`. Staging: <https://running-dinner-staging.onrender.com>. Production: <https://yale-running-dinner.onrender.com>.

This file is updated every sprint. Each item says what it is, where the code lives, the pull requests, how to see it working, and how it handles failure.

| # | Item | Course category | Status (Sprint 2) |
|---|---|---|---|
| 1 | CI: tests and linting on every pull request, merge blocked on failure | Delivery | Done |
| 2 | CD: `main` deploys staging automatically; a deliberate step promotes to production | Delivery | Done (workflow merged, PR #55) |
| 3 | Importing external data: recipes from TheMealDB | Backend | Done |
| 4 | Structured LLM output that drives app behavior: AI dish ideas | AI | Done (PR #49, merged) |

## 1. CI: tests and linting on every pull request, merge blocked on failure

**What it is.** Every pull request into `main`, and every push to `main`, runs the **tests** workflow on GitHub Actions against a throwaway PostgreSQL 16 database:

1. `ruff check .`, the linter, with a small bug-finding rule set: syntax errors, undefined names, unused imports and variables;
2. `python manage.py makemigrations --check`, which fails if a model change has no migration;
3. `collectstatic`, the same step Render runs, because the admin pages need its output;
4. the whole Django test suite.

A repository ruleset, "Protect main: tests must pass", makes the **tests** check required: GitHub greys out the merge button until it is green. The same ruleset blocks force-pushes to and deletion of `main`.

**Files.** `.github/workflows/tests.yml`, `ruff.toml`. Commands are in `README.md` and `AGENTS.md`.

**Pull requests.** #39 (issue #9), merged Nov 11.

**How to see it working.** Open any pull request, for example #44, and look at the **tests** check at the bottom, or open the **Actions** tab. On a pull request whose check is red, the merge button is disabled.

**Failure handling.** Any failing step fails the check and blocks the merge. A `concurrency` group cancels an outdated run when new commits are pushed to the same branch. A 15-minute timeout stops hung runs.

## 2. CD: staging deploys automatically, production by deliberate promotion

**What it is.** Two Render web services, each with its own Neon Postgres database:

| Environment | Render deploys | When |
|---|---|---|
| Staging | branch `main` | automatically, on every merge |
| Production | branch `production` | only when someone runs **Promote to production** |

**Promote to production** is a manual GitHub Actions workflow. Anyone with write access to the repo can run it from the Actions tab or with `gh workflow run promote.yml`, without access to Render. It promotes the latest `main`, or a chosen commit, only if:

- the commit is on `main`, and
- the **tests** check passed on *that exact* commit.

It then fast-forwards `production` to it, never with a force-push. Render notices the new commit and deploys it. Both environments run the same build script on every deploy (`build.sh`: install, `collectstatic`, `migrate`, recipe import if empty, `seed`), so schema changes and grader accounts reach production through the same tested path.

**Files.** `.github/workflows/promote.yml`, `scripts/promote.sh` (the git checks and the push), `build.sh`, and the README section "Deploying to production".

**Pull requests.** #55 (issue #16), merged Nov 16. The Render services, Neon databases and environment variables are dashboard work with no pull request (#16).

**How to see it working.**
- Merge any pull request: within minutes staging shows the change.
- Production: Actions → **Promote to production** → **Run workflow**. The run's summary page names the commit promoted and what was live before. Then open <https://yale-running-dinner.onrender.com> and check `/`, both grader logins and `/c6a680e/stats`.

**Failure handling.** The workflow refuses, with a message saying why, when:
- the commit is not on `main`;
- its tests failed, are still running, or never ran;
- it is older than what is live (no going backwards);
- `production` has commits that `main` lacks.

A concurrency group stops two promotions from running at once. The fast-forward rules were tested in seven cases against a throwaway git repository before merging (listed in PR #55), because a manual workflow cannot be run from a pull request branch.

## 3. Importing external data: recipes from TheMealDB

**What it is.** `python manage.py import_recipes` fills our own `Recipe` table from [TheMealDB](https://www.themealdb.com/api.php):
1. it lists the categories, then each category's meals, then looks up each meal;
2. it stores the title, cuisine, category, ingredients, instructions, source link and image;
3. it derives a course (starter, main or dessert) from the category, and best-effort diet tags (vegetarian, vegan, contains gluten, dairy or nuts) from the ingredient names.

Rows are matched by TheMealDB's id, so running the import twice updates rather than duplicates. The app then reads recipes from our database, never from TheMealDB at request time. Every page that shows recipes tells people to check ingredients themselves for allergies.

**Files.** `recipes/models.py`, `recipes/management/commands/import_recipes.py`, `recipes/diet.py` (course mapping and diet keywords), `recipes/admin.py`. `build.sh` runs `import_recipes --if-empty` after `migrate`, so each environment fills itself on its first deploy (Render's free plan has no shell). The API key comes from `THEMEALDB_API_KEY`, defaulting to the free test key `1`.

**Pull requests.** #47 (issue #19), merged Nov 16.

**How to see it working.** On staging, log in as the admin grader account and open `/admin/recipes/recipe/`: the list is filled (781 recipes on staging as of Nov 16), with course and diet tags.

**Failure handling.**
- Each request has a 10-second timeout and a short pause between requests.
- A failed category or meal is logged and skipped, and the import carries on.
- If TheMealDB is down, the command logs an error and exits without crashing.
- `build.sh` also ignores a failed import, so a TheMealDB outage can never block a deploy.

## 4. Structured LLM output that drives app behavior: AI dish ideas (started)

**What it is.** A host team clicks "Suggest dishes" and gets three dishes for its course, each with a one-line reason, plus a shared shopping list. There is no chat, by design:
1. **Our code picks the candidates:** up to 20 recipes from our own table for that course, removing any that conflict with the dinner's dietary restrictions and any already shown.
2. **The LLM only chooses among them**, through OpenRouter, called from the server only. It must reply in a fixed JSON shape: exactly three distinct recipe ids from the candidates, a reason for each, and a shopping list.
3. **The app validates that reply before using it.** It cannot invent a recipe or ignore a restriction, because anything outside the candidate list is rejected.
4. **Privacy:** the prompt contains only the theme, course, restriction keys, an optional short wish, and the candidates. No names, emails or addresses are ever sent.

**Files.** `recipes/openrouter.py` (the HTTP call, 20-second timeout, key from `OPENROUTER_API_KEY`), `recipes/ai.py` (candidates, prompt, validation, fallback), `recipes/views.py`, `recipes/urls.py`, `templates/recipes/dish_ideas.html`, and the tests `recipes/tests/test_ai.py`, `recipes/tests/test_openrouter.py` and `recipes/tests/test_dish_ideas_page.py`.

**Pull requests.** #49 (issue #20), merged Nov 17.

**How to see it working.** Once merged: log in, sign up a team for a dinner, open your team page, click **Get dish ideas** (`/dinners/<pk>/dish-ideas/`), then **Suggest dishes**. The page needs login and team membership; anyone else gets 403.

**Failure handling.** An invalid reply (bad JSON, wrong count, an id outside the candidates) is retried once. Each call has a 20-second timeout, and both attempts together are capped at 25 seconds, so a slow AI can't hit the server's 30-second limit. After that, and whenever the key is missing or OpenRouter errors or times out, the page shows three matching recipes chosen by our code, labelled "AI unavailable, here are matching recipes". The page always works.

**Next steps (Sprints 3 and 4).**
- Use the restrictions of the actual guests after matching.
- Add per-user AI usage limits.
- Add an evaluation set of fixed cases run like tests, checking the AI's choices respect restrictions.

## Testing strategy

**Where tests run.** On a real PostgreSQL database, both locally and in CI. We don't use SQLite for tests, so queries and constraints behave as in production. Every pull request needs green CI, and the reviewer re-runs the suite and clicks through the change before merging (`docs/sprint-2-plan.md`, section 6).

**What we test, at which level.**

| Level | Examples | Tools |
|---|---|---|
| Business rules as plain functions | waitlist status and position (`teams/tests/test_waitlist.py`); who may accept an invite (`teams/tests/test_invite.py`); sign-ups open or closed (`teams/tests/test_signup.py`); course mapping and diet tags (`recipes/tests/test_diet.py`); choosing and validating AI dish ideas (`recipes/tests/test_ai.py`); the A/B "preferred" calculation | Django `TestCase` |
| Models and migrations | `Dinner` validation: course times in order, deadline before the dinner (`dinners/tests/test_dinner_fields.py`); the `Team` model (`teams/tests/test_models.py`); every model change has a migration (CI) | `TestCase`, `makemigrations --check` |
| Pages and permissions | login redirects with `?next=` (`accounts/tests`, `dinners/tests/test_detail.py`); who can open the admin; who can see a team's address and one team per person per dinner (`teams/tests/test_signup.py`); CSRF and allowed methods on the invite accept (`teams/tests/test_invite.py`); the dish-ideas page's permissions (`recipes/tests/test_dish_ideas_page.py`); A/B impressions and clicks counted once per visitor, and the A/B click still counted with CSRF enforced (`abtest/tests`) | Django test client |
| Management commands | `seed` creates the grader accounts and is safe to run twice; `import_recipes` with fake HTTP responses, including failures | `call_command` |
| By hand, before each review | a click-through in a real browser, sometimes at phone size; for the A/B page, a scripted run of 200 fresh visitors against gunicorn and Postgres, described in PR #35 | browser |

**What we mock, and why.**
- **TheMealDB:** `urllib.request.urlopen` is patched with canned responses, including network errors, empty results and bad JSON; the tests also check the 10-second timeout is passed, and set the pause between requests to 0.
- **OpenRouter:** `chat_json` is patched to return valid, invalid and failing replies, so tests cover the retry and the fallback, and check that no personal data is in the prompt.
- **Randomness:** the A/B 50/50 choice (`random.choice`), so tests are repeatable.
- **Time:** tests on `main` build dates relative to today, so they never go stale; #48's tests also patch `timezone.now` to test the exact deadline moment.

No test calls a real outside service: tests must run with no keys and no network, they must not cost money, and a slow or changing outside service shouldn't make CI fail.

**What we don't test, and why.**
- **The real outside services**, beyond our side of the contract: we test how we call them and handle every kind of failure, not whether TheMealDB or OpenRouter are up.
- **How good the AI's suggestions are:** tests check the reply's shape and that it stays within the candidates. Judging quality needs an evaluation set, planned for Sprint 3 or 4.
- **Render and Neon configuration:** checked by deploying (staging on every merge, production on every promotion) and by the post-deploy checks in the README section "Deploying to production". The promotion script's git rules were tested against a throwaway repository instead.
- **Visual design and the copy-link buttons' JavaScript:** checked by hand in a browser. End-to-end browser tests (Playwright) in CI are a possible later item.
- **Django's own login and admin code:** we test our use of them (redirects, who reaches the admin), not the framework itself.
