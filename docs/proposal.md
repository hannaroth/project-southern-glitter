# MGT 656 Project Proposal

**Team southern-glitter** · Three ideas, ranked by preference (1 = first choice).

---

## New Idea 1: Running dinner for New Haven

### Tagline

Team up with a friend, host one course, and eat the other two at other students' homes.

### Major user journeys

- **As an admin**, I log in, create a dinner (date, course times, theme, after-party, team cap), run the matching when sign-ups close and publish the plan. If a team drops out, a waitlisted team takes its place.
- **As an interested participant**, I pick an upcoming dinner ("Around the World, Sat Nov 14") and fill out the sign-up form for a team of two, with no password: both our emails, our address, dietary restrictions and the course we'd like to host. If it's full, we join the waitlist.
- **As a participant**, I sign in with my email, see which course we host and our guests' dietary restrictions, and ask the AI for a menu that works for everyone. On the night, the same page shows my evening stop by stop on an integrated map; each next address appears shortly before that course.

### Core features (MVP)

1. **Logins**: admins log in with a password (the framework's built-in authentication) to create and run dinners. Participants use only their email, with no password: to sign in, they enter it and click a one-time link we email them. Both partners can sign in to their team's page.
2. **Dinners**: create, edit and browse dinners, with a team cap and a waitlist.
3. **AI matching**: when sign-ups close, the LLM proposes which team hosts which course and where everyone eats, keeping routes short and honoring the sign-up preferences where it can. It sees only team numbers, preferences and the distances between addresses that our code computes, never names or addresses. Our code then checks the rules (each team hosts once, three teams per table, no two teams meet twice) and rejects a plan that breaks one; after a few failed tries it falls back to a valid plan from our own algorithm. It needs a multiple of 3 teams (at least 9).
4. **My Dinner and address reveal**: each team's stops on an integrated map (Leaflet with OpenStreetMap; each address is geocoded once at sign-up). An address is visible only to the teams eating there, and only shortly before that course.
5. **AI menu helper** (see below).

### AI feature

The LLM runs on our server through OpenRouter and does two jobs: it proposes the matching (feature 3) and suggests menus. On their host page, a team clicks "Suggest a menu". The server sends the course, the theme, the number of guests and their dietary restrictions (no names or addresses) to the LLM. It returns JSON: three dishes, each with ingredients and the restrictions it meets, plus a shopping list. The app shows only dishes that meet every guest's restrictions and keeps the restrictions on screen, so hosts still double-check allergies.

---

## Idea 1: Event organizer with an AI co-organizer

### Tagline

Event planning for individuals, with an AI co-organizer.

### Major user journeys

- **As a member**, I log in, see my upcoming events and groups on my home page, browse events and groups, join or leave them (which makes me an attendee), and can create my own events or groups (which makes me an organizer).
- **As an attendee**, I open an event I joined, see its details and my status (going, pending or waitlist), and chat with the other attendees.
- **As an organizer**, I create an event or group, choose how people can join it, and use the AI to plan things like teams or rooms.
- **As a site admin**, I remove spam events or groups. After x months of inactivity groups are deleted automatically. 

### Core features (MVP)

1. **Accounts**: sign up and log in with email, password and username.
2. **Home page**: events I organize, events I'm attending, and my groups.
3. **Create events and groups**: public or group-only events, a spot limit with a waitlist, and an event page with an attendee-only chat.
4. **Discover**: suggested events and groups, plus search with filters (group, date, location, category).

### AI feature

The AI runs on our server through OpenRouter and works with the attendees' sign-up answers. We have three options in mind and will pick one:

- **a) Organizer chat:** the organizer asks, e.g., "form two teams with equal skill levels", and the AI returns the teams as a draft the organizer can edit.
- **b) Automatic:** once sign-ups close, the AI forms teams or rooms on its own and shows the organizer a draft to approve.
- **c) Create by chat:** the organizer describes the event ("3-day Montreal trip for 20, mid budget") and the AI fills in the event page, like setting up a Notion page by talking to Claude.

---

## Idea 2: Yale Shuttle trip planner

### Tagline

Type where you need to go and get the right Yale shuttle, stop and time, with no map-reading.

### Major user journeys

- **As a student**, I type "Evans Hall to Union Station, arrive by 5:30pm". The app tells me which stop to walk to, which line to take, where to get off, and whether that line runs at that time.
- **As a commuter**, I save "Home → SOM" and see it on my home page every morning with the next expected departure.
- **As an admin**, I edit routes, stops and service hours, and post a service alert ("Blue line detour on Prospect St") that appears on every affected trip.
- **As a visitor**, I can plan a trip without an account; accounts are only for saved trips and alerts.

### Core features (MVP)

1. **Route database**: routes, stops (with coordinates), stop order per route and service hours (weekday, weekend, night), imported once from Yale's published route pages and maintained by an admin.
2. **Trip planner**: pick a start and destination from a seeded list of Yale buildings and landmarks; the app finds the nearest stops and searches for one-line or one-transfer options in the database. Most lines run as loops without a timetable, so times are shown as estimates ("about every N minutes").
3. **"Is it running now?"** status per line, from service hours.
4. **Saved trips and alerts**: saved trips, plus email alerts when an admin posts a disruption on a saved line.
5. **AI trip request** (see below).

### AI feature

The user types a free-text request ("I'm at Evans and need to catch the 5:40 train at Union Station"). The LLM returns JSON: start place, destination place, and an arrive-by or leave-at time. Our planner then computes the trip from the database; the LLM never invents routes. If it can't match a place, the app asks the user to pick from the list.

---

## Idea 3: All-Yale events hub

### Tagline

Every Yale event in one place (SOM, the other schools, the College and Bulldogs games), filtered to what you care about.

### Major user journeys

- **As a student**, I sign up, pick my interests (careers, sports, arts, talks, food) and schools, and see "This week at Yale": SOM, Law, Jackson and College events next to Saturday's home game.
- **As a student**, I search "AI" or "free food", filter by date, school and category, save events, and export my saved events to my own calendar.
- **As a sports fan**, I follow Yale Hockey and get a Monday email with this week's home games next to campus events.
- **As an admin**, I add or pause a feed, see when each feed last synced, and fix events the AI tagged wrong.

### Core features (MVP)

1. **Feed import**: scheduled import of official calendar (ICS) feeds into PostgreSQL ([Yale Connect](https://yaleconnect.yale.edu/ics_helper) university-wide and per-group feeds, [SOM CampusGroups](https://groups.som.yale.edu/ics_helper) school-wide and per-club feeds), upcoming events only, with de-duplication when one event appears in two feeds. To check in Sprint 1: that the feeds work without a Yale login, and whether the Yale Athletics feed lists every varsity game.
2. **Browse and search**: event list with filters (date, school or source, category) and keyword search.
3. **Accounts**: interests, saved events, and an ICS export of saved events.
4. **Weekly email digest.**
5. **AI tagging and personal picks** (see below).

### AI feature

When new events arrive, the LLM reads each title and description and returns structured tags: category, audience (open to all or one school only), free food yes/no, and a one-line summary. Each event is tagged once and cached; the tags drive the filters. Each week the LLM also picks and explains "5 events for you" from our database, based on the user's interests.
