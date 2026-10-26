# DB Asset Hub

Deitemeyer Brothers' fleet and equipment app, and our own take on Whip Around:
daily inspections of the trucks, trailers, equipment, tools and fall
protection from the crew's phones; defects that put an asset out of service on
the spot; work orders a mechanic signs off on a phone; preventive maintenance
that schedules itself; the parts shelf; the roadside documents; and a desk
dashboard for the whole fleet.

**Status (26 Oct 2026): planned, not built.** Start with
**[`PLAYBOOK.md`](PLAYBOOK.md)**. It holds the decisions, the architecture, the
data, the rules, every feature, and the phases that build it, each with
"done when" checks and a kickoff prompt.

## Two halves

| Half | Who | Where |
| --- | --- | --- |
| Field | drivers, crews, mechanics | an **Equipo / Equipment** tab in DB Crew (`bledsoecw/db-crew-app`, `db-crews.web.app`) |
| Desk | office, fleet manager, owners, shop | this repo: Next.js on Vercel at `assets.deitemeyerbrothers.com`, Neon Postgres, private Vercel Blob |

People and access levels come from DB Hub's App access panel (`bledsoecw/DB-Hub`,
the **Asset Hub** column). The phone reaches this app through DB Crew's Apps
Script, the same way Close Out reaches the DB CheckOut server.
