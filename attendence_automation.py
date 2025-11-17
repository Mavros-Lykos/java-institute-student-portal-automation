import json
from playwright.sync_api import sync_playwright

# --------------------- Load Credentials ---------------------
def load_credentials():
    with open("credentials.json", "r") as file:
        return json.load(file)

# --------------------- Login Function ---------------------
def login(page, credentials):
    print("[*] Navigating to login page...")
    page.goto("https://web.javainstitute.org/web-portal/login/student.jsp")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    print("[*] Filling in login details...")
    page.get_by_role("textbox", name="Username").fill(credentials["username"])
    page.wait_for_timeout(500)
    page.get_by_role("textbox", name="Password").fill(credentials["password"])
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Sign In").click()

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    print("[+] Logged in successfully!")

# --------------------- Mark Attendance ---------------------
def mark_attendance(page):
    print("[*] Opening attendance panel...")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    panel = page.locator("#online_attendance_panel")
    panel.click()
    page.wait_for_timeout(1500)

    print("[*] Submitting attendance...")
    
    # Iterate and submit all available attendance entries inside the panel.
    # Use a safe maximum to avoid infinite loops if the page content doesn't update.
    max_attempts = 10
    attempt = 0
    submitted_any = False

    while attempt < max_attempts:
        submits = panel.get_by_role("button", name="Submit")
        try:
            count = submits.count()
        except Exception:
            count = 0

        if count == 0:
            break

        try:
            btn = submits.first
            btn.wait_for(state="visible", timeout=3000)
            btn.click()
            submitted_any = True
            print(f"[+] Clicked Submit (attempt {attempt+1})")

            # Handle any dialog that appears after submitting
            try:
                dialog = page.wait_for_event("dialog", timeout=5000)
                print(f"[+] Alert message: {dialog.message}")
                dialog.accept()
                print("[+] Alert accepted successfully!")
            except Exception as e:
                print(f"[!] No alert after submit (or timed out): {e}")

            # Allow the page to update after the submission
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"[!] Could not click a Submit button inside the panel: {e}")
            break

        attempt += 1
        # short pause before checking for more
        page.wait_for_timeout(500)

    if not submitted_any:
        print("[!] No Submit buttons found inside the attendance panel.")

    page.wait_for_timeout(2000)
    print("[+] Attendance submission flow complete.")

# --------------------- Main ---------------------
def main():
    credentials = load_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # visible mode
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Login
        login(page, credentials)

        # Step 2: Mark Attendance
        mark_attendance(page)

        print("[*] Process complete. Browser will remain open for review.")
        print("[*] You can close it manually when ready.")
        # DO NOT close the browser automatically — keep it open to observe
        input("\nPress ENTER here to close the browser after verifying... ")

        context.close()
        browser.close()
        print("[+] Browser closed. Script finished cleanly.")

if __name__ == "__main__":
    main()
