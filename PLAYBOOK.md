# DB Asset Hub: the build playbook

*Written 26 Oct 2026. Nothing in this repo is built yet. This file is the plan
the build sessions work from: what DB Asset Hub is, the decisions behind it,
the data, the rules, every feature, and the phases that build it.*

DB Asset Hub is Deitemeyer Brothers' own version of Whip Around. The crew runs
daily inspections of the trucks, trailers, equipment, tools and fall
protection from their phones. A failed item puts the asset out of service at
once. Defects are bundled into work orders, which a mechanic signs off on a
phone. Preventive maintenance schedules itself, the parts shelf counts itself
down, the roadside documents are in the driver's pocket, and the office gets a
dashboard showing the state of the whole fleet.

It has two halves:

| Half | Who uses it | Where it lives |
| --- | --- | --- |
| **Field**: the mobile intake tool | drivers, crews, mechanics | a new **Equipment** tab in **DB Crew** (`db-crews.web.app`), which already installs on iPhone and Android |
| **Desk**: the management command center | office, fleet manager, owners, the shop | **DB Asset Hub**, a web app at `assets.deitemeyerbrothers.com` |

---

## How to use this playbook

1. Read §1 to §6 once. They are the shape, the decisions, the architecture, the
   data and the rules. Every phase leans on them.
2. Carl does **Phase 0** (§10): answer the questions and gather the asset list.
   No code is written until then.
3. Work the phases **in order**. Each one ships something people can use, has a
   "Done when" list that decides when it is finished, and ends with a
   ready-to-paste **kickoff prompt** for a Claude Code session.
4. The pilot starts after Phase 5. You can stop after any phase and still have
   a working system.
5. When a phase changes a decision in here, change this file in the same pull
   request, with the date and who decided.

### Rules for every build session

These hold in every phase and every repo. If code you find contradicts one,
stop and ask Carl. Don't work around it.

1. **New features go on a branch with a pull request**, one per repo touched.
   Don't merge your own. Once the Vercel project is connected, merging to
   `main` deploys production.
2. **The rules live in `src/domain/`** as pure functions with tests (§6). Status,
   PM due dates, approvals, stock and compliance are decided there and nowhere
   else, so the phone, the desk and the crons can never disagree.
3. **Every crew-facing word exists in English and Spanish** behind DB Crew's
   ES·EN pill. English leads (D8).
4. **A phone never loses work.** Every write goes through DB Crew's outbox with
   a client reference, and the server treats a re-send as the same write.
5. **Payroll is not ours.** Never create, edit or close a JobTread time entry.
6. **Secrets go only in Vercel env vars and Apps Script Script Properties**,
   never in the repo, a test, a log line or a chat message.
7. **The hub can change the answer, never break it.** If DB Hub's feed is
   missing or late, people get their defaults. The seeded admins are never
   locked out.
8. **AI suggests and people decide** (D7).
9. **Nothing a DOT auditor could ask for is deleted** (D9). Records are voided
   with a reason; assets are retired.
10. **Every change a person makes lands in `audit_log`**: who, when, before and
    after.
11. **Update the README in the same pull request**, in the house style: what
    changed, why, who asked, the date.
12. **DB Hub's feed deployment is never `clasp deploy -i`'d.** See
    `bledsoecw/DB-Hub` `CLAUDE.md`. A new version of the feed is cut in the
    editor as operations@, with Who has access set to Anyone.
13. **Use the design system (§4.11).** Brand tokens and the standard
    components only: no one-off colors, fonts, icons or widgets. Every desk
    screen works on a laptop and on a phone.

---

## 1. The shape of it

```
          FIELD: phones                                    DESK: browsers
 ┌─────────────────────────────────┐          ┌────────────────────────────────────┐
 │ DB Crew PWA, Equipment tab      │          │ DB Asset Hub (Next.js on Vercel)   │
 │ scan QR · checklists · FIX      │          │ assets.deitemeyerbrothers.com      │
 │ my repairs · documents          │          │ dashboard · work orders · PM ·     │
 └───────────────┬─────────────────┘          │ parts · reports · checklist builder│
                 │ the phone's own session    └──────────────┬─────────────────────┘
 ┌───────────────▼─────────────────┐                         │ Google sign-in
 │ DB Crew Apps Script (as* calls) │  Bearer CREW_APP_SECRET │
 │ the door, as for Close Out      ├──X-Acting-Email────────►│ /api/crew/*   /api/desk/*
 └─────────────────────────────────┘  X-Client-Ref           │
                                              ┌──────────────┴───────┬────────────────┐
                                              │ Neon Postgres        │ Vercel Blob    │
                                              │ every record         │ photos, PDFs   │
                                              └──────────────────────┴────────────────┘
  DB Hub access feed ─────► people, names, levels (both halves read it)
  JobTread (read only) ───► who was on the clock which day (inspection compliance)
  Fuel card · telematics ─► fuel, odometer, engine hours, fault codes
  Gmail as operations@ ◄── alerts and the morning digest
  AI provider ◄──────────► FleetAI suggestions and ES→EN notes
```

### 1.1 Every requested feature, where it lives, when it's built

| Requested feature | Section | Phase |
| --- | --- | --- |
| Dynamic checklist execution | §7.1 | 2 |
| Mandatory photo capture & fraud prevention | §7.1 | 2 |
| Bar/QR code asset identification | §7.1 | 1 (stickers), 2 (scan) |
| Odometer & engine hour meter log | §7.1 | 2 |
| Instant fail categorization | §7.2 | 3 |
| Visual evidence uploader (photos, markup, voice/typed note) | §7.2 | 3 |
| Digital assignment clipboard | §7.3 | 4 |
| Digital mechanic sign-off | §7.3 | 4 |
| Photo proof of resolution | §7.3 | 4 |
| Roadside compliance vault (the wallet) | §7.4 | 7 |
| Asset health summary tiles | §8.1 | 5 |
| Driver & asset leaderboards | §8.1 | 5 |
| Activity live feed | §8.1 | 2 (list), 5 (live) |
| Defect-to-work-order converter | §8.2 | 4 |
| Internal & external shop dispatch | §8.2 | 4 |
| Work order kanban | §8.2 | 4 |
| Document & file aggregator | §8.2 | 4 |
| Multi-trigger service schedules | §8.3 | 6 |
| Automated maintenance alerts | §8.3 | 6 |
| Drag-and-drop checklist builder | §8.4 | 2 |
| Shop shelf stock tracker | §8.5 | 8 |
| Automatic stock deductions | §8.5 | 8 |
| Low stock alerts | §8.5 | 8 |
| Total cost of ownership ledger | §8.6 | 9 |
| Custom dashboard builder | §8.6 | 9 |
| Audit-ready history exporter (CSV, Excel, PDF) | §8.6 | 9 |
| Fuel card data sync | §8.7 | 11 |
| Telematics connectors (Motive, Samsara, Geotab), DTCs | §8.7 | 11 |
| Shop Ops: scheduling grid, labor clock, approval limits, quotes/invoices | §9.1 | 10 |
| FleetAI: photo analysis, defect triage, receipt reading, routing | §9.2 | 12 |

---

## 2. Decisions

**D1. The field half is a tab in DB Crew, not a new app.** Carl, 23 Oct 2026:
*"I want all of this on the crew app. The checkout app is retired."* The crew
already has DB Crew on their home screens, signed in, with the in-app camera,
the offline outbox, English and Spanish, dictation and push. A second app
would mean a second sign-in and a second icon nobody opens. DB Crew is a PWA,
so it already covers "runs on iOS and Android": it installs on both from the
browser. App-store builds aren't planned. If one is ever needed, DB CheckOut's
Expo app shows the way.

**D2. The desk half is its own app: Next.js on Vercel at
`assets.deitemeyerbrothers.com`.** It uses the same Vercel team, framework and
Node version (24.x) as the Production Board and the Estimator. It is not a new
tab in DB Hub. The hub is Apps Script on a spreadsheet, and this is relational
data (assets → inspections → defects → work orders → parts). It also needs
webhooks (Apps Script's `doPost` can't read request headers, so it can't check
a telematics provider's signature), crons, and drag-and-drop uploads. The brief
calls the desk "the central DB Hub". Here that means DB Asset Hub, and the
screens say **Asset Hub** so nobody mixes it up with the HR hub.

**D3. Records go in Neon Postgres and files in a private Vercel Blob store.**
Neon is already installed on the Deitemeyer Brothers Vercel team (Marketplace,
Free plan, which lists 1 GB storage and 100 CU-hours of compute per project).
This app gets its own Neon project. Photos and PDFs never go in the database.
The Blob store is private and files are served only through a signed-in route,
never a public URL, because insurance cards, VINs and faces are in them.

**D4. DB Hub stays the one store for people and access.** A new **Asset Hub**
column goes in the hub's App access panel, and both halves read it from the
feed the other apps already use. `ASSET_HUB_ADMINS` in Vercel names the people
who are Admin whatever the feed says, the same as DB Crew's `OPS_EMAILS`, so a
broken feed can't lock the office out.

**D5. The phone reaches the Asset Hub through DB Crew's Apps Script**, through
the same door Close Out uses. The phone calls its own script with its own
session. The script forwards the call with a shared secret, who is asking
(`X-Acting-Email`, `X-Acting-Name`) and the outbox's `X-Client-Ref`. The Asset
Hub trusts the script, not the phone, and looks up the person's level itself.

**D6. JobTread is read, and payroll is never written.** The Asset Hub reads
JobTread time entries to learn who was working which day, so it can count the
inspections each person owed. It reads nothing else. A mechanic's wrench time
is the Asset Hub's own per-work-order timer. DB Crew's clock is payroll and
stays untouched.

**D7. FleetAI suggests and people decide.** AI never changes an asset's
status, a stock count, a cost or a sign-off on its own. Its provider is chosen
in Phase 12 by testing on DB's own photos and invoices.

**D8. English first.** (Carl, 26 Oct 2026.) Every screen leads in English, on
the phone and at the desk. Spanish stays one tap away: DB Crew's ES·EN pill
flips the Equipment tab to Spanish for that person, and the phone remembers
it. A note dictated in Spanish is kept as it was said and also stored in
English; the desk shows the English, with the original one tap away.
Checklist items are written in both languages in the builder, English
first.

**D9. Nothing a DOT auditor could ask for is ever deleted.** Inspections,
defects, signatures, repair sign-offs and work orders are voided with a
reason, never deleted. Assets are retired, not removed. See §12.

**D10. A polished, branded, enterprise-grade interface.** (Carl, 26 Oct
2026.) Both halves are designed to the standard of established professional
desktop and mobile software: their structure, layout, navigation patterns and
UI/UX quality, carried in Deitemeyer Brothers' own logo, brand colors and
visual identity (§4.11). It should feel like a commercial product built for
the company, not a generic website or a basic web form. Other products,
Whip Around included, are references for patterns and quality only; their
branding, screens, wording and icons are never copied. Design work changes
presentation, user experience and interface architecture. Every function,
business rule and integration in this plan stays as written unless a change
is asked for explicitly.

---

## 3. Words used in this file

| Word | Means |
| --- | --- |
| **asset** | anything tracked: a truck, trailer, compressor, generator, nailer, ladder, harness. Every asset has a **tag** like `TRL-03` |
| **category** | the kind of asset (Pickup truck, Dump trailer, Generator…). Checklists, PM and meters hang off it |
| **team** | the division or crew an asset or person belongs to (Roofing, Gutters, Service, Construction, Shop). The exporter's "team" filter |
| **inspection** | one run of one checklist on one asset by one person. A **DVIR** is an inspection on a checklist marked DVIR |
| **defect** | something wrong with an asset: from a failed checklist item, a "report a problem", a fault code, or the desk |
| **out of service (OOS)** | not to be used until a defect is resolved |
| **work order (WO)** | the repair job: one asset, one or more defects or a PM task, one assignee (in-house mechanic or outside shop) |
| **PM** | preventive maintenance: a schedule by days, miles and/or hours |
| **level** | what a person may do in the Asset Hub, set in DB Hub (§4.3) |
| **the door** | DB Crew's Apps Script forwarding the phone's calls to `/api/crew/*` (§4.4) |

The Spanish labels for the Equipment tab and for "asset" (unidad? equipo?)
are settled with the crew in the pilot. "Equipo" also means "team", so ask
before shipping it.

---

## 4. Architecture

### 4.1 What changes in each repo

| Repo | Changes |
| --- | --- |
| `bledsoecw/DB-Asset-Hub` (this one) | everything new: the desk, the crew API, the database, the crons, the integrations |
| `bledsoecw/db-crew-app` | the Equipment tab in `dbtimeclock-pwa/public/index.html`; the `as*` forwarders and the level gate in `apps-script/Code.gs`; tests in `apps-script/code-test.mjs` and a new `dbtimeclock-pwa/dev/equipment-test.mjs` |
| `bledsoecw/DB-Hub` | one new entry in `ACCESS_APPS_` (the Asset Hub column), its onboarding task, and a new version of the feed deployment (Phase 1 only) |
| `bledsoecw/DB-CheckOut` | nothing. Its `auth.ts` (Google sign-in, sessions) and `translate.ts` (Gemini, with model discovery) are copied as starting points |
| DB Portal (`bledsoecw/db-portal`) | a card linking to the Asset Hub, added by hand after Phase 5 |

### 4.2 The Asset Hub's layout

```
app/
  (desk)/              signed-in pages: dashboard, assets, inspections, defects, work-orders,
                       maintenance, parts, fuel, reports, dashboards, exports, settings
  api/crew/…           the door DB Crew's script calls (docs/CREW-API.md)
  api/desk/…           JSON for the desk pages (session cookie)
  api/cron/…           Vercel Cron targets (Bearer CRON_SECRET)
  api/files/[id]       streams one private Blob file to a signed-in person
  api/hooks/…          fuel and telematics webhooks (Phase 11)
  q/[tag]/             the sticker landing page; shows no asset data without sign-in
  whoami/              build, commit, who you are, your level and where it came from, what's reachable
  design/              the living style guide (§4.11), Admin only
src/
  domain/              the rules (§6): pure functions, no I/O, every one tested
  db/                  Drizzle schema and queries
  auth/                Google sign-in, sessions, levels (feed + ASSET_HUB_ADMINS)
  integrations/        hubFeed, jobtread, mail, ai/, fuel/, telematics/
  pdf/                 sticker sheets, WO sheet, audit packets, quotes and invoices
  ui/                  the app shell and the standard components (§4.11)
  styles/              the DB design tokens as CSS variables and the Tailwind theme
drizzle/               SQL migrations, committed
test/                  node:test units and route tests with fakes; test/db/ against a Neon branch
e2e/                   Playwright desk flows
docs/CREW-API.md       the contract with DB Crew; both repos build to it (Appendix C is the draft)
```

Libraries, picked once so every phase uses the same ones: Drizzle ORM with
`drizzle-kit` migrations and the Neon serverless driver; `@vercel/blob`;
dnd-kit (kanban and builder drag-and-drop); Recharts (charts);
react-grid-layout (custom dashboards); pdf-lib (PDFs; DB Hub already uses it);
`qrcode` (sticker QR codes); exceljs (Excel exports); pdf.js in the browser
(PDF page images); Zod (validating every request body and every AI answer).
For the interface (§4.11): shadcn/ui (Radix primitives and Tailwind CSS,
themed with the DB tokens, including its command palette and toasts);
TanStack Table; react-hook-form; Lucide icons.

### 4.3 Who can do what

The level comes from DB Hub's App access panel, **Asset Hub** column (key
`assetHub` on the feed). Blank means the default for a company account.

| Level | On the phone (Equipment tab) | At the desk |
| --- | --- | --- |
| *(blank)*: everyone | scan, inspect, report a problem, acknowledge repairs, see status, documents | no access: the sign-in says "ask the office" |
| **View** | same as blank | everything read-only: dashboard, feed, assets, WOs, reports, exports |
| **Mechanic** | adds **My repairs**: timer, parts, notes, after photos, sign-off | the kanban and their own WOs; can open a WO from defects (it waits for approval) |
| **Manager** | same as Mechanic | runs the fleet: approve WOs up to the approval limit, dispatch, dismiss defects, put assets out of or back in service, PM, parts, documents, exports |
| **Admin** | same as Mechanic | adds the checklist builder (publish), settings, integrations, approval limits, labor rates, reopening a completed WO, voiding records |
| **Off** | the tab is hidden and the door refuses | refused |

Where the answer comes from, first match wins (the same order DB Crew uses):

1. `ASSET_HUB_ADMINS` (Vercel env) are Admin. This is never on the feed and
   can't be changed from either screen.
2. The DB Hub feed's `assetHub` value for the person, read from a copy at most
   five minutes old. If the feed is unreachable, the last good copy is used.
   With no copy at all, the feed has no opinion.
3. Blank, the default.

A person whose hub `status` is left, inactive or terminated is refused, as DB
Crew does. Sign-in itself is a verified Google account on
`deitemeyerbrothers.com` or on `GOOGLE_ALLOWED_EMAILS`, the same rule as DB
CheckOut's `assertAllowedIdentity`.

### 4.4 The door: DB Crew → Asset Hub

This works exactly like Close Out (`coFetch_` in DB Crew's `Code.gs`):

- The phone calls DB Crew's script (`fn: 'asInspect'` and so on) with its own
  30-day session. The script resolves the person from the verified token,
  never from anything the phone sent.
- The script gates first. If the person's `assetHub` level is Off, nothing goes
  through. A mechanic route also needs Mechanic or higher. The script then
  forwards to `ASSET_HUB_URL + /api/crew/...` with:
  - `Authorization: Bearer <ASSET_HUB_SECRET>` (the same value as the Asset
    Hub's `CREW_APP_SECRET`)
  - `X-Acting-Email`, `X-Acting-Name`
  - `X-Client-Ref` on writes, matching `^[A-Za-z0-9._-]{1,64}$` (Close Out's rule)
- The Asset Hub checks the secret in constant time, looks up the person's level
  itself (§4.3), and answers. With `CREW_APP_SECRET` unset, the door doesn't
  exist.
- The script answers `{ status, body, ms, reason }` and never throws for the
  server's trouble, so the phone keeps the item and says why.
- **Until `ASSET_HUB_URL` is set, the tab doesn't appear**, so DB Crew can ship
  its half before the Asset Hub is live.

How the server answers:

| Answer | Meaning | What the phone does |
| --- | --- | --- |
| 200 | done. A re-send with the same `X-Client-Ref` gets the first answer again, with `duplicate: true` | clears it from the outbox |
| 400 | refused, and it would be refused again; `error` gives the reason in EN and ES | keeps it as **rejected** with the reason, and lets the person discard it |
| 401 / 403 | wrong secret / level | shows the reason; doesn't retry |
| 404 | unknown asset or WO | rejected |
| 409 | not yet (e.g. a photo the inspection names hasn't landed) | retries |
| 5xx, timeout, unreachable | trouble | retries with backoff |

The full list of routes is Appendix C. Phase 1 copies it into
`docs/CREW-API.md`, and from then on both repos build to that file, the way
`CREW-ASSIGNMENTS-API.md` pins the board's contract.

### 4.5 The phone: offline and fast

- **The boot pack.** When the app opens, and every five minutes while it is
  open, `asBoot` returns every active asset (tag, name, category, status, since
  when, assigned to, meter kind, last reading), the published checklist
  versions, the categories and the settings the phone needs. The phone keeps
  it in IndexedDB. A scan or search answers from it **instantly**, and the
  network answer lands behind it (DB Crew's T2.5 rule: fast to the finger).
  Status drawn from the cache says "as of 7:42a".
- **Drafts are saved as you go.** An inspection is stored item by item, so
  nothing is lost if the app closes, the phone dies or a call comes in.
- **Send means the outbox.** Photos go first, then the inspection that names
  them, then any acknowledgment. Every item carries its own client reference.
- **The wait curtain** (T2.5) greys the screen for any tap that has to wait on
  the network.
- **Documents are on the phone** for the assets the person is assigned to and
  the last five they opened (§7.4).

### 4.6 Photos and files

- **Camera or phone.** DB Crew already knows the difference between its own
  camera and **From my photos** (T2.9). Required-photo checklist items and
  meter photos are **camera only**: no gallery button, and the server refuses
  `source: "phone"` for them. Defect evidence can be either. A phone photo
  carries the PHONE badge and its EXIF time. After photos follow DB Crew's
  AFTER rule: a phone photo must have been taken after the WO was opened.
- **The stamp.** Every camera photo gets a band burned in at capture: asset
  tag · date and time · GPS · first name. A photo can't be passed off later
  for another asset or another day.
- **Two sizes, made on the phone:** full (long edge ≤ 1600 px, JPEG) and thumb
  (≤ 320 px). The server does no image processing.
- **Fingerprint.** The server stores the sha256 of every full image. If the same
  hash is already on file for that asset, the inspection is flagged "photo
  used before".
- **Markup.** A marked-up copy is a new file with `annotated_of` pointing at
  the original. Both are kept; the desk shows the marked-up one with an
  "original" toggle.
- **Storage.** Private Blob keys look like `files/2026/10/<uuid>.jpg`. The desk
  reads them only through `/api/files/<id>`, which checks the session.
- **Desk uploads** (drag and drop) go from the browser straight to Blob with a
  token from `/api/desk/files/upload` (Vercel Blob client uploads). For a PDF,
  the browser also renders page images with pdf.js and uploads them beside it,
  for previews and for the wallet.
- **Signatures** are PNG files with purpose `signature`, like any other file.

### 4.7 Background work

Vercel Cron runs these from `vercel.json`, authenticated with
`Authorization: Bearer $CRON_SECRET`. Cron times are UTC, and DB's day is
**America/New_York**, so every date rule computes the local day explicitly.

| When | Route | What it does |
| --- | --- | --- |
| daily 10:30 UTC (6:30a EDT / 5:30a EST) | `/api/cron/daily` | PM states, document expiry, low stock, inspections missed yesterday, open/clear alerts, the morning digest email |
| hourly (needs Vercel Pro) | `/api/cron/hourly` | telematics and fuel pulls, DB Hub feed refresh, retrying failed emails and AI jobs |
| right after a request (Next.js `after()`) | none | the out-of-service email, FleetAI jobs, cost rollups |

On the Hobby plan crons run at most once a day. Everything hourly then moves
into the daily run, and the feed is refreshed on read (five-minute cache).

### 4.8 Alerts and email

Every alert is a row in `alerts`, opened once per condition and cleared when
the condition clears. A person gets one email when something changes, not one
a day for as long as it stays true. The morning digest is the exception.

| Alert | Opens when | Bell | Instant email | Digest |
| --- | --- | --- | --- | --- |
| Asset out of service | an OOS defect or a manual hold | ✓ | ✓ | ✓ |
| New defect | any defect | ✓ | | ✓ |
| WO needs approval | estimate over the opener's limit | ✓ | ✓ | ✓ |
| WO over estimate | actuals over the approved estimate (§6.6) | ✓ | | ✓ |
| PM due soon / overdue | §6.4 | ✓ | overdue only | ✓ |
| Document expiring / expired | 30 days before / on the day | ✓ | expired only | ✓ |
| Low stock | on hand ≤ reorder point | ✓ | | ✓ |
| Inspection missed | an owed daily check not done (§6.8) | ✓ | | ✓ |
| Suspicious inspection | too fast, photo reused, meter backwards or jumped | ✓ | | ✓ |
| New fault code | telematics DTC | ✓ | if severe | ✓ |

Who gets each kind is in Settings. Email goes out through the Gmail API as
`operations@deitemeyerbrothers.com`, using a service account with domain-wide
delegation for `https://www.googleapis.com/auth/gmail.send`. That is the same
mechanism DB Hub uses for Calendar, and a Workspace admin adds the scope once.
Until `MAIL_SA_KEY` is set, alerts stay in the bell and nothing breaks. Push
to phones goes through DB Crew's existing FCM setup later; it is optional and
not in any phase's "done when".

### 4.9 Settings and secrets

Vercel environment variables. Paste the values only in Vercel's dashboard.

| Variable | What | From phase |
| --- | --- | --- |
| `DATABASE_URL` | Neon. The integration sets it | 1 |
| `BLOB_READ_WRITE_TOKEN` | the private Blob store. Connecting the store sets it | 1 |
| `SESSION_SECRET` | signs desk sessions (`openssl rand -hex 32`) | 1 |
| `GOOGLE_CLIENT_ID` | the OAuth web client for desk sign-in | 1 |
| `GOOGLE_WORKSPACE_DOMAIN` | `deitemeyerbrothers.com` | 1 |
| `GOOGLE_ALLOWED_EMAILS` | extra addresses allowed beside the domain | 1 |
| `ASSET_HUB_ADMINS` | always Admin, e.g. operations@ and Carl | 1 |
| `HUB_FEED_URL`, `HUB_FEED_KEY` | DB Hub's access feed and its key | 1 |
| `PUBLIC_URL` | `https://assets.deitemeyerbrothers.com` | 1 |
| `CREW_APP_URL` | `https://db-crews.web.app`, for the sticker page's "Open in DB Crew" | 1 |
| `CREW_APP_SECRET` | the door's secret; same value as DB Crew's `ASSET_HUB_SECRET` | 2 |
| `GEMINI_API_KEY` | ES→EN notes. The same kind of key DB CheckOut uses | 3 |
| `MAIL_SA_KEY`, `MAIL_FROM` | Gmail sending as operations@ | 3 |
| `CRON_SECRET` | Vercel Cron's bearer | 3 |
| `JT_GRANT_KEY` | JobTread, read only: who was on the clock which day | 5 |
| `FUEL_*`, `TELEMATICS_*` | per provider, named in Phase 11 | 11 |
| `AI_PROVIDER`, `AI_MODEL_<TASK>`, `ANTHROPIC_API_KEY`, `AI_MONTHLY_CAP_CENTS` | FleetAI | 12 |

DB Crew Script Properties: `ASSET_HUB_URL` (the Asset Hub's origin) and
`ASSET_HUB_SECRET`.

Everything else (approval limit, labor rates, alert recipients, minimum
inspection time, photo limits, due-soon windows) lives in the `settings` table
and is edited on the desk's Settings page, so nobody needs a deploy for the
everyday knobs.

### 4.10 Tests and shipping

| Command | What |
| --- | --- |
| `npm test` | node:test through tsx: every `src/domain` rule, and the routes with fakes (no network, no database). Same style as DB CheckOut |
| `npm run test:db` | the queries and migrations against a throwaway Neon branch (`DATABASE_URL_TEST`) |
| `npm run e2e` | Playwright on the desk, with a test sign-in that only exists when `NODE_ENV=test` |
| `npm run typecheck`, `npm run lint` | strict TypeScript, ESLint |
| DB Crew: `node apps-script/code-test.mjs` | the `as*` forwarders and the level gate (extend the existing file) |
| DB Crew: `node dev/equipment-test.mjs` | the Equipment tab end to end against `dev/mock.js`, like `closeout-test.mjs` |

Shipping:

- **Asset Hub:** a pull request gets a Vercel preview with its own Neon branch
  (the integration's preview branching). Merging to `main` deploys production.
  Migrations run in the build step (`drizzle-kit migrate && next build`)
  against that environment's database. Vercel Authentication covers
  everything except the custom domain, as on the Production Board.
- **DB Crew:** `clasp push -f`, then `clasp deploy -i <the API deployment>`
  (the ID is in `apps-script/README.md`), then `firebase deploy --only
  hosting`. Confirm on the phone's Diagnostics screen.
- **DB Hub:** the two steps in its `CLAUDE.md`, plus the feed deployment's new
  version in the editor (Phase 1).
- **Every release:** `/whoami` on the Asset Hub prints the build, the commit,
  who you are, your level and where it came from, and whether the database,
  Blob, the feed, JobTread and Gmail are reachable. That is DB Hub's
  `?whoami=1` habit.

### 4.11 The interface: design system and layout

The bar is D10: both halves look and work like a commercial product built for
Deitemeyer Brothers, at the standard of established enterprise desktop and
mobile software.

**The brand already exists.** The Deitemeyer Brothers design system was
rebuilt in July 2026 from the company's live tools (the Sales & Operations
Dashboard, DB Cam, the Team Portal). A snapshot sits in `bledsoecw/db-crew-app`
under `project/_ds/deitemeyer-brothers-design-system-d0550d2f-…/` (tokens,
logo rules, component inventory). Phase 1 copies its tokens into this repo as
the one source, after checking Claude Design for a newer export. Nothing in
the Asset Hub uses a framework's default colors, fonts, logo or favicon.

| Token | Value | Used for |
| --- | --- | --- |
| Primary | navy `#1A4789` (`--navy-700`) | buttons, links, headers, focus. The sidebar rail is `--navy-800` `#142A52` |
| Accent | electric green `#3CC84A` (`--green-500`) | live, positive or on-goal, and the one emphasized word in a label. Never a primary action |
| Surfaces | app background slate `#F4F6F9`, cards white, hairlines `#D8DFE8` | every Asset Hub screen. Warm cream is for customer-facing pages only |
| Status | success `#29A03D`, warning `#B5892A`, danger `#C0392B`, info `#21569F`, idle `#9A9285` | asset and WO status, alerts, PM states |
| Type | Archivo (uppercase headings; metrics with tabular figures), Barlow (body and UI), IBM Plex Mono (labels, table headers, tags, timestamps) | everything |
| Icons | Lucide line icons, one set | everything |
| Shape and motion | radius 3 / 5 / 8 px, 1 px hairlines, little shadow, 120–320 ms transitions | everything |
| Logo | the DB wordmark, on a white plaque on navy; never redrawn or recolored | sidebar, sign-in, emails, PDFs, sticker sheets |

Status colors: Safe is success; Defects and Due soon are warning; Out of
service and Overdue are danger; Retired is idle. A status chip always carries
an icon and a word as well as its color.

The wordmark's typefaces are proprietary, so the system substitutes Google
Fonts (Archivo, Barlow, IBM Plex Mono) until Carl sends the real files (Phase
0, question 11).

**Desktop first: the app shell.** Designed at 1440 × 900 first, then 1024,
tablet (768) and phone (390). Frequent jobs are one click from anywhere: the
sidebar, Ctrl+K and the New menu.

- **Sidebar:** the navy rail (the design system's `SideNav`), always there:
  the logo plaque on top; grouped items with icons: *Operate* (Dashboard,
  Assets, Inspections, Defects, Work orders), *Maintain* (Maintenance, Parts,
  Fuel), *Analyze* (Reports, Dashboards, Exports); Settings and the signed-in
  person at the foot. It collapses to icons and remembers the choice. The
  active item has the green left bar.
- **Top toolbar:** the page title and breadcrumbs; global search (**Ctrl+K**,
  a command palette that jumps to an asset tag, a WO number, a person or a
  page); **New** (work order, asset, checklist, part); the alerts bell with
  its count; the user menu.
- **The page:** a header with the title, one primary action and the rest in a
  "…" menu; a filter bar; then panels. Selecting a row opens its detail in a
  right-hand drawer, so the list stays in view. Only deep work (the checklist
  builder, the kanban, reports) takes a full page.
- **Density:** comfortable table rows by default, with a compact toggle.

**Mobile and tablet.** Below tablet width the sidebar becomes a bottom tab bar
(Dashboard, Assets, Work orders, Alerts, More), tables become card lists with
the same search and filters, drawers and dialogs become full-screen sheets,
the kanban shows one lane at a time with a lane switcher, and every touch
target is at least 44 px.

**The Equipment tab in DB Crew** is a native-app-style screen inside DB Crew's
own shell, whose bottom tabs stay as they are: a top bar with search, a
floating Scan button, cards, bottom sheets for actions, and glove-sized
targets. It uses the same brand tokens, copied into DB Crew as CSS variables
(DB Crew is one HTML file with no build step, so it can't use the React
components). Restyling the rest of DB Crew is not part of this build unless
Carl asks.

**The standard components** are built once with shadcn/ui (Radix primitives
and Tailwind CSS) themed with the DB tokens, with the design system's own
pieces (`SideNav`, `PanelHeader`, `DataTable`, `Badge`, `Stat`, `MetricStrip`,
`KpiBanner`) rebuilt on top:

| Pattern | Standard |
| --- | --- |
| Tables | TanStack Table: search, column filters, sort, show/hide columns, saved views per person, a row "…" menu and right-click menu, multi-select with bulk actions, CSV export, sticky header, virtual scrolling for long lists |
| Forms | react-hook-form with Zod; labels above fields, inline errors, required fields marked; short forms in a dialog, long ones in a drawer; a warning before leaving unsaved changes |
| Dialogs | a confirmation for anything permanent (void, cancel, retire) that says what will happen |
| Notifications | a toast for the result of each action, with Undo where it can be undone; the bell for alerts (§4.8); a banner for system state (feed down, an integration failing) |
| Status | chips with icon, word and color |
| Empty, loading, error | every list says what to do when it's empty, shows skeletons while loading, and offers Retry on an error |
| Dashboards | interactive: hover for values; click a tile, bar or row to filter; the date range in the toolbar |
| Keyboard | Ctrl+K search, `/` to focus the page's search, Esc to close, arrow keys in tables, a visible focus ring |

**Quality bar:** WCAG 2.1 AA contrast (green text uses `--green-700` on light
surfaces, per the design system), everything reachable by keyboard, usable at
200% zoom, and no layout jump while loading. Emails, the WO sheet, audit
packets, quotes and invoices, and sticker sheets carry the same brand.

**The living style guide:** `/design` (Admin only) shows every token and
component in the brand. Phase 1 builds it, every later phase keeps it
current, and the e2e tests screenshot it.

---

## 5. The data

Postgres on Neon. Money is integer cents. Times are `timestamptz` stored in
UTC, and "a day" means America/New_York. Ids are UUIDs except where a human
number is shown (`WO-1001`). Lists in `[]` are Postgres arrays or join tables,
whichever Drizzle makes cleaner.

```
-- people and setup ---------------------------------------------------------
people             email PK, name, team_id, level_cached, level_source, labor_rate_cents,
                   bill_rate_cents, approval_limit_cents (null = level default), active, last_seen_at
teams              id, name                       -- Roofing, Gutters, Service, Construction, Shop
settings           key PK, value jsonb, updated_by, updated_at
audit_log          id, at, actor_email, action, entity, entity_id, before jsonb, after jsonb

-- assets -------------------------------------------------------------------
asset_categories   id, name_en, name_es, kind (vehicle|trailer|equipment|tool|safety),
                   tag_prefix, meter_kind (odometer|hours|both|none), archived
assets             id, tag UNIQUE, name, category_id, team_id,
                   status (safe|defect|out_of_service|retired), status_since, status_reason, manual_hold,
                   make, model, year, vin_serial, plate, plate_state, gvwr_lbs, is_cmv,
                   assigned_to_email, home_base, photo_file_id,
                   purchase_date, purchase_price_cents, in_service_date, expected_life_months,
                   retired_at, retire_reason,
                   odometer, engine_hours, meters_at,          -- cached from meter_readings
                   fuel_card_ref, telematics_ref, tank_gallons, fuel_type, notes
asset_status_log   asset_id, status, from_at, to_at, cause_kind, cause_id   -- downtime comes from here
meter_readings     id, asset_id, kind (odometer|hours), value, at,
                   source (inspection|work_order|fuel|telematics|desk), source_id, photo_file_id,
                   by_email, flagged, flag_reason, accepted_by           -- "meter replaced" lives here too
asset_documents    id, asset_id, kind (registration|insurance|permit|annual_inspection|cab_card|title|manual|other),
                   title, file_id, page_file_ids[], expires_on, in_wallet, uploaded_by, voided_at

-- checklists and inspections ----------------------------------------------
checklists         id, name_en, name_es, purpose (pretrip|posttrip|daily|each_use|periodic),
                   is_dvir, min_seconds, archived
checklist_versions id, checklist_id, version, items jsonb, published_at, published_by
                   -- immutable once published; inspections point at the version they used
checklist_targets  checklist_id, category_id | asset_id, every (each_use|daily|weekly|monthly|quarterly|annual)
inspections        id, client_ref UNIQUE, asset_id, checklist_version_id, inspector_email,
                   started_at, submitted_at, received_at, duration_s,
                   result (pass|defects|out_of_service), odometer, engine_hours, meter_photo_file_id,
                   lat, lng, signature_file_id,
                   flags[] (too_fast|photo_reused|meter_backwards|meter_jump|sent_late),
                   voided_at, void_reason, voided_by
inspection_answers inspection_id, item_key, value jsonb, passed, na, comment, photo_file_ids[]
acknowledgments    id, client_ref UNIQUE, asset_id, person_email, defect_ids[], signature_file_id, at

-- defects and work orders --------------------------------------------------
defects            id, client_ref UNIQUE, asset_id, inspection_id, item_key, title,
                   note_en, note_said, said_lang, photo_file_ids[],
                   severity (defect|out_of_service), category,
                   status (open|in_work_order|resolved|dismissed),
                   source (inspection|report|telematics|desk), reported_by, reported_at,
                   repeat_count, last_reported_at, last_reported_by,
                   work_order_id, resolution (repaired|not_needed), resolution_note,
                   resolved_by, resolved_at, dismissed_by, dismissed_reason
work_orders        id, number UNIQUE, asset_id, title, description, priority (low|normal|high|urgent),
                   status (pending_approval|scheduled|in_progress|on_hold|completed|cancelled),
                   hold_reason (parts|vendor|approval|other), hold_note,
                   assignee_kind (internal|vendor), mechanic_email, vendor_id,
                   scheduled_for, due_by, est_hours, estimate_cents,
                   approved_by, approved_at, opened_by, opened_at, started_at, completed_at,
                   completion_note, signed_by, signature_file_id, signed_at, meters_at_close jsonb,
                   pm_schedule_id, labor_cents, parts_cents, vendor_cents, total_cents,  -- rollups
                   cancelled_reason, reopened_reason
wo_events          id, wo_id, at, by_email, kind (status|assign|note|file|part|labor|approve|estimate), data jsonb
wo_labor           id, client_ref UNIQUE, wo_id, mechanic_email, started_at, ended_at, minutes, rate_cents
wo_lines           id, wo_id, kind (part|vendor|fee), description, qty, unit_cost_cents, part_id, file_id
files              id, client_ref UNIQUE, blob_key, thumb_key, filename, mime, bytes, sha256,
                   purpose (inspection|meter|defect|after|signature|document|invoice|receipt|quote|other),
                   source (camera|phone|desk|integration), taken_at, stamped, annotated_of,
                   uploaded_by, uploaded_at, owner_kind, owner_id, ai_status
vendors            id, name, phone, email, address, kind (shop|tires|glass|dealer|mobile|parts), notes, active

-- preventive maintenance ---------------------------------------------------
pm_schedules       id, name, asset_id | category_id, every_days, every_miles, every_hours,
                   soon_days, soon_miles, soon_hours, action (work_order|inspection), checklist_id,
                   task_text, est_hours, auto_create_wo, active
pm_baselines       id, schedule_id, asset_id, done_at, odometer, engine_hours, wo_id, inspection_id
                   -- every reset is a new row; the latest per (schedule, asset) is the baseline

-- parts --------------------------------------------------------------------
parts              id, sku, name, category, unit, bin, on_hand, reorder_point, reorder_qty,
                   avg_cost_cents, vendor_id, fits_category_ids[], count_needed, active
part_moves         id, client_ref UNIQUE, part_id, qty (+ in / - out),
                   kind (receive|use|return|adjust|count), unit_cost_cents, wo_id, file_id,
                   by_email, at, note

-- fuel, telematics, alerts, analytics, AI ----------------------------------
fuel_tx            id, provider, external_id, asset_id, card_ref, driver, at, gallons, total_cents,
                   unit_cents, odometer, merchant, city, state, product, flags[]
                   UNIQUE (provider, external_id)
dtc_events         id, asset_id, code, description, severity, first_seen, last_seen, cleared_at, defect_id
integrations       provider PK, config jsonb (never secrets), last_sync_at, last_ok_at, last_error
alerts             id, kind, asset_id, ref_kind, ref_id, state (open|cleared), opened_at, cleared_at,
                   emailed_at, seen_by[]        -- at most one open alert per (kind, ref)
fixed_costs        id, asset_id, kind (insurance|registration|lease|loan|other), monthly_cents, from_on, to_on
dashboards         id, owner_email, name, shared, layout jsonb
exports            id, by_email, params jsonb, status, file_id, created_at, finished_at, error
ai_runs            id, task, provider, model, prompt_version, input_ref, output jsonb, ms,
                   in_tokens, out_tokens, cost_cents, outcome (accepted|edited|rejected|ignored), decided_by
quotes_invoices    id, number UNIQUE, kind (quote|invoice), wo_id, bill_to, lines jsonb, tax_cents,
                   total_cents, status (draft|sent|paid|void), file_id     -- Phase 10
```

A checklist item, as stored in `checklist_versions.items`:

```jsonc
{
  "key": "tires",                    // stable across versions; reports join on it
  "type": "pass_fail",               // pass_fail | choice | number | meter | photo | text | signature | section
  "label": { "es": "Llantas: dibujo, presión, costados", "en": "Tires: tread, pressure, sidewalls" },
  "help":  { "es": "Revise las cuatro", "en": "Check all four" },
  "required": true,
  "allowNA": false,
  "photo": "required",               // none | optional | on_fail | required  (required = camera only)
  "comment": "on_fail",              // never | on_fail | always  ("pass/fail with mandatory comment")
  "failSeverity": "out_of_service",  // defect | out_of_service
  "choices": [],                     // choice: [{ "value", "label": {es,en}, "fails": bool }]
  "meter": null,                     // meter: "odometer" | "hours"; with photo "required" it's verified
  "min": null, "max": null           // number
}
```

---

## 6. The rules (`src/domain`)

Each rule is a pure function with its own test file. The routes, the crons and
the desk pages call these; none of them re-implements one.

### 6.1 Asset status

```
status(asset, openDefects) =
  retired                 if asset.retired_at
  out_of_service          if asset.manual_hold or any open defect has severity out_of_service
  defect                  if any defect is open or in_work_order
  safe                    otherwise
```

Dismissed and resolved defects don't count. "Overdue for service" is **not** a
status. It is a PM state shown beside the status, so an asset can be Safe and
Overdue at the same time. Status is always **recomputed from the open
defects**, in the same transaction that changes a defect, and never set
directly. An inspection that arrives late, after a newer one, therefore can't
roll an asset back. Every change writes `asset_status_log`.

### 6.2 Taking an inspection in

The server checks the inspection, without trusting the phone:

- every required item is answered, and N/A is used only where the item allows it;
- every `photo: "required"` item, and every verified meter, has at least one
  photo with `source: "camera"`. If not, it answers 400 with the item named;
- every photo the inspection names has arrived. If not, it answers 409 and the
  phone retries;
- the checklist version is published and targets this asset or its category.

Then, in one transaction:

- Each failed item opens a defect, **or adds to the open one** for the same
  asset and item key (`repeat_count + 1`, "reported again by…"), so a flat
  tire reported by three drivers is one defect, not three.
- Severity is the item's `failSeverity`, raised to out of service if the crew
  answered "not safe to use". The crew can raise it but never lower it.
- The result is `out_of_service` if any OOS defect was touched, `defects` if
  any defect was, and `pass` otherwise. The asset status is recomputed (6.1).
- Flags, which never block anything:
  - `too_fast`: duration under the checklist's `min_seconds`;
  - `photo_reused`: a full-image hash already on file for this asset;
  - `meter_backwards`: a reading below the last one;
  - `meter_jump`: more than the setting allows since the last reading
    (default 800 mi or 24 h per day elapsed);
  - `sent_late`: submitted more than 24 h after it started. This is for
    information only; it usually means a dead spot.

### 6.3 Meters

`meter_readings` is a ledger, and the asset's `odometer` / `engine_hours` cache
is its latest accepted value. A flagged reading is kept but ignored by PM until
a Manager accepts it, or marks **meter replaced at X**, which starts a fresh
baseline. Sources, from most to least trusted: telematics, work order close,
inspection with photo, fuel, inspection without photo, desk.

### 6.4 PM due

For a schedule with any of `every_days`, `every_miles`, `every_hours` and the
asset's latest baseline (date, odometer, hours):

```
due_date  = baseline.done_at + every_days
due_miles = baseline.odometer + every_miles
due_hours = baseline.engine_hours + every_hours

per trigger:  overdue   if today ≥ due_date   | odometer ≥ due_miles   | hours ≥ due_hours
              due_soon  if today ≥ due_date - soon_days | odometer ≥ due_miles - soon_miles | ...
              ok        otherwise
state = the worst trigger                     (whichever comes first)
```

Default windows are 14 days, 500 mi and 15 h. A meter that hasn't been updated
in 14 days says so beside the state ("meter last read Oct 3"), because the
answer might be wrong. With no baseline yet, the asset's `in_service_date` and
first reading count as done. Completing a WO linked to the schedule writes a
new baseline from `meters_at_close`. For an inspection-action schedule, the
inspection on its checklist does.

### 6.5 Work order states

| From → to | Who | Needs |
| --- | --- | --- |
| *(new)* → Pending approval | anyone Mechanic+ | an asset, and defects or a task |
| *(new)* → Scheduled | Manager+ within their limit | an assignee; a date is optional |
| Pending approval → Scheduled | Manager+ whose limit covers the estimate | an assignee |
| Pending approval → Cancelled | Manager+ | a reason. Its defects go back to Open |
| Scheduled → In progress | the mechanic (timer start) or Manager+ | |
| In progress ↔ On hold | the mechanic or Manager+ | a hold reason: parts / vendor / approval / other |
| In progress / On hold → Completed | **in-house:** the assigned mechanic's sign-off (§7.3). **Outside shop:** a Manager's sign-off on the desk, with the vendor's invoice attached | every linked defect resolved as repaired or not needed |
| Completed → In progress | Admin | a reason (logged) |
| any open state → Cancelled | Manager+ | a reason |

The kanban refuses an illegal drag and says which rule. Each move writes a
`wo_events` row. Completing a WO resolves its defects, recomputes the asset
status (6.1), and writes the PM baseline if the WO is linked to a schedule.

### 6.6 Approvals and limits

- Limits by level: Admin has no limit, Manager has the `approval_limit_cents`
  setting (default **$500**), and a Mechanic's limit is $0, so anything a
  mechanic opens waits for approval. Shop Ops (Phase 10) adds per-person limits.
- A WO whose estimate is over its opener's limit lands in Pending approval and
  alerts the people who can approve it.
- Over estimate: when the actual total passes the approved estimate by more
  than 10% *and* more than $50 (both settings), the "over estimate" alert
  opens. The work isn't blocked.

### 6.7 Stock

- `on_hand` = the sum of `part_moves.qty`, cached on `parts` and updated in the
  same transaction as the move.
- **receive:** adds stock and re-averages the cost:
  `avg = (on_hand·avg + qty·unit) / (on_hand + qty)`.
- **use** (from a WO): subtracts at the current average cost and adds `qty ×
  avg` to the WO's parts cost. It is allowed to go below zero with a warning
  ("the count says 0, it may be off"), and that sets `count_needed`. A
  mechanic is never stopped by the books.
- **return:** reverses a use at that use's cost. **adjust / count** needs a
  reason and is logged.
- **Low stock:** `on_hand ≤ reorder_point` opens one alert per crossing.

### 6.8 Inspection compliance

```
owed(person, day)  = the person had a JobTread time entry that day (America/New_York)
                     AND is the assigned driver of ≥ 1 active asset with a daily checklist
                     → one owed inspection per such asset
                     (with telematics: only the assets that moved that day)
done(person, day)  = an inspection by that person, on that asset, on that day, on one of its daily checklists
compliance         = done ÷ owed over the range
```

Each-use assets (tools, ladders, harnesses) aren't counted, because nobody can
know when they were used. They show "last inspected" instead. If JobTread
can't be reached, the leaderboard says "clock days unavailable" and the rest
of the dashboard works.

### 6.9 Total cost of ownership

For one asset over a date range:

```
labor  = Σ wo_labor.minutes / 60 × rate at the time   (Asset Hub labor rate, not payroll)
parts  = Σ part uses on its WOs
vendor = Σ wo_lines kind vendor|fee on its WOs
fuel   = Σ fuel_tx.total_cents
fixed  = Σ fixed_costs prorated by day
depreciation (toggle) = purchase_price ÷ expected_life_months, prorated by day
per mile = total ÷ miles in range;  per hour = total ÷ hours in range   (from meter_readings)
```

---

## 7. Field features: DB Crew's Equipment tab

The tab is there for every role (crew, site manager, service, manager,
operations), as long as `ASSET_HUB_URL` is set and the person's level isn't
Off. The labels below are the English ones, which lead (D8). Each has a
Spanish twin behind DB Crew's ES·EN pill, the way Close Out's OK / FIX is
BIEN / FALLA. Its home screen has:

- a big **Scan** button and a search box (tag or name);
- **My assets** (assigned to me), each card showing the tag large, the name, a
  status chip (green **Safe**, amber **Defects**, red **Out of service**) and
  "inspected today ✓" or "pre-trip owed";
- **Recent**;
- for Mechanic and up, **My repairs (3)**.

### 7.1 Inspection and DVIR intake

**Dynamic checklist execution**

- An asset's card shows its checklists. The asset's own target comes first,
  then its category's. The main button is the one owed now: **Daily check**,
  or the pre-trip on a CMV. A 10-point roofing trailer check, a 5-point
  generator check and the DOT pre-trip are just different checklists
  (Appendix A).
- One item per row with big **OK / FIX** buttons, as Close Out's checklist
  has. N/A shows where the builder allows it. Choice, number and text inputs
  are inline. Required items are marked, and progress shows as "7 of 10".
- A pre-trip opens with the acknowledgment step if one is owed (below).
- A DVIR ends with a finger signature; other checklists just **Send**.

**Mandatory photo capture and fraud prevention**

- An item with `photo: "required"` opens DB Crew's in-app camera, with no From
  my photos button. The photo is stamped (§4.6). The server refuses a phone
  photo for that item even if one is forced through.
- `on_fail` photos are asked for only when FIX is tapped.
- The desk flags `too_fast`, `photo_reused`, `meter_backwards` and
  `meter_jump` inspections (§6.2), and FleetAI later checks the photos
  themselves (§9.2).
- What this can't do: no app can stop someone from photographing a photo. The
  stamp, the GPS, the fingerprint and the timing make that visible on the
  desk, and that is the real deterrent.

**QR asset identification**

- The sticker is a QR code of `https://assets.deitemeyerbrothers.com/q/TRL-03`,
  with the tag in big letters and "Scan with DB Crew" (with a Spanish line
  under it).
- The in-app scanner uses `BarcodeDetector` where the browser has it (Chrome on
  Android). Elsewhere (iPhone Safari) it uses jsQR, vendored as one file the
  way DB Hub vendors pdf-lib. The scan resolves from the boot pack instantly
  and opens the asset's card with **Start inspection**.
- **From the phone's own camera app,** `/q/TRL-03` offers **Open in DB Crew**,
  a link to DB Crew with `?asset=TRL-03`, which DB Crew reads on open. On
  Android an installed DB Crew opens. On iPhone the link opens Safari, which
  isn't the home-screen app (iOS keeps them apart), so the crew is taught the
  in-app Scan button. The `/q` page shows no asset data to anyone who isn't
  signed in.
- A damaged sticker: type the tag.

**Odometer and engine hour log**

- An asset whose category has a meter asks for the odometer, the hours or
  both before Send, prefilled with the last reading ("Last: 84,212 · Oct 24")
  to confirm or retype.
- With "verify with photo" on (the default for trucks and generators), a camera
  photo of the dash or hour meter is required.
- Going backwards asks "Sure? The last reading was higher" and sends it with a
  flag. The crew is never blocked.

**Next driver's acknowledgment** (49 CFR 396.13, §12)

- If a defect on this asset was repaired since this person last inspected it,
  the pre-trip's first screen lists it ("Rear light, repaired by Juan, Oct
  25") with a checkbox and a signature, stored in `acknowledgments`.

### 7.2 Field defect and failure reporting

**Instant fail categorization**

- **FIX** opens the defect sheet inline: photos, a note, and **Safe to use?**
  (yes/no). Severity comes from the item, and "no" raises it to out of
  service.
- On Send, the server sets the asset's status in the same transaction (§6.1)
  and answers with it. The phone shows the banner ("TRL-03 is OUT OF SERVICE.
  Don't use it. The office has been told.") and updates its cache. The desk
  feed and tiles show it on the next poll (≤ 15 s), and an OOS sends the
  instant email.
- **"Immediately" means the moment the phone has signal.** Offline, that phone
  shows the asset as OOS at once and says "Sends when there's signal". Other
  phones learn when it lands.
- An out-of-service asset shows a red banner to everyone who opens or scans
  it: since when, by whom and why.
- **Report a problem** on the asset's card opens the same sheet without a
  checklist (`source: report`).

**Visual evidence uploader**

- Up to six photos per defect (a setting), from the camera or From my photos.
  Phone photos get the PHONE badge and their EXIF time (DB Crew T2.9).
- **Mark up:** tap a photo and draw with a finger (circle, arrow, freehand) in
  red or yellow, with Undo and Done. The marked copy is a new photo, and the
  original is kept (§4.6).
- **The note:** typed, or dictated with the mic DB Crew's day log already uses
  (`SpeechRecognition` where the phone has it; the keyboard's mic where it
  doesn't), in English, Spanish or a mix. A note not in English is sent as
  said plus English (`asTranslate` → the Asset Hub's translate, from DB
  CheckOut's `translate.ts`), and the crew sees the English before sending, as
  in Close Out's area note.

### 7.3 Mechanic mobile workflow

**Digital assignment clipboard: My repairs** (Mechanic+)

- Shows the WOs assigned to me in Scheduled, In progress or On hold, sorted by
  due date then priority. Each shows the WO number, the asset's tag and name,
  what's wrong, when it's due, its status and any parts set aside for it.
- The WO screen has the defects with their photos and notes (in English, or in
  Spanish on that person's pill, with the original), the history, the parts on
  it, the files (view only) and the timer.
- **Timer:** Start / Pause / Resume. One runs at a time per mechanic; starting
  another pauses this one. The times are taken on the phone and sent through
  the outbox, so it works offline.
- **Parts used:** search the shelf and enter a quantity. The stock is deducted
  when it lands (Phase 8; before that, a free-text "parts used" line). Notes
  can be typed or dictated.

**Digital mechanic sign-off**

- **Finish & sign:** each defect is marked Repaired or Not needed (which needs
  a note). The mechanic enters the meters at close (prefilled), at least one
  after photo, a completion note and a finger signature.
- The server completes the WO, resolves its defects and recomputes the status,
  so the asset turns green if nothing else is open. This record is the DOT
  repair certification (§12).
- **The answer comes from the server, never a guess.** "TRL-03 is back in
  service" shows only when the server says so (DB Crew's T2.8.3 habit).

**Photo proof of resolution**

- After photos come from the camera, or from the phone's photos only if taken
  after the WO was opened (DB Crew's AFTER rule). They are stamped and shown
  beside the before photos on the desk and in the audit packet.

### 7.4 The wallet: Documents

- An asset's card lists its documents marked `in_wallet`: registration,
  insurance card, permits, the annual inspection report, the cab card. Each
  has an expiry chip ("expires Nov 3"), red once expired.
- **Show the officer:** full screen with a brightness hint, pinch to zoom,
  swipe between documents, and nothing else on screen.
- **Offline:** the documents for the person's assigned assets and the last
  five they opened are kept on the phone as page images (§4.6) and say
  "Available offline". A roadside stop is often where the signal isn't.
- An expired document still shows (the newer paper copy might be in the glove
  box), but in red, and the desk was warned 30 days before.
- Driver documents (CDL, medical card) are HR papers and belong in DB Hub's
  vault. They are not part of this build.

---

## 8. Desk features: DB Asset Hub

The sidebar (§4.11): Dashboard · Assets · Inspections · Defects · Work orders ·
Maintenance · Parts · Fuel · Reports · Settings (checklists, categories, teams,
people and limits, vendors, alerts, integrations, FleetAI).

### 8.1 Live feed and dashboard

**Asset health tiles:** **Safe · With defects · Out of service · Overdue for
service**, with Due soon small underneath. They count active (not retired)
assets, and a click opens the filtered asset list. The first three add up to
the fleet. Overdue overlaps them, and the tile says so.

**Leaderboards**

- **Inspection compliance** (§6.8): person, owed, done, %, average time,
  flagged inspections, defects found. Sorted worst first by default; range and
  team filters.
- **Worst assets:** most defects, most downtime days (from
  `asset_status_log`), most cost, cost per mile or hour. Range and category
  filters.

**Activity live feed:** newest first, polled every 15 seconds while the tab is
visible, with new rows sliding in. Each row shows the time, person, asset,
checklist, a result chip, the duration, flags and a photo strip. A click opens
the inspection: every answer, photos in a lightbox, a map pin, the signature
and the linked defects. Filters cover team, category, person and result.

**The bell:** open alerts (§4.8), newest first, with "seen".

### 8.2 Maintenance and work orders

**Defect-to-work-order converter**

- **Open defects** are grouped by asset, with photos, the English note (and
  the original), severity, who reported it and when, and the repeat count.
- Select several on one asset → **Create work order**. The title is prefilled
  from the defects, and the form takes an estimate, priority and due date. Or
  **Add to WO-1042**, or **Dismiss** with a reason (pre-existing, cosmetic,
  duplicate). Dismissing keeps the photos and note as a record.
- Manager+ can also **Put out of service** or **Return to service** by hand,
  with a reason (`manual_hold`).

**Internal and external dispatch**

- **Assign to:** an in-house mechanic (Mechanic-level people) or an outside
  shop (vendors, with **Add vendor** inline), plus a date.
- An outside shop's WO has **Email the shop**, which sends a WO sheet (PDF:
  the asset, VIN and plate, the defects with photos, who to call) from
  operations@.

**Kanban:** lanes **Pending approval · Scheduled · In progress · On hold
(waiting parts / vendor / approval) · Completed** (the last 30 days). Cards
drag between lanes, and an illegal move is refused with the rule (§6.5). A card
shows the WO number, asset, title, assignee, due date, cost so far and file
count, and goes red when overdue. Clicking opens the drawer: defects, the
timeline (`wo_events`), labor, parts, vendor lines, files and actions.

**Document and file aggregator:** drop PDFs or images on a card or the drawer.
They upload to Blob and attach with a kind (invoice / receipt / quote / photo
/ other), guessed from the name and changeable. An invoice or receipt asks for
the amount and invoice number (FleetAI pre-fills them in Phase 12), which
become a vendor or parts line in the WO's cost. Every file is listed on the WO
and the asset.

### 8.3 Preventive maintenance automation

**Multi-trigger schedules**

- A schedule goes on a category (every asset in it) or on one asset. It can
  have any combination of **days, miles and hours**, whichever comes first,
  with due-soon windows. Its action is to open a WO (automatically, or as a
  suggestion) or to require an inspection on a checklist.
- Each asset's Maintenance panel shows each schedule's next due date, miles
  and hours, and a state chip.
- Seed schedules, which Carl edits in Phase 6: truck oil change every 5,000 mi
  or 180 days; generator service every 150 h or 365 days; ladder inspection
  every 90 days (inspection action); DOT annual inspection every 365 days on
  CMVs; fire extinguisher monthly check.

**Automated maintenance alerts:** the Overdue tile and the asset chips update
on the daily run. A schedule entering Due soon goes in the morning digest. One
going Overdue sends an instant email, once. With `auto_create_wo` on, the WO
opens itself and lands as §6.6 says. Completing it resets the baseline (§6.4).

### 8.4 Custom checklist builder

- **Left:** the palette: Pass/Fail, Pass/Fail + comment, Multiple choice,
  Number, Meter (odometer/hours), Photo, Text, Signature, Section header.
- **Middle:** the checklist. Drag items in, drag to reorder, click to edit
  (dnd-kit).
- **Right:** the item's properties: English and Spanish labels with a
  **Translate** button that fills the empty one for a person to
  check, plus required, N/A allowed, photo rule, comment rule, fail severity,
  choices (and which ones fail), and min/max.
- **Preview** as the phone will show it, with an ES/EN toggle.
- Checklist settings: name, purpose, DVIR (which requires a signature and the
  meters), minimum seconds, and targets (categories or assets, with how often).
- **Draft → Publish** makes a new immutable version. Old inspections keep the
  version and wording they were done on, and reports join items by key across
  versions. Admin publishes; Manager can draft.

### 8.5 Parts inventory

- **Shelf:** SKU, name, bin, on hand, reorder point, average cost and value.
  Low ones are red, at the top.
- **Receive** (quantity, unit cost, vendor, receipt file), **Adjust / Count**
  (with a reason), and each part's history of moves.
- **Automatic deductions:** a part added to a WO (on the desk or the
  mechanic's phone) is deducted at the average cost and added to the WO's
  parts cost. Removing it returns it (§6.7).
- **Low stock alerts:** crossing the reorder point opens one alert, showing
  the reorder quantity and vendor, in the bell and the digest.

### 8.6 Analytics and reporting

**Total cost of ownership ledger:** pick a range and a team, category or
asset. A table per asset shows labor, parts, vendor, fuel, fixed, depreciation
(toggle), total, miles or hours, and $/mi or $/h (§6.9). A monthly stacked
chart breaks it down by cost type, every number drills down to its lines, and
it exports to CSV or Excel.

**Custom dashboard builder:** **My dashboards**. Add widgets from templates,
each with a range, filters and a chart type (bar / line / table / big number),
then drag and resize them on a grid (react-grid-layout), save, and optionally
share with the office. The first templates:

- Assets with the most defect flags
- Average repair turnaround (defect reported → resolved; WO opened → completed)
- Downtime days by asset
- Cost by category by month
- Cost per mile by asset
- Inspection compliance by person
- Inspections per day
- Defects by category
- Open WOs by status and age
- Parts below reorder point
- Fuel $/mile trend
- PM on-time %

**Audit-ready history exporter**

- Filters: date range, team, category, asset(s), person. Record types:
  inspections, defects, WOs, PM history, fuel, documents.
- **CSV:** a zip with one file per type. **Excel:** one sheet per type.
- **PDF packet per asset**, in the order an auditor reads it: the asset's card;
  the DVIRs with signatures and photos; the repair sign-offs; the
  acknowledgments; the annual inspection reports; the PM and maintenance
  history; the document list.
- A big export runs in the background and shows up under **Exports**, emailed
  to whoever asked. PDFs are made with pdf-lib and Excel with exceljs.

### 8.7 Fuel card and integration hub

**Fuel card data sync**

- **First, CSV import:** upload the card company's export, map its columns
  once (saved per provider), and the import de-duplicates and matches card →
  asset (or the unit number typed at the pump). Unmatched rows go to a queue.
- **Then, if the card offers it, automatic:** the provider's API or a
  scheduled export (Phase 0, question 4).
- Worked out from it: gallons, $, $/gal, MPG between fills (the odometer
  entered at the pump, else the nearest reading), and fuel $/mile per asset.
  Flags: more gallons than the tank holds, the wrong product (diesel into a
  gas unit), two fills in a day, fills on non-workdays. A pump odometer
  becomes a meter reading (`source: fuel`).

**Telematics connectors**

- There is one interface (`listVehicles`, `readingsSince`, `faultsSince`,
  `lastLocation`) and one implementation per provider: Motive, Samsara,
  Geotab. **Build only the one DB actually has** (Phase 0, question 5).
- Vehicles are matched by VIN. Data comes in hourly (Vercel Pro), or by
  webhook where the provider has one. The Asset Hub can check webhook
  signatures, which Apps Script can't (part of D2).
- Odometer and engine hours become meter readings (`source: telematics`) and
  drive PM.
- A new fault code (DTC) becomes a `dtc_events` row and opens a defect
  (`source: telematics`). A check-engine light is a defect, and a Manager can
  raise it to out of service. A cleared code is noted on the defect but
  doesn't resolve it; a person does.
- Location shows on the asset's card as "last seen" with a map link. Trips make
  compliance exact (§6.8).
- The integrations page shows the last sync, the last error and the matched
  and unmatched vehicles. Keys live only in env vars.

---

## 9. Advanced modules (the add-ons)

### 9.1 Shop Ops (Phase 10)

- **Mechanic scheduling grid:** a week view with rows for each mechanic (plus
  Outside shops) and a column per day. WO cards are sized by estimated hours
  and dragged in from an Unscheduled tray. Each mechanic has a daily capacity
  (8 h, a setting), and an overbooked day turns red.
- **Technician labor clock:** the §7.3 timer, reported per WO and per mechanic
  per day. Utilization is wrench time ÷ clock time, with clock time read from
  JobTread. It's a number for Carl, not payroll.
- **Cost-based approval limits:** a limit per person, over the level default
  (§6.6). An over-limit WO waits in Pending approval with "needs someone with a
  $X limit". The approval log is kept.
- **Quotes and invoices:** from a WO, a **Quote** before the work (estimated
  labor at the bill rate, parts at average cost plus markup, vendor costs
  passed through, and a tax setting), PDF numbered `Q-1001`. After completion,
  an **Invoice** from the actuals, `INV-1001`. Status runs draft / sent / paid,
  against a bill-to list. Handing invoices to JobTread or accounting waits for
  Phase 0, question 8.

### 9.2 FleetAI (Phase 12)

| Task | Reads | Answers | Shows up | A person… |
| --- | --- | --- | --- | --- |
| **Photo check** | the required and defect photos on an inspection | possible damage, with where in the photo and how sure | a ⚑ on the inspection; a "FleetAI saw" panel | confirms (opens a defect) or dismisses |
| **Defect triage** | the defect's note (EN and as said), photos, asset | category, suggested severity, "probably the same as open defect #n", an English title | chips on the defect queue | accepts or changes |
| **Document reader** | an invoice, receipt or quote (PDF or photo) | vendor, date, invoice #, lines (description, qty, unit, total, matching part), tax, total | pre-fills the WO's file panel and Parts → Receive | confirms the lines; then they become costs and stock |
| **Meter reader** | a dash or hour-meter photo | the reading, and how sure | flags the inspection if it disagrees with what was typed | reviews |
| **Routing** | a new WO | a suggested assignee (mechanic or shop) from the category and history; title and description in English and Spanish | pre-fills the WO form | accepts or changes |
| **Translate** | crew notes, checklist labels | English, or Spanish | everywhere | |

The rules:

- It runs **after the record lands** (`after()`), never in the phone's path. A
  slow or failed AI call never delays a send.
- Every answer is checked against a JSON schema (Zod). Anything else (bad
  JSON, a refusal, a timeout) means no suggestion, and that is logged.
- **No automatic writes** (D7). If a task's measured accept rate is high
  enough, say 95% over 200 runs, Carl can switch that one task to apply on its
  own. That is a setting, off by default.
- Every call is a row in `ai_runs`: provider, model, prompt version, time,
  tokens, cost and what the person did. The FleetAI settings page shows the
  accept rate per task and the month's spend. `AI_MONTHLY_CAP_CENTS` pauses it
  when reached, and nothing else breaks.
- **The provider is picked by testing, first thing in Phase 12.** Build a test
  set from DB's own data with known answers: about 50 defect photos, 20 real
  vendor invoices and receipts, and 30 meter photos. Run each candidate and
  score accuracy, cost and speed per task. The candidates are **Gemini** (DB
  CheckOut already holds a key for translation, and its `translate.ts`
  discovers the current model rather than hard-coding one) and **Claude** (the
  Anthropic API through the official `@anthropic-ai/sdk`, starting with
  `claude-opus-5-5`, which reads images and PDFs and can answer in a fixed JSON
  schema). The provider can differ per task. Models go in env vars
  (`AI_MODEL_<TASK>`), never in code, because providers retire models on a
  rolling basis.
- **Cost sense:** at DB's volume (tens of inspections a day, a few invoices a
  week), expect tens of dollars a month even on a top model. The test run
  measures the real figure before anything is switched on.
- **What goes out:** only the photo or document and the least text the task
  needs. No names beyond the first name already burned into the stamp.

---

## 10. The phases

| # | Phase | Repos | Size | People can… |
| --- | --- | --- | --- | --- |
| 0 | Gather and decide | none (Carl) | Carl | |
| 1 | Foundation | Asset Hub, DB Hub | M | sign in, load the assets, print stickers |
| 2 | Checklists and inspections | Asset Hub, DB Crew | L | do daily checks from their phones |
| 3 | Defects | Asset Hub, DB Crew | M | fail an item and put an asset out of service |
| 4 | Work orders and mechanics | Asset Hub, DB Crew | L | close the repair loop |
| 5 | Dashboard | Asset Hub | M | run the fleet from the desk: **pilot starts** |
| 6 | Preventive maintenance | Asset Hub | M | let service schedule itself |
| 7 | Wallet | Asset Hub, DB Crew | S | show documents at a roadside stop |
| 8 | Parts | Asset Hub, DB Crew | M | count the shelf down automatically |
| 9 | Analytics and reports | Asset Hub | L | see cost and hand an auditor a packet |
| 10 | Shop Ops | Asset Hub, DB Crew | M | schedule mechanics, approve by limit, invoice |
| 11 | Fuel and telematics | Asset Hub | M each | stop typing meters, see fuel and fault codes |
| 12 | FleetAI | Asset Hub | M | get a second pair of eyes |

Size is relative (S < M < L), not a promise of days.

### Phase 0: Gather and decide (Carl)

Answer these and put the answers in this file under §2 or the phase they
affect:

1. **The asset list.** Every truck, trailer, piece of equipment, power tool,
   ladder and fall-protection kit worth tracking, in the Appendix B sheet.
   Where does it live today?
2. **CMVs.** Which units are commercial motor vehicles (a GVWR or combined
   rating of 10,001 lb or more; a pickup with a loaded dump trailer often
   counts)? What is the USDOT number? Who is the safety or insurance contact
   who confirms?
3. **Who fixes things.** The in-house mechanic(s): names and Google accounts.
   They also need DB Crew, which means a JobTread membership. The outside
   shops: name, phone, email.
4. **Fuel card.** Which company? Can its portal export transactions as CSV, or
   does it offer an API or a scheduled export?
5. **Telematics.** GPS on any vehicle? Which provider (Motive, Samsara, Geotab,
   other, none)?
6. **Approval limit.** The dollar figure above which a WO needs approval
   (default $500), and who approves.
7. **Email.** Who gets out-of-service alerts, the morning digest and approval
   requests?
8. **Billing out.** Is a repair ever billed to someone (a job, a sister
   company)? To whom, and at what labor rate and markup? If never, Shop Ops
   skips invoices.
9. **The documents.** Registration, insurance card, permits and annual
   inspection report for each vehicle, scanned or photographed.
10. **Sticker stock.** Outdoor laminated vinyl labels or a label printer. Pick
    after printing a test sheet in Phase 1.
11. **The brand.** The DB design system (§4.11: navy, electric green, Archivo,
    Barlow, IBM Plex Mono, Lucide icons) is the starting point. Confirm it,
    and send the logo as SVG and the wordmark's real font files if you have
    them.

### Phase 1: Foundation

**Carl's part (as the Vercel owner and operations@):**

- Create the Vercel project `db-asset-hub` from `bledsoecw/DB-Asset-Hub`
  (framework Next.js, Node 24.x), with Vercel Authentication on everything
  except custom domains, and add the domain `assets.deitemeyerbrothers.com`.
- Storage: create a Neon database for the project (turn on a branch per
  preview), and create a **private** Blob store and connect it.
- Google Cloud: an OAuth web client for the desk sign-in, with authorized
  origin `https://assets.deitemeyerbrothers.com` (plus the preview domain if
  wanted).
- Fill in the Phase 1 env vars (§4.9).

**Build: Asset Hub**

- **The design system and the app shell first** (§4.11): the DB tokens as CSS
  variables and the Tailwind theme; shadcn/ui themed with them; the shell
  (sidebar, toolbar, the phone's bottom bar); the standard table, form,
  dialog, toast, and empty, loading and error states; DB-branded sign-in,
  favicon, email and PDF templates; and `/design`, the living style guide.
- Next.js (App Router) with strict TypeScript, Drizzle, and the first
  migration: `people`, `teams`, `settings`, `audit_log`, `asset_categories`,
  `assets`, `asset_status_log`, `meter_readings`, `files`.
- Sign-in: Google, domain plus allow-list. Copy DB CheckOut's `auth.ts` and its
  tests. A 30-day session cookie (httpOnly, Secure, SameSite=Lax).
- Levels (§4.3): the DB Hub feed, a five-minute cache, the last good copy,
  `ASSET_HUB_ADMINS`. Then `/whoami` and `/api/health`.
- Assets: list (search, filters), card, create, edit, retire, and **CSV
  import** (Appendix B) with a dry run that lists every problem before writing
  anything.
- Stickers: the `/q/[tag]` page, and a sticker-sheet PDF for the selected
  assets (pdf-lib + qrcode), with the layout set for the stock Carl picks.
- `audit_log` on every write.
- `docs/CREW-API.md`, copied from Appendix C. From here on it is the contract.

**Build: DB Hub** (its own branch and PR)

- Add `{ key: 'assetHub', col: 'Asset Hub', label: 'DB Asset Hub',
  options: ['', 'View', 'Mechanic', 'Manager', 'Admin', 'Off'], hint: … }` to
  `ACCESS_APPS_`, its onboarding task in `ACCESS_TASK_MAP_` and the seeds
  (`?addtasks=1` appends it to the live sheet), and bump `HUB_BUILD`.
- Ship per its `CLAUDE.md`: `clasp push -f`, then `clasp deploy -i` the **live
  web app** deployment. Then **the feed deployment gets a new version in the
  editor, as operations@, Who has access: Anyone. Never `clasp deploy -i` the
  feed.** Prove it with the `?accessfeed=1&probe=…` check in that file, then
  confirm the feed JSON now carries `assetHub` for each person.

**Done when**

- Carl has approved the shell and `/design` on a laptop and a phone, in the DB
  brand, before any feature is built on them. The asset list uses the
  standard table: search, filters, saved views, the row menu.
- Carl signs in at `assets.deitemeyerbrothers.com`, and `/whoami` shows Admin
  (seeded) and the feed's level.
- A Gmail address not on the allow-list is refused. Setting someone's Asset Hub
  column to Off refuses them within five minutes.
- The asset sheet imports, with the dry run listing duplicate tags and unknown
  categories before anything is written.
- A sticker sheet prints, and a phone's camera on a sticker opens
  `/q/<tag>`.
- `npm test`, typecheck and lint are green, and the README says how to run it.

**Kickoff prompt**

> Phase 1 of DB Asset Hub. Read `PLAYBOOK.md` in `bledsoecw/DB-Asset-Hub`
> (the rules, §2–§6 including §4.11, Phase 1 and Appendices B and C), the DB
> design system in `bledsoecw/db-crew-app` under `project/_ds/`, and
> `CLAUDE.md` in `bledsoecw/DB-Hub`. Build Phase 1 in DB-Asset-Hub, and the `assetHub` access
> column in DB-Hub, each on its own branch with a pull request. Tests as §4.10
> says. Don't deploy anything; list the deploy steps for Carl at the end.

### Phase 2: Checklists and inspections

**Build: Asset Hub**

- Migrations: `checklists`, `checklist_versions`, `checklist_targets`,
  `inspections`, `inspection_answers`.
- The checklist builder (§8.4), and the Appendix A checklists as seeds.
- The door (§4.4): `CREW_APP_SECRET`, the `X-Acting-*` headers, levels, and
  idempotency on `X-Client-Ref`. Routes: `boot`, `assets/:tag`, `photos`,
  `inspections`.
- `src/domain`: taking an inspection in (§6.2, without defects yet; a failed item
  is stored as an answer) and meters (§6.3), with tests.
- Desk: the inspections list and detail (the first form of the feed).

**Build: DB Crew**

- Script: `asBoot`, `asAsset`, `asPhoto`, `asInspect` over an `asFetch_` copied
  from `coFetch_`; Script Properties `ASSET_HUB_URL` and `ASSET_HUB_SECRET`;
  the level gate; cases in `code-test.mjs`.
- PWA: the Equipment tab for every role, in the DB brand tokens (§4.11),
  hidden until `ASSET_HUB_URL` is set; the
  boot pack cache; the scanner (`BarcodeDetector`, vendored jsQR, typed tag);
  the asset card; the checklist runner for every item type; camera-only
  required photos with the stamp; meters and the meter photo; the signature
  pad; outbox order (photos, then the inspection); EN/ES strings, English
  first;
  `dev/mock.js` additions; `dev/equipment-test.mjs`.

**Done when**

- On a real Android phone **and** a real iPhone: scan TRL-03's sticker from the
  Equipment tab, do the 10-point check in airplane mode, turn airplane mode off,
  and the inspection lands on the desk with its stamped photos within a
  minute.
- The tire item can't be passed with a gallery photo. There's no button, and a
  forced call is refused with 400 and the reason.
- Sending the same inspection twice creates one.
- A checklist edited and re-published leaves old inspections showing the old
  wording.
- Domain, route, `code-test.mjs` and `equipment-test.mjs` tests are green.

**Kickoff prompt**

> Phase 2 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §4.4–§4.6, §4.11, §5, §6.2,
> §6.3, §7.1, §8.4, Phase 2, Appendices A and C) and `docs/CREW-API.md` in
> `bledsoecw/DB-Asset-Hub`, and Close Out in `bledsoecw/db-crew-app`
> (`coFetch_` in `apps-script/Code.gs`, its tab in
> `dbtimeclock-pwa/public/index.html`, `dev/closeout-test.mjs`): the Equipment
> tab follows the same patterns. Build Phase 2 in both repos, one branch and
> PR each, with tests. No deploys.

### Phase 3: Defects

**Build: Asset Hub**

- Migrations: `defects`, `acknowledgments`, `alerts`.
- `src/domain`: asset status (§6.1) and the defect half of §6.2, including
  repeats and severity, with tests. Status is recomputed in the same
  transaction as every defect change.
- Routes: `inspections` now opens defects; `defects` (report a problem);
  `acknowledgments`; `translate` (from DB CheckOut's `translate.ts`,
  `GEMINI_API_KEY`).
- Desk: the open-defects queue, dismiss with a reason, put out of / return to
  service, the bell.
- Email: the Gmail sender (§4.8) and the instant out-of-service email;
  `CRON_SECRET` and the daily cron skeleton.

**Build: DB Crew**

- The defect sheet: up to six photos, gallery with the PHONE badge, the markup
  editor, dictation with the English preview (`asTranslate`), "safe to use?".
- Status banners, Report a problem, and the acknowledgment step on the
  pre-trip.

**Done when**

- FIX on tires with "not safe" puts TRL-03 out of service on the desk within
  15 seconds of the phone sending. A second phone scanning it sees the red
  banner, and the email arrives.
- Dismissing that defect on the desk turns TRL-03 Safe.
- A second report of the same item makes the repeat count 2 and opens no new
  defect.
- A marked-up photo and its original are both stored.
- Spanish dictation shows its English before sending.
- The next driver is asked to acknowledge once a defect is repaired (with a
  test repair).

**Kickoff prompt**

> Phase 3 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §4.6, §4.8, §6.1,
> §6.2, §7.1's acknowledgment, §7.2, §8.2's defect queue, Phase 3) and
> `docs/CREW-API.md`. Build Phase 3 in `bledsoecw/DB-Asset-Hub` and
> `bledsoecw/db-crew-app`, one branch and PR each, with tests. No deploys.

### Phase 4: Work orders and mechanics

**Build: Asset Hub**

- Migrations: `work_orders`, `wo_events`, `wo_labor`, `wo_lines`, `vendors`.
- `src/domain`: WO states (§6.5) and approvals at level limits (§6.6), with
  tests.
- Desk: the defect → WO converter, dispatch (mechanic or shop, Email the shop
  with the WO sheet PDF), the kanban (dnd-kit), the drawer, and the file
  aggregator (Blob client uploads).
- Routes: `my-repairs`, `work-orders/:id`, `timer`, `parts` (free-text lines
  until Phase 8), `notes`, `sign-off`.

**Build: DB Crew**

- My repairs (Mechanic+): the list, the WO screen, the timer, notes, after
  photos under the AFTER rule, and the sign-off with each defect's outcome and
  a signature. "Back in service" shows only on the server's answer.

**Done when**

- Two defects on TRK-07 become one WO, assigned to the in-house mechanic, and
  it appears on their phone. They run the timer for 20 minutes, take an after
  photo and sign. The WO is Completed, both defects are Repaired, TRK-07 is
  Safe, and its history shows who, when and the signature.
- A shop WO completed on the desk, with the shop's invoice PDF dropped on the
  card, adds its amount to the WO's cost.
- Dragging Pending approval → Completed is refused with the reason.
- A Manager's $800 WO waits for an Admin while the limit is $500.

**Kickoff prompt**

> Phase 4 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §5's work orders,
> §6.5, §6.6, §7.3, §8.2, Phase 4) and `docs/CREW-API.md`. Build Phase 4 in
> `bledsoecw/DB-Asset-Hub` and `bledsoecw/db-crew-app`, one branch and PR
> each, with tests. No deploys.

### Phase 5: Dashboard (then the pilot)

**Build: Asset Hub**

- The tiles, the live feed (a 15-second poll), the leaderboards (§6.8 using
  JobTread clock days through `JT_GRANT_KEY`, one cached query per range), the
  worst assets, the bell, and the morning digest.
- Suspicious-inspection flags made visible (feed, inspection, a leaderboard
  column).

**Done when**

- The tiles match a hand count on the seeded data.
- A phone's inspection shows in the feed within 15 seconds.
- A test person with 5 days on the clock in JobTread and 4 inspections shows
  80%.
- With JobTread unreachable, the leaderboard says "clock days unavailable" and
  the rest of the dashboard works.

Then **the pilot** (§11).

**Kickoff prompt**

> Phase 5 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §4.7, §4.8, §6.8,
> §8.1, Phase 5) and DB Crew's `JOBTREAD-NOTES.md` (time entries) in
> `bledsoecw/db-crew-app`. Build Phase 5 in `bledsoecw/DB-Asset-Hub` on a
> branch with a PR, with tests. The JobTread read is read-only: no writes of
> any kind. No deploys.

### Phase 6: Preventive maintenance

**Build:** `pm_schedules` and `pm_baselines`; §6.4 with tests (each trigger,
whichever first, the windows, stale meters, the first baseline); the schedules
page, each asset's Maintenance panel and the seeds (§8.3); the daily cron
computing states, opening and clearing alerts and auto-creating WOs; a
WO completion or an inspection resetting the baseline.

**Done when**

- A truck 4,600 mi past its last oil change shows Due soon (500 mi window); at
  5,000 it shows Overdue and one email goes out.
- Completing the linked WO resets it.
- A generator runs on hours and a ladder on days, the ladder needing an
  inspection rather than a WO.

**Kickoff prompt**

> Phase 6 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §4.7, §6.3, §6.4,
> §8.3, Phase 6). Build it in `bledsoecw/DB-Asset-Hub` on a branch with a PR,
> with tests. No deploys.

### Phase 7: Wallet

**Build:** `asset_documents`; desk upload with pdf.js page images, expiry
dates and the `in_wallet` toggle; expiry alerts in the daily cron. In DB Crew:
`asDoc`, the Documents list on the asset's card, Show the officer, and the
offline cache (§7.4).

**Done when**

- In airplane mode, opening TRK-07 shows its registration and insurance card
  full screen.
- A document expiring in 25 days alerts the desk once.

**Kickoff prompt**

> Phase 7 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §4.5, §4.6, §7.4,
> Phase 7) and `docs/CREW-API.md`. Build it in `bledsoecw/DB-Asset-Hub` and
> `bledsoecw/db-crew-app`, one branch and PR each, with tests. No deploys.

### Phase 8: Parts

**Build:** `parts` and `part_moves`; §6.7 with tests; the shelf, Receive,
Adjust/Count and history; parts on WOs from the desk and the phone (replacing
the free-text line); low-stock alerts.

**Done when**

- Using 2 air filters on a WO takes on hand from 5 to 3 and adds 2 × the
  average cost to the WO. Crossing the reorder point alerts once.
- Using one more than is on hand works, with "count needed" set.

**Kickoff prompt**

> Phase 8 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §6.7, §7.3's parts,
> §8.5, Phase 8) and `docs/CREW-API.md`. Build it in `bledsoecw/DB-Asset-Hub`
> and `bledsoecw/db-crew-app`, one branch and PR each, with tests. No deploys.

### Phase 9: Analytics and reports

**Build:** `fixed_costs`, `dashboards` and `exports`; TCO (§6.9) with tests; the
TCO page; the dashboard builder with the §8.6 templates; the exporter (CSV,
Excel, the PDF packet) running in the background, with the Exports page.

**Done when**

- One asset's TCO equals a hand sum of its WOs, fuel and fixed costs for the
  range.
- TRK-07's three-month DOT packet has every DVIR with its signature and photos
  and every repair sign-off.
- A dashboard Carl builds is still there after signing out and in, and a
  shared one shows for the office.

**Kickoff prompt**

> Phase 9 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §6.9, §8.6, §12,
> Phase 9). Build it in `bledsoecw/DB-Asset-Hub` on a branch with a PR, with
> tests. No deploys.

### Phase 10: Shop Ops

**Build:** the scheduling grid; per-person approval limits and labor/bill rates
(people and limits in Settings); utilization (wrench time from `wo_labor`,
clock time read from JobTread); `quotes_invoices` with the PDFs (§9.1).

**Done when**

- Dragging a WO onto Tuesday schedules it, and a 10-hour Tuesday shows red.
- A $700 WO from a Manager with a $1,000 personal limit is approved on
  creation.
- An invoice PDF from a completed WO matches its lines and markup.

**Kickoff prompt**

> Phase 10 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §6.6, §9.1, Phase
> 10, and Phase 0's answer on billing out). Build it in
> `bledsoecw/DB-Asset-Hub` on a branch with a PR, with tests. JobTread is read
> only. No deploys.

### Phase 11: Fuel and telematics

**Build:** `fuel_tx`, the CSV import with column mapping and the unmatched
queue, the fuel metrics and flags; then the provider's API if Phase 0 found
one. `dtc_events`, `integrations`, the telematics interface and the **one**
provider DB uses: VIN matching, hourly readings, faults → defects, the
webhook route with signature checks, and the integrations page (§8.7).

**Done when**

- A month's fuel export imports twice with no duplicates, and every card
  matches an asset or sits in the queue.
- MPG for a truck matches a hand calculation.
- A test fault code opens one defect, and the next pull's odometer moves that
  truck's PM.

**Kickoff prompt**

> Phase 11 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, §6.3, §6.8, §8.7,
> Phase 11, and Phase 0's answers on fuel and telematics). Build it in
> `bledsoecw/DB-Asset-Hub` on a branch with a PR, with tests. Use the
> provider's official API documentation, and put keys only in Vercel env vars.
> No deploys.

### Phase 12: FleetAI

**Build:** first the test set and the provider comparison (§9.2), with a
written result in this file. Then `ai_runs`, the provider interface and the
chosen provider per task, the six tasks, their suggestion UIs, the FleetAI
settings page (accept rates, spend, cap), and moving translate onto the same
interface.

**Done when**

- The comparison is written up with accuracy, cost and time per task, and
  Carl has picked.
- A photo of a bulging sidewall that was marked OK gets a ⚑ on the desk
  within a minute.
- A real vendor invoice pre-fills a WO's lines correctly, and nothing is
  posted until a person confirms.
- Pulling the AI key leaves every flow working, with no suggestions.

**Kickoff prompt**

> Phase 12 of DB Asset Hub. Read `PLAYBOOK.md` (the rules, D7, §9.2, Phase
> 12). Start with the provider comparison on the test set Carl provides and
> write the result into `PLAYBOOK.md` before building the tasks. Build in
> `bledsoecw/DB-Asset-Hub` on a branch with a PR, with tests. No deploys.

---

## 11. Rolling it out to the crew

- **Pilot (after Phase 5, two weeks):** Carl, the service crew, one install
  crew's truck and trailer, and the shop. Only those assets get stickers. It
  succeeds with at least 90% of owed pre-trips done, no lost inspections, and
  the crew's changes made.
- **Stickers:** one place per category so nobody hunts: the driver's door jamb
  on trucks, the tongue on trailers, the handle or frame on equipment, the
  label pouch or a tag on a harness. Use durable outdoor labels, and redo any
  that won't scan.
- **Training:** a ten-minute tailgate demo, in English and again in Spanish
  for whoever wants it (showing the ES·EN pill), and a one-page card (EN/ES):
  *Scan → Check → Send / Escanear → Revisar → Enviar*. In the first
  week the office checks the live feed every morning and calls whoever is
  missing.
- **Go-live:** every asset stickered and compliance reviewed weekly. Paper DVIR
  books are retired after two clean weeks, but each CMV keeps a paper pad for a
  dead phone.
- **Measure monthly:** compliance %, out-of-service days, average repair
  turnaround, PM on-time %, and cost per mile.

---

## 12. DOT and OSHA notes

These are the rules the design keeps in mind. **Confirm with DB's safety or
insurance contact which apply to which units** (Phase 0, question 2). `is_cmv`
on each asset decides which ones need the DVIR flow.

| Rule | What it asks | How the Asset Hub covers it |
| --- | --- | --- |
| 49 CFR 396.11 | a driver vehicle inspection report listing defects that affect safety, signed by the driver; the carrier certifies the repair (or that none was needed) before the vehicle is used again; keep the report, the certification and the next driver's review for 3 months | DVIR checklists with a signature; defects; the mechanic's or manager's sign-off as the certification; nothing deleted (D9) |
| 49 CFR 396.13 | before driving, review the last report and sign that the repairs were done | the acknowledgment step (§7.1) |
| 49 CFR 396.3 | inspection, repair and maintenance records per vehicle; kept a year, and 6 months after it leaves the fleet | WO, PM and inspection history; assets are retired, not deleted |
| 49 CFR 396.17 / 396.21 | a periodic (annual) inspection; keep the report 14 months | a 365-day PM schedule plus the `annual_inspection` document kind |
| OSHA 1926.502(d)(21) | personal fall arrest systems inspected before each use | the fall-protection checklist, each use; any failed item is out of service |
| OSHA 1926.1053(b)(15) | ladders inspected periodically and after anything that could affect safe use | the ladder checklist and a 90-day PM |

396.11 asks for the report at the end of each day's work. Most fleets run the
same checklist as a pre-trip, and a problem found during the day goes in
through Report a problem. Ask the safety contact whether DB also needs a
post-trip. If so, it is one more checklist with `purpose: posttrip`, and no
code changes.

---

## 13. Risks and how the plan handles them

| Risk | Plan |
| --- | --- |
| The crew doesn't use it | it's in the app they already have, English first with Spanish one tap away, a check takes about a minute, the leaderboards, and a pilot first |
| No signal | the outbox, the cached boot pack, documents on the phone |
| Pencil-whipping | camera-only required photos, the stamp, the fingerprint, timing, meter checks, and later FleetAI's photo check |
| iPhone's camera app opens Safari, not DB Crew | teach the in-app Scan button; tags are typeable |
| DB Hub's feed down | last good copy, then defaults; seeded admins |
| The Apps Script hop is slow | reads come from the phone's cache first; writes are queued; the desk doesn't use the hop at all |
| Two sources of truth for status | one function (§6.1), recomputed from the open defects every time |
| Neon free plan compute | watch the project's usage page and move to a paid plan if it runs short; records are small and photos aren't in it |
| Vercel plan limits crons | the daily fallback (§4.7) |
| AI gets it wrong | suggestions only, measured, with a spend cap |
| This is a big build | each phase ships something usable, the pilot comes at Phase 5, and you can stop after any phase |
| Typing in the asset list and documents | CSV import with a dry run; documents photographed from a phone and uploaded on the desk |

---

## Appendix A: seed checklists

Starting points that Carl edits in the builder. **OOS** means a failed item (FIX)
puts the asset out of service, and *photo* means a camera photo is required.

**A1. Truck: DOT pre-trip (DVIR)**, for CMVs, daily, signature and meters required
1. Service brakes and trailer brake connections (OOS)
2. Parking brake (OOS)
3. Steering (OOS)
4. Lights and reflectors: headlights, brake, turn, marker
5. Tires: tread, pressure, sidewalls, all positions (OOS, *photo*)
6. Wheels, rims and lug nuts (OOS)
7. Horn
8. Windshield and wipers
9. Mirrors
10. Coupling: hitch, pin, chains, breakaway (OOS, *photo* when towing)
11. Emergency equipment: fire extinguisher, triangles
12. Leaks under the vehicle: oil, coolant, fuel
13. Seat belts
14. Load secured
15. Odometer (meter, *photo*)

The first eleven are the components 49 CFR 396.11 names. The rest are DB's.

**A2. Roofing trailer: 10-point**, daily when used
1. Coupler latched and pinned (OOS, *photo*)
2. Safety chains crossed and attached (OOS)
3. Breakaway cable and battery (where fitted) (OOS)
4. Lights: brake, turn, running
5. Tires: tread, pressure, sidewalls (OOS, *photo*)
6. Lug nuts present and tight (OOS)
7. Brakes / brake controller response (OOS)
8. Jack and stands up and stowed
9. Load secured and tarped (shingles, debris)
10. Deck, gate latch, dump hydraulics where fitted

**A3. Portable generator: 5-point**, each use
1. Oil level
2. Fuel level, no leaks (OOS if leaking)
3. Cords, outlets and GFCI undamaged (OOS)
4. Hour meter (meter, *photo*)
5. Starts and runs without unusual noise

**A4. Air compressor**, each use: tank drained; hoses and fittings; safety valve
(OOS); belt guard in place (OOS); oil; hour meter.

**A5. Pneumatic nailer**, each use: safety contact tip works (OOS); no air
leaks; depth adjust; magazine and feed; fitting.

**A6. Ladder**, before use, plus the 90-day PM: rails and rungs (OOS); feet
(OOS); locks and spreaders (OOS); labels legible; nothing hiding damage (paint,
tar).

**A7. Fall protection: harness, lanyard or SRL, anchor**, before each use;
every failed item is OOS: webbing and stitching; D-rings, buckles and hardware;
lanyard or SRL locks and retracts; fall indicator not tripped; labels legible;
roof anchor sound.

---

## Appendix B: the asset import sheet

One row per asset. The importer's dry run checks every row before anything is
written.

| Column | Example | Notes |
| --- | --- | --- |
| `tag` | `TRL-03` | unique. Suggested prefixes: TRK truck, TRL trailer, EQ equipment, TL power tool, LAD ladder, FP fall protection, SHOP shop |
| `name` | `16' dump trailer` | |
| `category` | `Dump trailer` | must exist, or be listed in the categories sheet |
| `team` | `Roofing` | |
| `make`, `model`, `year` | `Big Tex`, `14LP`, `2021` | |
| `vin_serial` | | VIN for vehicles and trailers, serial for equipment |
| `plate`, `plate_state` | `ABC1234`, `OH` | |
| `gvwr_lbs`, `is_cmv` | `14000`, `yes` | §12 |
| `odometer`, `engine_hours` | `84212`, | the starting readings |
| `assigned_to_email` | | the usual driver, for compliance |
| `purchase_date`, `purchase_price`, `in_service_date`, `expected_life_months` | | for TCO |
| `fuel_card_ref`, `telematics_ref`, `tank_gallons`, `fuel_type` | | Phase 11 |
| `notes` | | |

---

## Appendix C: the crew API (draft of `docs/CREW-API.md`)

Every route is under `https://assets.deitemeyerbrothers.com/api/crew` and is
called only by DB Crew's Apps Script, with the headers and answers in §4.4.
Times are ISO 8601 with the phone's offset, and the server also records when
each item arrived. A file is always sent with `POST /photos` first and named by
its `photoRef` (the client ref it was sent with).

| Route | Level | Sends → gets back |
| --- | --- | --- |
| `GET /boot` | any | → `{ me {email, name, level}, assets[], checklists[], categories[], settings{}, myRepairs, at }` |
| `GET /assets/:tag` | any | → `{ asset, status, openDefects[], lastInspection, checklists[], pm[], documents[], ackNeeded[] }` |
| `POST /photos` | any | `{ purpose, assetTag, imageBase64, thumbBase64, source: camera\|phone, takenAt, stamped, annotatedOf?, lat?, lng?, woId? }` → `{ photoRef, fileId }` |
| `POST /inspections` | any | `{ assetTag, checklistVersionId, startedAt, submittedAt, answers[{ key, value, na, comment, photoRefs[] }], meters { odometer?, hours?, photoRef?, replaced? }, defects[{ key, safe, noteSaid, noteEn, lang, photoRefs[] }], signatureRef?, lat?, lng? }` → `{ inspectionId, result, asset { status, since }, defects[{ id, repeat }] }` |
| `POST /defects` | any | `{ assetTag, title, safe, noteSaid, noteEn, lang, photoRefs[] }` → `{ defectId, repeat, asset { status } }` |
| `POST /acknowledgments` | any | `{ assetTag, defectIds[], signatureRef }` → `{ ok }` |
| `POST /translate` | any | `{ texts[], to: en\|es }` → `{ texts[] }` (at most 100 strings of 4,000 characters, Close Out's limits) |
| `GET /documents/:id` | any | → `{ title, kind, expiresOn, pages[{ imageBase64 }] }` |
| `GET /my-repairs` | Mechanic+ | → `{ workOrders[] }` |
| `GET /work-orders/:id` | Mechanic+ | → `{ workOrder, asset, defects[], parts[], labor, files[], events[] }` |
| `POST /work-orders/:id/timer` | Mechanic+ | `{ action: start\|pause, at }` → `{ running, minutes }` |
| `POST /work-orders/:id/parts` | Mechanic+ | `{ partId? , text?, qty }` → `{ line, onHand?, warning? }` |
| `POST /work-orders/:id/notes` | Mechanic+ | `{ noteSaid, noteEn, lang }` → `{ ok }` |
| `POST /work-orders/:id/sign-off` | Mechanic+ | `{ resolutions[{ defectId, outcome: repaired\|not_needed, note }], afterPhotoRefs[], meters {}, note, signatureRef }` → `{ workOrder { status }, asset { status } }` |
| `GET /parts?q=` | Mechanic+ | → `{ parts[] }` |

On the DB Crew side, each route is a one-line function over `asFetch_`:
`asBoot`, `asAsset`, `asPhoto`, `asInspect`, `asDefect`, `asAck`,
`asTranslate`, `asDoc`, `asMyRepairs`, `asWorkOrder`, `asTimer`, `asPart`,
`asNote`, `asSignOff`, `asParts`. They are registered in `doPost`'s `WITH_USER`
table, so the person is always the one resolved from the verified token.
