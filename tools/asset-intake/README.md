# Asset List intake

Gathers `PLAYBOOK.md` Phase 0, question 1: every truck, trailer, piece of
equipment, power tool, ladder, fall-protection kit and company computer,
tablet and phone, with the Appendix B fields. Two ways to fill it in, with the
same questions:

- **Online:** a Google Form (phone, tablet or computer). Responses land in a
  Google Sheet. Built by `AssetListForm.gs`.
- **Paper:** `asset-list-printable.pdf`. Page 1 is the instructions, page 2 is
  one record per piece of equipment (print one per vehicle, trailer or
  machine), page 3 lists tools and page 4 lists technology, fourteen to a page.

The form opens on one question, **What are you entering?**, and each answer
leads to its own questions:

| Answer | What it asks | Per response |
| --- | --- | --- |
| Equipment | the five equipment pages, as before | one item |
| Tools | whose tools, team, where they're kept; then one short page per tool (kind, make and model, serial number, value) with **Add tool 2?** after each | up to 10 tools |
| Technology | device type, make, model, serial number and who it's issued to (all required); team, phone number, purchase date and price, notes | one device |

All three come from `PAGES` in `build.py`. Change a question there and run
`python3 tools/asset-intake/build.py` to rebuild the PDF and
`AssetListForm.gs`, then put the new script in place and run
`rebuildAssetListForm` (below).

## Setting it up (once, about five minutes)

Everything belongs to **operations@deitemeyerbrothers.com** (Carl, 26 Oct
2026), like the hub's live deployment. Use a Chrome window signed in to that
account only: an Incognito window, or a Chrome profile of its own. Apps Script
gets the account wrong when a browser is signed in to several.

1. Open <https://script.google.com/create> as operations@. Replace the starter
   code with `AssetListForm.gs`, name the project "DB Asset Hub: Asset List
   form", and save.
2. Choose `buildAssetListForm` and click **Run**. Allow the permissions it asks
   for (Forms, Sheets, Drive, and sending one email). It makes the **DB Asset
   Hub: Asset List** folder in operations@'s Drive, with the form and its
   responses Sheet inside, and emails operations@ the links.
3. Drop `asset-list-printable.pdf` into that folder (any name works; the script
   uses whatever PDF is there), then click **Run** again. The form now links the
   PDF, and anyone at the company can open it.
4. The email "DB Asset Hub: Asset List form links" has the link to send, the
   form's edit link, the responses Sheet and the folder. The execution log
   shows the same lines on every run.

## Changing the live form (rebuild in place)

`buildAssetListForm` never touches a form that already exists. To change the
questions on the live form, as operations@:

1. Open the same Apps Script project ("DB Asset Hub: Asset List form"),
   select everything in the editor, paste the new `AssetListForm.gs` over it,
   and save. The project's script properties (the form, Sheet and folder IDs)
   stay put.
2. Choose `rebuildAssetListForm` and click **Run**.

It replaces every question on the same form, so the link people already have
(forms.gle and the long one) keeps working. Answers given before the rebuild
stay in the Sheet, in a tab renamed "Before rebuild" plus the date and time.
New answers go to a new tab. The execution log says how many earlier answers
there were.

To swap the printable PDF without changing its link: in Drive, right-click the
PDF in the folder, then **File information → Manage versions → Upload new
version**.

The form only takes company Google accounts, and records who filled in each
response. Someone without a company account can't open it; to allow that,
turn off "Restrict to users in Deitemeyer Brothers" in the form's Settings.

Google Apps Script can't create file-upload questions. To collect photos of
each asset, add a **File upload** question in the form editor.

## From responses to the import sheet (Appendix B)

Each response carries the responder's email and a timestamp, which say who
reported each item and when its meters were read. The first answer, **What
are you entering?**, says which columns below that row filled in.

### Equipment

| Form question | Appendix B column | Notes |
| --- | --- | --- |
| Kind of equipment | `category` | "Other" answers become new categories or map to existing ones |
| Name or short description | `name` | |
| Unit number or label it has now | (for `tag`) | the office assigns the tag: category prefix plus a number, keeping today's number where there is one |
| Team | `team` | |
| Who usually drives or uses it | `assigned_to_email` | names are matched to company emails |
| Make, Model, Year | `make`, `model`, `year` | |
| VIN or serial number | `vin_serial` | |
| License plate, Plate state | `plate`, `plate_state` | |
| GVWR (lbs) | `gvwr_lbs` | |
| Commercial vehicle (DOT)? | `is_cmv` | "Not sure" stays blank and is flagged for Phase 0, question 2 |
| Odometer (miles), Engine hours | `odometer`, `engine_hours` | the starting readings, dated by the response's timestamp |
| Fuel type, Tank size (gallons) | `fuel_type`, `tank_gallons` | |
| Fuel card: last 4 digits | `fuel_card_ref` | |
| GPS tracker | `telematics_ref` | the provider for now; the device ID comes in Phase 11 |
| Purchase date, Purchase price ($), In service since | `purchase_date`, `purchase_price`, `in_service_date` | |
| Expected life (years) | `expected_life_months` | years × 12 |
| Notes | `notes` | |

### Tools

One response holds up to ten tools, in columns "Tool 1: kind" through
"Tool 10: value ($)". Each tool that was filled in becomes its own import
row; the three questions at the top apply to all of them.

| Form question | Appendix B column | Notes |
| --- | --- | --- |
| Tool *n*: kind | `category` | tag prefix TL for power tools, LAD for ladders, FP for harnesses, lanyards, SRLs and anchors |
| Tool *n*: make and model | `make`, `model`, `name` | split by the office; the whole answer is the name |
| Tool *n*: serial number | `vin_serial` | |
| Tool *n*: value ($) | `purchase_price` | the replacement value, until a real price is known |
| Whose tools are these? | `assigned_to_email` | names are matched to company emails; a crew or shop name leaves it blank and goes in `notes` |
| Tools: team | `team` | |
| Where are they kept? | `notes` | |

### Technology

| Form question | Appendix B column | Notes |
| --- | --- | --- |
| Device type | `category` | category kind `technology`, tag prefix IT |
| Device make, Device model | `make`, `model` | the name is make plus model, e.g. "Apple iPhone 15" |
| Device serial number | `vin_serial` | |
| Issued to | `assigned_to_email` | names are matched to company emails |
| Device team | `team` | |
| Phone number | `notes` | |
| Device purchase date, Device purchase price ($) | `purchase_date`, `purchase_price` | |
| Device notes | `notes` | |
