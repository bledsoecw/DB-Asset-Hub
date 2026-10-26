# DB Asset Hub: working notes

## Start here

`PLAYBOOK.md` is the plan: the decisions (§2), the architecture (§4), the data
(§5), the rules (§6), and the phases (§10). Work the phases in order and follow
its "Rules for every build session". When a decision changes, change the
playbook in the same pull request, with the date and who decided.

## Shipping is different here

Once the Vercel project `db-asset-hub` is connected (Phase 1), **merging to
`main` deploys production** at `assets.deitemeyerbrothers.com`. That is unlike
DB Hub and DB Crew, where pushing to GitHub deploys nothing. So every change
goes on a branch with a pull request, and nothing merges without Carl.

## The other repos this touches

- `bledsoecw/db-crew-app`: the phone half (the Equipo tab, the `as*`
  forwarders in `apps-script/Code.gs`). Its deploy steps are in
  `apps-script/README.md` and `dbtimeclock-pwa/SETUP.md`.
- `bledsoecw/DB-Hub`: people and access levels (the `assetHub` column). Read
  its `CLAUDE.md` before touching it. **Never `clasp deploy -i` its feed
  deployment.**
- `bledsoecw/DB-CheckOut`: `apps/sync/src/auth.ts` and `translate.ts` are the
  starting points to copy. Nothing in that repo changes.

Carl works on Windows (PowerShell), as with the other DB repos, so commands in
chat should be written for that unless Carl says otherwise.
