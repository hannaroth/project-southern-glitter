# Running dinner backlog (team southern-glitter)

Each story below becomes one GitHub issue with the label `user story`; `task` items are technical work without a user. The acceptance criteria are written to hand to your coding agent as its spec. Sprint 1 items name their owner (the issue's assignee) and reviewer by GitHub username; later sprints get owners at their sprint planning. Sprint 1 stories are detailed; refine the later ones at each sprint's planning.

## GitHub Project setup

- One Project linked to the repo, with a **Board** view.
- **Iteration** field with one iteration per sprint (edit each iteration's start date and length):

| Iteration | Start | End | Length |
|---|---|---|---|
| Sprint 1 | Tue Nov 3 | Wed Nov 11 | 9 days |
| Sprint 2 | Thu Nov 12 | Wed Nov 18 | 7 days |
| Sprint 3 | Thu Nov 19 | Wed Dec 2 | 14 days |
| Sprint 4 | Thu Dec 3 | Fri Dec 11 | 9 days |

- Turn on the built-in workflows **Auto-add to project** (new issues from this repo) and **Item closed → Done**.
- Labels: `user story`, `task`.
- Break a story into **sub-issues** when it needs several pieces of work (marked below).

---

## Sprint 1: walking skeleton

### A/B test page at `/c6a680e`

`user story` · Sprint 1 · Owner: kawaiibunny202 · Reviewer: nicode656

As the course staff, I want a public page that shows each visitor a `kudos` or `thanks` button, so that the end-of-term A/B run can measure which text gets more clicks.

Acceptance criteria:
- `GET /c6a680e` returns 200 without logging in, with no redirect (no trailing slash added) and no pop-up or cookie banner.
- The page lists our team members' course nicknames: magnificent-aardvark, stormy-zebra, delightful-crocodile.
- The page contains exactly one `<button id="abtest">` whose text, ignoring surrounding whitespace, is exactly `kudos` or `thanks` (lowercase). The server writes the text into the HTML; no JavaScript sets it.
- A new visitor gets `kudos` or `thanks` at random, 50/50. The choice is stored in the session (or a cookie), and the same visitor always sees the same text.
- The first view per visitor stores one impression (visitor id, variant, timestamp) in the database. Reloads do not add impressions.
- The button sits in a plain `<form method="post">`. A click stores at most one click per visitor (visitor id, variant, timestamp), then redirects back to `/c6a680e`. That redirect does not add an impression or change the variant.
- Tests cover: 50/50 assignment with the random choice mocked, the variant staying the same across visits, one impression per visitor, one click per visitor, and the redirect after a click not counting.

### A/B stats at `/c6a680e/stats`

`user story` · Sprint 1 · Owner: kawaiibunny202 · Reviewer: nicode656

As the course staff, I want the live A/B results as JSON, so that I can read which variant won right after the run.

Acceptance criteria:
- `GET /c6a680e/stats` returns 200 and JSON without logging in.
- `preferred` is `"kudos"` or `"thanks"`: the variant with the higher click rate (clicks ÷ impressions), computed from the database at request time.
- With zero impressions or a tie, `preferred` still returns one of the two values (no error, no null, no division by zero).
- The JSON also includes the counts: `{"preferred": "kudos", "kudos": {"impressions": 212, "clicks": 63}, "thanks": {"impressions": 207, "clicks": 21}}`.
- Tests cover a clear winner, a tie, and zero impressions.

### Base app: sign up, log in and log out, with roles

`user story` · Sprint 1 · Owner: nicode656 · Reviewer: hannaroth

As a student, I want an account with my email and a password, so that my dinner sign-ups stay mine.

Acceptance criteria:
- Sets up the base app: a Django project connected to Postgres through `DATABASE_URL`, a CSS framework, `.env.example`, the settings Render needs, and the Commands section of `AGENTS.md`. Everything else in Sprint 1 builds on this.
- Uses the framework's built-in authentication (Django `django.contrib.auth`, or the Rails authentication generator). Email is the login name.
- Pages to sign up, log in and log out. After logging in, I land on the home page and see my name and a log-out link.
- No email verification and no two-factor, so graders can log in with a username and password.
- Two roles from day one: admin and participant. Admins are users with an admin flag (Django `is_staff`). Only admins can open the admin area; a regular user who tries gets refused.
- Tests cover: sign-up, log-in with the right and the wrong password, log-out, and a regular user being refused the admin area.

### Seed command for demo data and grader accounts

`user story` · Sprint 1 · Owner: nicode656 · Reviewer: kawaiibunny202

As a grader, I want ready-made accounts and demo dinners on staging, so that I can try the app without signing up.

Acceptance criteria:
- One command (Django `python manage.py seed`) creates an admin account, a participant account and three upcoming demo dinners: "Around the World", "Through the Eras" and "No Theme, Just Dinner".
- Running it twice changes nothing and raises no error.
- The grader passwords come from environment variables (`SEED_ADMIN_PASSWORD`, `SEED_MEMBER_PASSWORD`), never from the repo. Accounts use fake names and `@example.com` emails.
- The README says how to run it; we run it on staging after every database reset.

### Upcoming dinners on the home page

`user story` · Sprint 1 · Owner: nicode656 · Reviewer: kawaiibunny202

As a student, I want to see the upcoming running dinners, so that I can pick one to join.

Acceptance criteria:
- A `Dinner` table with title, theme, date, after-party place and team cap, created by a migration.
- The home page lists dinners dated today or later, soonest first, with title, date, theme and after-party. Past dinners are hidden.
- Visible without logging in.
- Works on phones and desktops (use a CSS framework such as Bootstrap or Pico).
- Tests cover: past dinners hidden, order by date.

### Staging on Render with a Neon database

`task` · Sprint 1 · Owner: hannaroth (Render connects through the repo owner's GitHub) · Starts once the base app is merged

- A Render web service deploys `main` automatically; a Neon Postgres database for staging only.
- All configuration in environment variables: `SECRET_KEY`, `DATABASE_URL`, `DEBUG` off, allowed hosts, the seed passwords. A `.env.example` lists the names with no values; `.env` is in `.gitignore`.
- The app listens on `$PORT`, logs to stdout, runs migrations on each deploy and serves its static files (Django: WhiteNoise).

### Tests on every pull request (stretch)

`task` · Sprint 1 (stretch) · Owner: kawaiibunny202 · Reviewer: nicode656

- GitHub Actions runs the tests and a linter on every pull request against a throwaway Postgres.
- Once it works, Hanna makes passing checks required for merging into `main` (only the repo owner can change that setting).
- Counts toward the technical challenge (CI).

### Check everything on staging

`task` · Sprint 1 · Owner: kawaiibunny202 · Starts once staging is live and the other Sprint 1 items are merged

- Log in on staging with each grader account (admin and participant).
- Open `/c6a680e` in two private windows: each shows `kudos` or `thanks`, a reload keeps the same one, and a click counts once.
- `/c6a680e/stats` shows the counts and a `preferred` value.
- Comment on the matching issue for anything broken, so its owner can fix it.

### Sprint 1 report and submission

`task` · Sprint 1 · Owners: nicode656 (report), hannaroth (submission) · Reviewer: hannaroth

- Check the course project page first: Kyle said on Nov 9 he will add detail to the report format.
- `docs/mgt656/sprints/sprint-1.md` on `main`: goal, status, what shipped with links to closed issues and merged pull requests, what works on staging, one agent lesson from each of us, and backlog changes; a burn-up screenshot from the Project's Insights tab in `docs/mgt656/sprints/img/`.
- On the course site: the login page, a username and password for each kind of user, the repo URL and the staging URL.

---

## Sprint 2

### Admins create and edit dinners

`user story` · Sprint 2

As an admin, I want to create and edit a dinner, so that students can sign up for it.

Acceptance criteria:
- Fields: date, start times for starter, main and dessert, theme, after-party name and address, team cap, sign-up deadline.
- Only admins can create or edit (the Django admin is fine).

### Sign up for a dinner as a team of two

`user story` · Sprint 2 · sub-issues: sign-up form, partner invite link, waitlist

As a student, I want to sign up for a dinner with a friend, so that we cook and go together.

Acceptance criteria:
- Form: our address, dietary restrictions (vegetarian, vegan, gluten-free, dairy-free, nut allergy, plus a free-text field) and the course we'd like to host (starter, main, dessert or no preference).
- I invite my partner with a share link; the team is complete when they accept while logged in.
- A person can be on only one team per dinner, and sign-ups close at the deadline.
- Once the team cap is reached, new teams join a waitlist in sign-up order.

### Share a dinner

`user story` · Sprint 2

As a student, I want to send a dinner's link to friends, so that they can join too.

Acceptance criteria:
- Each dinner has a detail page with a copy-link button; logged-out visitors see it and are asked to log in to join.

### Cancel before the matching

`user story` · Sprint 2

As a team, we want to cancel before the matching, so that another team gets our spot.

Acceptance criteria:
- Either partner can cancel until sign-ups close; the first waitlisted team moves up.

### Production environment

`task` · Sprint 2

- A separate Render service and Neon database for production, promoted from staging by a deliberate step (counts toward CD).

---

## Sprint 3

### Match teams when sign-ups close

`user story` · Sprint 3 · sub-issues: rule checker, fallback plan, addresses to coordinates, distances, AI proposal, evaluation set

As an admin, I want the app to plan who hosts which course and where everyone eats, so that I don't have to puzzle it out by hand.

Acceptance criteria:
- Rule checker: every team hosts exactly one course and eats the other two as a guest, three teams per table, no two teams meet twice. Needs a multiple of 3 teams, at least 9.
- Fallback plan from a fixed rotation in our own code; a test shows it passes the rule checker for every multiple of 3 from 9 to 60 teams.
- Each address is turned into coordinates once at sign-up and stored; our code computes the straight-line distances between them.
- The LLM (through OpenRouter, server-side) gets only team numbers, preferences and distances, never names or addresses, and returns the plan as JSON. Plans that break a rule are rejected and retried, then the fallback is used.
- Tests mock the LLM. An evaluation set of saved sign-up lists compares the AI plans with the fallback on total walking distance.
- The admin reviews the plan, then publishes it.

### My Dinner page with timed address reveal and map

`user story` · Sprint 3

As a participant, I want to see my evening stop by stop, so that I know where to go next.

Acceptance criteria:
- Shows the course we host, our guests' dietary restrictions, and our three stops plus the after-party on a map (Leaflet with OpenStreetMap tiles).
- An address is visible only to the teams eating there, and only from a set time before that course (e.g. 30 minutes); tests check both rules.

### Recipe database

`user story` · Sprint 3

As a host, I want menu ideas drawn from real recipes, so that I can cook something tested.

Acceptance criteria:
- A one-time import (re-runnable) of recipes from an open source into Postgres: title, cuisine, category, ingredients, instructions, source link.
- Candidate source: TheMealDB (cuisines and categories such as Starter, Dessert, Vegetarian and Vegan match our themes and courses). Its free key is for development and education; a public production app needs its £10 supporter key, so ask Kyle.

### AI menu helper

`user story` · Sprint 3

As a host, I want a menu that suits my guests, so that everyone can eat what we cook.

Acceptance criteria:
- Our code first selects recipes from our database that fit the course, the theme and the guests' restrictions; the LLM picks three, explains why and writes a shopping list for the group. It cannot suggest a recipe that isn't in our database.
- The guests' restrictions stay on screen; tests mock the LLM.

---

## Sprint 4

### Friends

`user story` · Sprint 4

As a student, I want to add friends, so that I can see which dinners they joined and pick a partner quickly.

### Calendar export

`user story` · Sprint 4

As a participant, I want to add my dinner to my calendar, so that I don't forget it.

Acceptance criteria:
- Download an `.ics` file with the course times and the after-party; no addresses, since those are revealed on the night.

### A waitlisted team replaces a team that drops out

`user story` · Sprint 4

As an admin, I want a waitlisted team to take over a dropped team's place, so that the published plan still works.

### Sign in with a one-time email link (optional)

`user story` · Sprint 4

As a student, I want to sign in by clicking a link sent to my email, so that I don't need a password.

### Prepare production for the A/B run

`task` · Sprint 4

- Delete our own test impressions and clicks on production before the announced run window.
