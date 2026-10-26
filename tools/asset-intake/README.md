# Asset List intake

Gathers `PLAYBOOK.md` Phase 0, question 1: every truck, trailer, piece of
equipment, power tool, ladder and fall-protection kit, with the Appendix B
fields. Two ways to fill it in, with the same questions in the same order:

- **Online:** a Google Form (phone, tablet or computer), one response per asset.
  Responses land in a Google Sheet. Built by `AssetListForm.gs`.
- **Paper:** `asset-list-printable.pdf`. Page 1 is the instructions, page 2 is
  one record per asset (print one per vehicle, trailer or machine), and page 3
  is a quick list for small tools and safety gear, fifteen to a page.

Both come from `QUESTIONS` in `build.py`. Change a question there and run
`python3 tools/asset-intake/build.py --folder-id <Drive folder id>` to rebuild
both. Then paste the new `AssetListForm.gs` into the script project and edit the
live form by hand (a re-run does not rebuild an existing form).

## Setting it up (once, about five minutes)

Everything lives in Carl's Drive folder **DB Asset Hub: Asset List**
(`1Y_FSHZmWxuM8rH_CV0sa19IoCkmYbEvY`).

1. Drop `asset-list-printable.pdf` into that folder (any name works; the script
   uses whatever PDF is there).
2. Open <https://script.google.com/create> signed in as
   carlbledsoe@deitemeyerbrothers.com. Replace the starter code with
   `AssetListForm.gs`, name the project, and save.
3. Choose `buildAssetListForm` and click **Run**. Allow the permissions it asks
   for (Forms, Sheets, Drive, and sending you one email).
4. The email "DB Asset Hub: Asset List form links" has the link to send, the
   form's edit link, the responses Sheet and the printable PDF. The execution
   log shows the same lines.

The form only takes company Google accounts, and records who filled in each
response. Someone without a company account can't open it; to allow that,
turn off "Restrict to users in Deitemeyer Brothers" in the form's Settings.

Google Apps Script can't create file-upload questions. To collect photos of
each asset, add a **File upload** question in the form editor.

## From responses to the import sheet (Appendix B)

| Form question | Appendix B column | Notes |
| --- | --- | --- |
| Kind of asset | `category` | "Other" answers become new categories or map to existing ones |
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

Each response also carries the responder's email and a timestamp, which say
who reported each asset and when its meters were read.
