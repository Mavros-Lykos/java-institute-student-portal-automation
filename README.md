
# Java Institute Zoom & Attendance Automation ⚙️🎓

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Playwright](https://img.shields.io/badge/playwright-1.55.0-orange)
![Status](https://img.shields.io/badge/status-experimental-yellow)

Lightweight automation scripts to simplify two common student-portal tasks:

- `login_automation.py` — locate a scheduled class and complete the Zoom registration flow.
- `attendence_automation.py` — open the attendance panel and submit attendance.

This README focuses only on these two scripts (inputs, expected behavior, setup, and local testing).

**Please read carefully** — both scripts interact with the live portal and open a real browser session.

**Quick Links**
- Script: `login_automation.py`
- Script: `attendence_automation.py`
- Config file: `credentials.json` (required)

**Note:** Do NOT commit `credentials.json` to version control. Keep it private.

## Files & Purpose 📁

- `login_automation.py` —
	- Navigates to `site_url` from `credentials.json` and signs in with `username`/`password`.
	- Scans the page for class cards (green cards), finds the nearest/ongoing class, clicks it, and opens the Zoom registration popup.
	- Fills Zoom registration fields (`First Name`, `Last Name`, `Email Address`, `NIC Number`, `Contact Number`) from `credentials.json` and attempts to click `Register and Join`.
	- Waits for the `Open Zoom` button and attempts to click it. Contains a manual pause for any missing fields.

- `attendence_automation.py` —
	- Navigates directly to the student login page (hard-coded URL used in the script).
	- Signs in with `username`/`password` from `credentials.json`.
	- Opens the attendance panel (`#online_attendance_panel`) and clicks the `Submit` button.
	- Waits for any confirmation dialog and accepts it. Leaves the browser open so you can review the result, then asks for a final Enter to close.

## Example `credentials.json` 🔐

Create a `credentials.json` file in the project root with the following structure (example values shown):

```
{
	"site_url": "https://web.javainstitute.org/web-portal/student-dashboard",
	"username": "your_username",
	"password": "your_password",
	"first_name": "John",
	"last_name": "Doe",
	"email": "john.doe@example.com",
	"nic_number": "123456789V",
	"contact_number": "+94123456789"
}
```

Only `username` and `password` are required for `attendence_automation.py`. `login_automation.py` uses the additional fields for the Zoom form.

## Local Development & Testing 🧪 (Windows / PowerShell)

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

3. Install Playwright browsers

```powershell
python -m playwright install
```

4. Prepare `credentials.json` (see example above)

5. Run the scripts (visible browser; scripts use headful mode by default)

```powershell
python attendence_automation.py
python login_automation.py
```

What to expect when running:
- A Chromium browser will open (non-headless) so you can watch the automation.
- Both scripts use `input(...)` pauses in the code to allow you to manually fix missing fields or inspect results.
- `attendence_automation.py` will keep the browser open until you press Enter in the console; this is deliberate for verification.

## Common Troubleshooting 🔍

- Playwright complains about missing browsers: run `python -m playwright install`.
- Selectors stop working: the portal layout or element labels may have changed. Inspect the portal in the browser and update selectors in the scripts (for example `get_by_role` names, CSS locators like `#online_attendance_panel`, or class names used for cards).
- No class cards found in `login_automation.py`: ensure you are logged into the correct dashboard URL (set `site_url` in `credentials.json`) and classes are shown as green cards.
- Scripts hang at `input(...)`: that's an intentional pause — press Enter to continue or remove the pause if you prefer a fully automated run (not recommended until stable).

## Security & Privacy ⚠️

- Never commit `credentials.json` to source control. Add it to `.gitignore` if you plan to keep this repository.
- Keep 2FA/secondary authentication in mind — these scripts do not handle MFA flows.

## Suggestions & Next Steps 🚀

- Add CLI flags to both scripts to allow `--headless` and `--site-url` overrides.
- Extract shared login logic into a small module to reduce duplication.
- Add automated tests for selector mappings (mock pages or snapshots) before enabling headless scheduled runs.
- Add a small GitHub Action that runs a smoke test against a staging portal (use secrets to store credentials securely if you choose to automate in CI — be extremely careful).

## Contact & Contribution

If you'd like help hardening these scripts, converting to a robust Playwright test suite, or adding scheduling and monitoring, open an issue or DM me and I can help implement the next steps. 👍

---

Made with ❤️ for faster attendance and Zoom registration.
