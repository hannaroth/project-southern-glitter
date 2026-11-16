# Sprint 2 plan: team southern-glitter

Written Sun Nov 15, 2026 (Nicola). Covers Sprint 2: Thu Nov 12 to Wed Nov 18. Read this together with `AGENTS.md`, `docs/backlog.md` and `docs/decisions.md`.

**For AI agents:** `AGENTS.md` still governs how you work (one issue at a time, branch per issue, tests, no secrets, never push to `main`, never merge). This file adds the Sprint 2 specifics: who owns what, in which order, and the **shared contracts in section 5**, which let three people build in parallel without collisions. Build only the issues your human owns. Do not change a contract on your own; if one looks wrong, stop and ask your human, who raises it in the group.

---

## 1. What Sprint 2 is graded on

From the course site (Project: Sprint 2, 15 points) and the [requirements repo](https://github.com/yale-mgt-656-fall-2026/project-requirements):

- **Production** is deployed, with its own database.
- **First user stories are shipped** through pull requests.
- **The AI feature is started.**
- `docs/mgt656/sprints/sprint-2.md` is on `main`.
- Graded on what shipped, the report, and **how we worked**: a teammate reviews every pull request before it merges, every pull request says `Closes #<issue>`, and every pull request description says what the agent produced and what we changed or rejected.
- Submission fields: repo URL, staging URL, **production URL** (new) and "Grader access and notes" (login page plus one username and password per kind of user, and a note about anything half done).
- No story points, velocity or burndown charts.

**Course deadline:** Wed Nov 18, 11:59pm ET. **Team target:** submitted **Tue Nov 17 by 8pm ET**. Wednesday is buffer for fixes only.

## 2. Sprint goal

> Students can sign up for a dinner as a team of two on production, and hosts get their first AI dish ideas from a real recipe database.

## 3. Scope, owners, reviewers

**Rule (decided Nov 15):** the reviewer re-runs the tests, smoke-tests the change, approves it and **merges it right away** once CI is green. The author never merges their own pull request (`AGENTS.md` step 8). This matches the Nov 9 decision; in Sprint 1, 5 of 6 pull requests were merged by their author, and Sprint 2 returns to the rule. Reviewers aim to review within 2 hours on Monday daytime.

Reviewer rotation: **Jason reviews Nicola's work, Hanna reviews Jason's, Nicola reviews Hanna's**, with one swap to even out the load: Jason reviews the report.

| # | Item | Owner | Reviewer (merges) | Needs first | Merged by |
|---|---|---|---|---|---|
| — | This plan and new `docs/decisions.md` lines (pull request) | Nicola | Hanna | — | Sun night |
| 12 | Admins create and edit dinners | Nicola | Jason | — | **Mon 11am** (unblocks the rest) |
| 26 | Sign-up form (part of #13) | Nicola | Jason | #12 (build on top of #12's branch) | Mon 4pm |
| 27 | Partner invite link (part of #13) | Nicola | Jason | #26 | Mon 10pm |
| 16 | Production: Render service, Neon database, environment variables | Hanna | — (dashboard work, no pull request) | — | Mon 12pm |
| 16 | Production: "Promote to production" workflow | Jason | Hanna | — | Mon 12pm |
| 14 | Share a dinner (detail page) | Jason | Hanna | #12 merged | Mon 5pm |
| 28 | Waitlist (part of #13) | Jason | Hanna | #26 | Mon 10pm |
| 19 | Recipe database (pulled forward from Sprint 3) | Hanna | Nicola | — | Mon 4pm |
| 20 | AI dish ideas, first slice (pulled forward from Sprint 3) | Hanna | Nicola | #19; its page needs #26 | Mon 11pm |
| — | `docs/mgt656/technical.md` first version (**vital: how Kyle grades our 20-point technical challenge**, new task issue) | Jason | Hanna | promote workflow | Tue 3pm |
| — | `docs/mgt656/sprints/sprint-2.md` report and the submission (new task issue "Sprint 2 report and submission") | Nicola (report), Hanna (submission) | Jason | everything else | Tue 5pm |
| — | Run "Promote to production", then check staging and production | Jason | — | everything merged | Tue 2pm |

**Moved out:** #15 Cancel before the matching goes to **Sprint 3** (decided Nov 15). It sits at the end of the sign-up chain and would crowd Tuesday, which now belongs to production and `technical.md`.

Non-code to-dos are in section 7. #13 (parent story) is closed by Nicola once #26, #27 and #28 are merged.

## 4. Timeline (all times ET)

```
            Sun night      Mon 9am-1pm         Mon 1:00-2:20   Mon 2:30-11pm           Tue 9am-5pm                   Tue 8pm
Nicola  | plan PR,     | #12 -> #26          | class        | #26 -> #27            | report sprint-2.md          |
        | issues, board| (ask Kyle in class: TheMealDB key)                                                          |
Jason   | read plan    | promote workflow,   | class        | #14 -> #28            | PROMOTE, check staging+prod,|
        |              | review #12, #14     |              | (on top of #26)       | technical.md (20 points!),  |
        |              |                     |              |                       | review report               |
Hanna   | read plan    | prod Render+Neon,   | class        | #19 -> #20            | review technical.md,        | SUBMIT
        |              | #19                 |              |                       | grader notes, submission    |
                                             ^ 10-min check-in at end of class
```

- **Sun night:** Nicola opens the plan pull request. Nicola runs the issue script and updates the board (section 7). Everyone reads the plan. Anyone may start their agent on a first item that needs nothing else (#12, the promote workflow, #19).
- **Mon morning:** everyone starts on items that need nothing else. #12 goes first because #26 and #14 need its fields; Jason reviews and merges it as soon as it's up.
- **Mon end of class, 10-minute check-in (the only meeting):** see section 10.
- **Mon afternoon and evening:** the sign-up chain (#26 → #27 and #28) and the AI track (#19 → #20). Goal: everything merged by Mon 11pm.
- **Tue:** promote to production, check staging and production, report, `technical.md`, submission.

**No waiting rule:** if you are blocked, take your next item that needs nothing else, or build on top of the branch you need (as we did in Sprint 1) and say so in the pull request body ("Builds on #26; ignore its files in the diff"). Keep the pull request base on `main`, so CI runs. After the parent merges, update your branch with `git merge origin/main` (no force-push).

## 5. Shared contracts (binding for all branches)

These keep parallel branches compatible. Field names, URL names and app names below are fixed.

### 5.1 Dinner (owned by #12, app `dinners`)

Current model: `title`, `theme`, `date`, `after_party_place`, `team_cap`.

#12 changes it to:

| Field | Type | Notes |
|---|---|---|
| `title` | CharField(200) | unchanged |
| `theme` | CharField(200) | unchanged |
| `date` | DateField | unchanged |
| `starter_time` | TimeField | migration default 18:00 |
| `main_time` | TimeField | migration default 19:30 |
| `dessert_time` | TimeField | migration default 21:00 |
| `after_party_name` | CharField(200) | **rename** of `after_party_place` (RenameField, keeps data) |
| `after_party_address` | CharField(255) | migration default `""`; required in the admin form |
| `team_cap` | PositiveIntegerField | unchanged |
| `signup_deadline` | DateTimeField | migration fills existing rows with the dinner date minus 2 days, 23:59 America/New_York |

- Admin (`dinners/admin.py`): all fields editable, grouped (Basics / Course times / After-party / Sign-ups). Only `is_staff` users reach the admin (already true). Validation: course times in order (starter < main < dessert); `signup_deadline` before the dinner date.
- Update `dinners/management/commands/seed.py` (stays idempotent) and `templates/home.html` (`after_party_place` → `after_party_name`).
- #12 is the only Sprint 2 change to the `dinners` migrations. Nobody else adds a `dinners` migration this sprint.
- Tests: admin can create and edit; a participant is refused; the validation rules; the seed is still idempotent.

### 5.2 URLs and templates

| URL | Name | Owner |
|---|---|---|
| `/dinners/<int:pk>/` | `dinners:detail` | #14 (creates `dinners/urls.py` with `app_name = "dinners"`, included from `config/urls.py`) |
| `/dinners/<int:pk>/signup/` | `teams:signup` | #26 |
| `/teams/<int:pk>/` | `teams:detail` ("our team" page: status, partner, invite link, waitlist position) | #26 creates; #27 and #28 add to it (#15 adds cancel in Sprint 3) |
| `/teams/join/<str:token>/` | `teams:accept` | #27 |
| `/teams/<int:pk>/cancel/` (POST only) | `teams:cancel` | #15, **Sprint 3** (reserved name, not built now) |
| `/dinners/<int:pk>/dish-ideas/` | `recipes:dish_ideas` | #20 |

- The home page links each dinner title to `dinners:detail` (#14).
- The **join button** on the detail page: #14 shows "Log in to join" to logged-out visitors (link to `/login/?next=/dinners/<pk>/`) and leaves a `{% block join %}` for logged-in users. Whichever of #14 and #26 merges second wires the "Sign up as a team" button to `teams:signup`. Logged-in users who already have a team see "Your team" linking to `teams:detail`.
- Templates stay server-rendered with Pico CSS and work on phones. A little JavaScript is fine for the copy-link button only (`navigator.clipboard`, with the URL also shown as text).

### 5.3 Team (owned by #26, new app `teams`)

**#26 creates the full model below, including the fields #27, #28 and later #15 (Sprint 3) use, so those add no migrations.**

```python
DIET_CHOICES = [
    ("vegetarian", "Vegetarian"), ("vegan", "Vegan"), ("gluten_free", "Gluten-free"),
    ("dairy_free", "Dairy-free"), ("nut_allergy", "Nut allergy"),
]

class Team(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered"   # holds one of the dinner's team_cap spots
        WAITLISTED = "waitlisted"
        CANCELLED = "cancelled"

    class Course(models.TextChoices):
        STARTER = "starter"; MAIN = "main"; DESSERT = "dessert"; NO_PREFERENCE = "no_preference"

    dinner = models.ForeignKey("dinners.Dinner", on_delete=models.CASCADE, related_name="teams")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_teams")
    partner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="partner_teams")
    address = models.CharField(max_length=255)
    dietary_restrictions = models.JSONField(default=list, blank=True)   # keys from DIET_CHOICES
    dietary_notes = models.CharField(max_length=255, blank=True)        # free text
    preferred_course = models.CharField(max_length=20, choices=Course.choices, default=Course.NO_PREFERENCE)
    invite_token = models.CharField(max_length=64, unique=True, default=new_invite_token)  # secrets.token_urlsafe(32)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]   # sign-up order
```

Business rules, with their owners (put helpers in `teams/services.py`):

- **Sign-ups open** while `timezone.now() < dinner.signup_deadline`; after that the form, the invite accept and cancel all refuse with a clear message (#26 adds `signups_open(dinner)`; #27 reuses it, and #15 will in Sprint 3).
- **One team per person per dinner:** a user may be `creator` or `partner` of at most one non-cancelled team per dinner. #26 checks this on sign-up; #27 checks it on accept (you can't accept an invite to a second team for the same dinner, or your own invite).
- **Team complete** = `partner` is set. An incomplete team **still holds its spot** in sign-up order (decided Nov 15: partners usually agree to go together before signing up).
- **Waitlist (#28):** `assign_status(team)` is called when a team is created: `REGISTERED` if fewer than `dinner.team_cap` non-cancelled `REGISTERED` teams exist, otherwise `WAITLISTED`. The team page shows the waitlist position (1-based, in sign-up order). Until #28 merges, #26 creates every team as `REGISTERED`.
- **Cancel (#15, Sprint 3, not built now; written down so the model fits):** either partner can cancel (POST, with a confirm step) until the sign-up deadline; this sets `status=CANCELLED` and `cancelled_at`, and if the cancelled team was `REGISTERED`, `promote_waitlist(dinner)` moves the earliest `WAITLISTED` team to `REGISTERED`. Wrap it in a transaction with `select_for_update` on the dinner's teams.
- **Privacy:** a team's address is visible only to its two members and admins. Address reveal to guests is Sprint 3 (#18).
- Register `Team` in the Django admin (list: dinner, creator, partner, status, created_at).

### 5.4 Recipe (owned by #19, new app `recipes`)

#19 is the **data**: real recipes imported into our own database, with no AI. #20 (5.5) is the **AI feature** built on top of it: it picks dishes from those recipes for a host.

Source: **[TheMealDB](https://www.themealdb.com/api.php)**. Its free test key `1` is meant for development and education; its docs say a publicly shipped app should get a supporter key (one-time small fee). Nicola asks Kyle on Monday (section 9). The key is read from the environment, so switching keys needs no code change. Fallback source if needed: the Wikibooks Cookbook dataset (CC BY-SA 4.0). We don't scrape sites.

```python
class Recipe(models.Model):
    source = models.CharField(max_length=30, default="themealdb")
    external_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    cuisine = models.CharField(max_length=100, blank=True)     # TheMealDB "strArea", e.g. "Italian"
    category = models.CharField(max_length=100, blank=True)    # TheMealDB "strCategory", e.g. "Dessert"
    course = models.CharField(max_length=20)                   # "starter" | "main" | "dessert" (derived)
    ingredients = models.JSONField(default=list)               # [{"name": "...", "measure": "..."}]
    instructions = models.TextField()
    source_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    diet_tags = models.JSONField(default=list)                 # derived, see below
    imported_at = models.DateTimeField(auto_now=True)
```

- **Course mapping:** category `Starter` or `Side` → `starter`; `Dessert` → `dessert`; everything else → `main`.
- **Diet tags (derived, best effort):** `vegetarian` if the category is Vegetarian or Vegan; `vegan` if Vegan; `contains_gluten`, `contains_dairy`, `contains_nuts` from keyword lists over the ingredient names (lists live in `recipes/diet.py` with tests). Every page that shows recipes says: *"Check the ingredients yourself for allergies."*
- **Import command:** `python manage.py import_recipes [--if-empty]`. It lists categories, fetches each category's meals, looks up each meal, and upserts by `external_id` (safe to run twice). The key comes from `THEMEALDB_API_KEY` (default `"1"`). It uses a 10-second timeout and a short pause between requests, and logs and skips failures instead of crashing. Uses the standard library (`urllib.request`), so no new dependency.
- Add `python manage.py import_recipes --if-empty` to `build.sh` after `migrate`, so each environment fills itself on first deploy (Render's free plan has no shell) and later deploys skip it.
- Tests mock all HTTP; no test calls TheMealDB. Add `THEMEALDB_API_KEY` to `.env.example` (name only). Show "Recipes from TheMealDB" wherever recipes appear.

### 5.5 AI dish ideas, first slice (owned by #20, app `recipes`)

**Design decision: no chat.** One click gives three dish ideas drawn from **our own recipe table**, each with a one-line reason and a shared shopping list. An optional one-line wish ("no oven", "something spicy") and a "Suggest others" button give most of a chat's flexibility, while staying testable, cheap, and unable to invent recipes.

- `recipes/openrouter.py`: `chat_json(messages, *, model=None) -> dict` POSTs to `https://openrouter.ai/api/v1/chat/completions` with the standard library, using a 20-second timeout and asking for a JSON object. It reads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from the environment (add both names to `.env.example`). It raises a clear error if the key is missing. **It is called only from the server.**
- `recipes/ai.py`: `suggest_dishes(*, course, theme, restrictions, wish="", exclude_ids=()) -> DishIdeas`:
  1. Our code picks up to 20 candidates: recipes with that `course`, excluding any whose `diet_tags` conflict with the restrictions (vegetarian/vegan need the tag; gluten-free, dairy-free and nut allergy exclude `contains_*`), and excluding `exclude_ids`.
  2. The prompt contains only the theme, course, restriction keys, the wish (trimmed to 200 characters) and the candidates (id, title, cuisine, category, ingredient names). **Never names, emails or addresses.**
  3. Expected reply: `{"suggestions": [{"recipe_id": <int>, "why": "<one sentence>"}] (exactly 3), "shopping_list": ["..."]}`.
  4. Validate: exactly 3 distinct ids, all from the candidates. On invalid JSON or a bad id, retry once, then fall back to 3 candidates chosen by our code, labelled "AI unavailable, here are matching recipes". The same fallback applies when the key is missing or OpenRouter errors or times out.
- Page `recipes:dish_ideas` (`/dinners/<pk>/dish-ideas/`): login required, and only for members of a non-cancelled team for that dinner (others get 403). It shows the team's preferred course (with a picker if "no preference"), the dinner theme, and the restrictions. Until matching exists (Sprint 3), the restrictions are the **union of all non-cancelled teams' restrictions for that dinner**. Elements: a "Suggest dishes" button (POST), the optional wish field, and "Suggest others", which excludes the ids already shown. Results show the 3 recipes with reason, cuisine, a link to the source, the shopping list and the allergy note. Link to it from `teams:detail`.
- Tests mock `chat_json`: a valid reply gives 3 ideas; invalid JSON is retried, then the fallback is used; an id outside the candidates is rejected; a missing key gives the fallback; **no personal data in the prompt** (assert the team's address and the users' emails don't appear in the messages sent); permissions on the page.
- Later (not Sprint 2): restrictions of the actual guests after matching, per-user AI usage limits, and an evaluation set.

### 5.6 Production and promotion (#16)

Goal: staging keeps deploying `main` automatically. Production deploys only when someone deliberately promotes a tested commit, and anyone (or their agent) can do it from GitHub without touching Render. This counts toward the CD tech-challenge item.

**Hanna (one-time setup in her accounts, about 45 minutes):**
- Neon: a **new database for production**, separate from staging (own project or own branch, whichever the free plan allows).
- Render: a new web service for production from the same repo, **branch `production`**, auto-deploy on, same build (`./build.sh`) and start command as staging.
- Production environment variables: `DATABASE_URL` (the production database), a **new** `SECRET_KEY`, `DEBUG=false`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SEED_ADMIN_PASSWORD` and `SEED_MEMBER_PASSWORD` (same grader values as staging, so grader notes stay simple), later `OPENROUTER_API_KEY` and `THEMEALDB_API_KEY`. Values only in Render, never in chat or git.
- Create the `production` branch from `main` once (or let the first workflow run create it).
- Put the production URL into the README and the submission.

**Jason (pull request): `.github/workflows/promote.yml`, named "Promote to production":**
- Trigger: `workflow_dispatch` with an optional input `sha` (default: current `main` HEAD).
- Checks: the commit is on `main`, and the `tests` check on that commit succeeded.
- Action: `git push origin <sha>:refs/heads/production`. Fast-forward only; it fails loudly if `production` has commits that aren't on `main`.
- Permissions: `contents: write` (plus `checks: read`). Writes a job summary saying which commit was promoted.
- README section "Deploying to production": run `gh workflow run promote.yml`, or Actions tab → "Promote to production" → Run workflow. Note that Render then deploys `production` automatically.
- If anyone later protects the `production` branch, GitHub Actions must be allowed to push to it.

## 6. Definition of done for every pull request

1. Branch `<issue>-<short-name>` from the latest `main`.
2. Tests for every acceptance criterion and contract rule. Locally, on a real Postgres: full test suite, `ruff check .` and `python manage.py makemigrations --check` all pass.
3. **The human owner independently re-runs the tests and smoke-tests in a browser** before asking for review. Never trust the agent's own "all green".
4. Pull request into `main` (if `gh pr create` fails in your agent's environment, use `gh api repos/hannaroth/project-southern-glitter/pulls`). Title = issue title. Body: `Closes #N` on the first line, then a summary, how to test it, "Builds on #X" if it does, and **"What the AI produced / what we changed or rejected"**, written by the human.
5. **Re-fetch the pull request from the GitHub API to confirm it exists before reporting it as done** (Sprint 1 lesson).
6. Request the reviewer from section 3 and post the link in the WhatsApp group.
7. The reviewer re-runs the tests, smoke-tests, approves and **merges**. If changes are needed, comment; the author fixes and re-requests.
8. After the merge, staging deploys automatically. The owner checks the feature on staging within the hour.
9. Never put passwords, keys or tokens in code, commits, issues, pull requests or chat.

## 7. To-do lists

### Nicola (magnificent-aardvark, `nicode656`)
- [ ] **Sun night:** open the pull request with this plan plus the `docs/decisions.md` lines from section 8, and in `docs/backlog.md` move "Cancel before the matching" under Sprint 3 and "Recipe database" and "AI menu helper" under Sprint 2. Hanna approves and merges it right away. Share the plan link in WhatsApp.
- [ ] **Sun night, about 2 minutes:** assign and annotate the Sprint 2 issues by running `sprint-2-issues.sh` (Nicola has it; not in the repo; `bash sprint-2-issues.sh` with the GitHub CLI logged in). It sets the assignees from section 3 and adds owner, reviewer, plan section and notes to #12, #13, #14, #16, #19, #20 and #26–#28 (#19 and #20 become "Planned for Sprint 2", #20 gets the no-chat design), and moves #15 to Sprint 3. It also creates two task issues: "Sprint 2 report and submission" and "technical.md: first version". Safe to run twice.
- [ ] **Sun night, about 5 minutes, board:** on the project board ("southern-glitter: Running Dinner", Backlog view), add the sub-issues #26, #27, #28 and the two new task issues (type `#` plus the number in the "Add item" row). Then set Iteration = Sprint 2 for #12, #13, #14, #16, #19, #20, #26, #27, #28 and the two new task issues, and Iteration = Sprint 3 for #15. You have write access to the board.
- [ ] **Mon 9 to 11am:** #12 Admins create and edit dinners (contract 5.1). Pull request to Jason by about 10am.
- [ ] **Mon 10am to 4pm:** #26 Sign-up form, building on #12's branch (contracts 5.2, 5.3). Pull request to Jason by about 2:30pm.
- [ ] **Mon in class:** ask Kyle whether TheMealDB's free key is fine or we should get the supporter key (section 9).
- [ ] **Mon 4 to 10pm:** #27 Partner invite link (contract 5.3). Pull request to Jason.
- [ ] **Mon:** review and merge Hanna's #19 and #20.
- [ ] **When #26, #27 and #28 are merged:** close parent #13.
- [ ] **Tue 9am to 5pm:** `docs/mgt656/sprints/sprint-2.md` (section 11), pull request to Jason; collect each person's agent lesson by Tue 12pm.

### Jason (delightful-crocodile, `kawaiibunny202`)
- [ ] **Sun night or Mon 9am:** read the plan (Nicola's script assigns you #14, #28, the promote part of #16 and `technical.md`).
- [ ] **Mon 9am to 12pm:** `promote.yml` workflow and README section (contract 5.6). Pull request to Hanna. Meanwhile **review and merge #12 quickly**: #26 and #14 depend on it.
- [ ] **Mon 11am to 5pm:** #14 Share a dinner (detail page and copy-link button, contract 5.2). Pull request to Hanna.
- [ ] **Mon 2:30 to 10pm:** review and merge Nicola's #26 when it's ready. #28 Waitlist, building on #26's branch (contract 5.3). Pull request to Hanna.
- [ ] **Mon evening:** review and merge Nicola's #27.
- [ ] **Tue by 11am:** run "Promote to production" (`gh workflow run promote.yml`) once everything is merged. Confirm production is up, seeded, and has recipes imported.
- [ ] **Tue right after:** check staging **and** production: both grader logins, create a dinner as admin, sign up as a team, accept the invite in a private window, waitlist with team cap 1, share link logged out, dish ideas, and `/c6a680e` plus `/c6a680e/stats`. Comment on the matching issue for anything broken.
- [ ] **Tue 9am to 3pm:** `docs/mgt656/technical.md` first version. **Vital, give it real care:** it is how Kyle finds and judges our technical challenge, which is worth **20 of the 60 project points**, and it is part of the 10-point process-and-docs grade. Contents: CI (#9, PR #39) and CD (#16), each with what it is, main files, pull requests and how to see it working; then a short testing strategy (what we test at which level, what we mock: OpenRouter and TheMealDB; what we don't test and why). Pull request to Hanna.

### Hanna (stormy-zebra, `hannaroth`)
- [ ] **Sun night:** review and merge Nicola's plan pull request.
- [ ] **Mon 9am to 12pm:** production setup (contract 5.6): Neon database, Render service on branch `production`, environment variables. Then review and merge Jason's promote workflow.
- [ ] **Mon morning, OpenRouter key:** get OpenRouter credits and a key yourself at the Yale SOM Token Fund, https://fund.som.chat (Yale login). Put the key and put it straight into Render as `OPENROUTER_API_KEY` on staging and production. Never in chat, git or WhatsApp. Tests never need it.
- [ ] **Mon 11am to 4pm:** #19 Recipe database (contract 5.4). Pull request to Nicola.
- [ ] **Mon:** review and merge Jason's #14 and #28.
- [ ] **Mon 4 to 11pm:** #20 AI dish ideas, first slice (contract 5.5), building on #19. Pull request to Nicola. Once the key is in Render, try the dish-ideas page on staging with real AI.
- [ ] **Tue by 4pm:** review and merge Jason's `technical.md`.
- [ ] **Tue afternoon:** write the grader notes (section 12) once production is checked.
- [ ] **Tue by 8pm:** submit on the course site (section 12).

## 8. Lines to add to `docs/decisions.md` (in the plan pull request)

Add new rows, without rewriting old ones:

| Date | Decision | Choice | Why |
|---|---|---|---|
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

## 9. Questions for Kyle (Nicola, Monday class)

1. TheMealDB's free key is meant for development and education; its docs ask public apps to get a supporter key. Is the free key fine for our course app, or should we get the supporter key (and would the course cover it)?

## 10. Monday check-in (10 minutes, end of class)

1. Is #12 merged? Are #26 and #19 pull requests up? Any blockers?
2. Confirm or change the contract choice: restrictions for dish ideas are the union of all teams until matching.
3. Kyle's answer on the TheMealDB key. Is the OpenRouter key in Render?
4. Does production exist yet (Render service and database)?
5. Re-split anything that is behind, so Tuesday stays light.

## 11. Sprint 2 report (`docs/mgt656/sprints/sprint-2.md`)

About half a page, same structure as Sprint 1:
- the sprint goal (section 2)
- status in one line
- what shipped, with links to closed issues and merged pull requests
- what works **on staging and production** now, with both URLs
- working with our agents: one concrete thing per person that worked or didn't, and what we changed (each person sends theirs to Nicola by Tue 12pm)
- backlog changes for Sprint 3: #19 and #20 pulled forward; #15 moved to Sprint 3; matching (#17, #29–#34), My Dinner page (#18) and the next AI steps
- no burndown chart, no story points; screenshots in `docs/mgt656/sprints/img/` are optional

## 12. Submission and grader notes (Hanna, Tue by 8pm)

The course form for Sprint 2 has four fields: repo URL, staging URL, **production URL** and **"Grader access and notes"**. The last one tells the graders how to get into the app. It is visible to the team and course staff, is never stored in git, and takes about 5 minutes. Hanna writes it because the grader passwords live only in her Render environment variables (`SEED_ADMIN_PASSWORD`, `SEED_MEMBER_PASSWORD`).

- Repo: `https://github.com/hannaroth/project-southern-glitter`
- Staging: `https://running-dinner-staging.onrender.com`
- Production: the new Render URL
- Grader access and notes, in the course's format (fake accounts created by the seed command; real passwords typed only into the form):

```
Access:
<production URL>/login/   (staging: https://running-dinner-staging.onrender.com/login/)
admin: admin@example.com / <SEED_ADMIN_PASSWORD from Render>
member: member@example.com / <SEED_MEMBER_PASSWORD from Render>

Notes:
- New this sprint: admins create and edit dinners (admin area); teams of two sign up, invite their partner with a link, and join a waitlist when the dinner is full; dinner pages can be shared.
- AI dish ideas: open a dinner you signed up for, then "Dish ideas". Recipes come from TheMealDB.
- To test the partner invite, open the invite link in a private window and log in as the other account.
- Cancelling a sign-up (#15) moved to Sprint 3.
```

Adjust the notes to what actually shipped. If the OpenRouter key is not in place yet, add: "Dish ideas currently show matching recipes without AI reasons."
