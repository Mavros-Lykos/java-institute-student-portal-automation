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

    # Click the Submit button inside the opened attendance panel to avoid matching
    # multiple global "Submit" buttons on the page (strict mode violation).
    try:
        submit_btn = panel.get_by_role("button", name="Submit").first
        submit_btn.wait_for(state="visible", timeout=5000)
        submit_btn.click()
    except Exception as e:
        # Fallback: try to click the first visible Submit button on the page
        print(f"[!] Could not click panel Submit (fallback): {e}")
        try:
            fallback = page.get_by_role("button", name="Submit").first
            fallback.click()
        except Exception as e2:
            print(f"[!] Fallback also failed: {e2}")

    # Wait for popup (alert)
    try:
        # Listen for the next alert/dialog
        dialog = page.wait_for_event("dialog", timeout=5000)
        print(f"[+] Alert message: {dialog.message}")
        dialog.accept()
        print("[+] Alert accepted successfully!")
    except Exception as e:
        print(f"[!] No alert appeared (maybe already marked or something changed): {e}")

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
