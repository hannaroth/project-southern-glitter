# MGT 656 Project Proposal

**Team southern-glitter** · Three ideas, ranked by preference (1 = first choice).

---

## Idea 1: Event organizer with an AI co-organizer

### Tagline

Plan and run events with ease (pickup games, cohort trips, dinners, club outings), public or just for your groups, with an AI co-organizer that turns sign-up answers into balanced teams, preferred budgets, destinations and more.

### Major user journeys

- **As an organizer**, I log in, create a group such as "SOM Cohort GBS" or "East Rock Baddies". People can find it by searching in the app or through a link I share. I choose whether the group is **open** (anyone can join right away) or **approval required** (people stay pending until I accept them).
- **As an organizer**, I create an event (title, date, place, max attendees), choose whether it is public or visible to one of my groups only, choose whether RSVPs are **open** or **approval required** (for group and public events alike), and add sign-up questions such as "Skill level?", "Budget?" or "Who do you want to room with?".
- **As a member**, I find groups and events by searching and browsing in the app or through a shared link. I join groups, RSVP to events and answer the sign-up questions. If a group or event requires approval, I stay pending until the organizer accepts me. Group-only events are visible only to that group's members. If an event is full, I join the waitlist. When someone cancels, the first person on the waitlist moves up automatically and gets an email.
- **As an organizer**, I see a list of pending requests for my groups and events, with each person's sign-up answers, and accept or decline them.
- **As an organizer**, I build the event page from my own sections (e.g. "Schedule", "What to bring"). When I want help, I ask the AI co-organizer ("split everyone into 2 even teams", "what budget works for most people?", "suggest 3 destinations that fit the group"), then edit its draft section and publish it.
- **As an attendee**, I read the event page and post in the event's discussion thread, which only attendees can see.
- **As a site admin**, I remove spam events or groups.

### Core features (MVP)

1. **Accounts and groups**: sign-up and login with the framework's built-in authentication; groups that people find by search or a shared link; the owner sets each group to open joining or approval required; owner and member roles.
2. **Events and visibility**: create, edit, browse and search events (date, place, cap, custom sign-up questions); each event is public or for one group only, and its RSVPs are open or approval required.
3. **RSVP, approval and waitlist**: RSVP with answers to the sign-up questions; on approval-required events, RSVPs stay pending until the organizer accepts or declines them; a hard cap with automatic waitlist promotion on cancellation. Only accepted attendees count toward the cap. When two people grab the last spot at once, a database transaction decides who gets it.
4. **Event page and discussion**: a free-form page of sections the organizer creates and edits, plus an attendee-only discussion thread with pinned announcements. The thread is the basis for fuller messaging later.
5. **Email notifications**: an email when a waitlist spot opens, and a reminder before the event (scheduled job).

**Later (not MVP):** Splitwise-style expense splitting (who paid what, who owes whom), full messaging (group chats, direct messages), a discussion thread that updates live without page reloads.

**We skip:** in-app payments, bookings (hotels, courts), maps, push notifications, a native app.

### AI feature

The organizer types a request into an "Ask AI" box on the event page. The server sends the request plus the attendees' sign-up answers to an LLM through OpenRouter. The LLM returns structured JSON that becomes a **draft section**: balanced teams, the budget most people chose, destination ideas that fit the group's preferences, a summary of dietary restrictions, and so on. The organizer keeps, edits or discards it before publishing. When the draft is a grouping, the app checks that every attendee appears exactly once before showing it; if the check fails, it shows an error and offers to try again.

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

**We skip:** live bus positions and ETAs (no documented public API; stretch goal only with Yale Transit's permission), map tiles and turn-by-turn walking directions, address geocoding, the night "to-door" service, Safe Ride booking, a native app.

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

**We skip:** creating events in our app (we only aggregate), RSVPs and tickets, maps, scraping sites without feeds, members-only events, push notifications.

### AI feature

When new events arrive, the LLM reads each title and description and returns structured tags: category, audience (open to all or one school only), free food yes/no, and a one-line summary. Each event is tagged once and cached; the tags drive the filters. Each week the LLM also picks and explains "5 events for you" from our database, based on the user's interests.
