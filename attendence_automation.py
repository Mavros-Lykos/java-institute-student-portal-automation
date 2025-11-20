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

    print("[*] Searching for attendance entries to submit...")

    # Loop to submit all available attendance entries
    max_attempts = 10
    attempt = 0
    submitted_count = 0

    while attempt < max_attempts:
        # Find all Submit buttons inside the attendance panel
        submit_buttons = panel.get_by_role("button", name="Submit")
        
        try:
            count = submit_buttons.count()
        except Exception:
            count = 0

        if count == 0:
            print(f"[+] No more attendance entries found (checked {attempt+1} times)")
            break

        print(f"[*] Found {count} attendance entry/entries to submit")

        try:
            # Get the first Submit button
            submit_btn = submit_buttons.first
            
            # Try to extract class details from the parent card/container
            try:
                # Navigate up to the col-md-6 div that contains the class info
                card_container = submit_btn.locator("xpath=ancestor::div[contains(@class, 'col-md-6')][1]")
                class_details = card_container.inner_text(timeout=3000)
                
                # Clean up and format the details for display
                details_lines = [line.strip() for line in class_details.split('\n') if line.strip() and 'Submit' not in line]
                if details_lines:
                    print(f"\n{'='*60}")
                    print(f"[+] Marking attendance for:")
                    for line in details_lines[:5]:  # Show first 5 lines to avoid clutter
                        print(f"    {line}")
                    print(f"{'='*60}\n")
                else:
                    print(f"[+] Marking attendance (attempt {submitted_count + 1})")
            except Exception as e:
                print(f"[+] Marking attendance (attempt {submitted_count + 1})")

            # Wait for button to be visible and click it
            submit_btn.wait_for(state="visible", timeout=5000)
            submit_btn.click()
            print(f"[+] Clicked Submit button")

            # Handle the confirmation dialog
            try:
                dialog = page.wait_for_event("dialog", timeout=5000)
                print(f"[+] Alert message: {dialog.message}")
                dialog.accept()
                print("[+] Alert accepted successfully!")
            except Exception as e:
                print(f"[!] No alert appeared (maybe already marked): {e}")

            submitted_count += 1
            
            # Wait for the page to update after submission
            page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"[!] Error while trying to submit attendance: {e}")
            break

        attempt += 1
        page.wait_for_timeout(500)  # Small pause before next check

    if submitted_count == 0:
        print("[!] No attendance entries were submitted. All might be already marked.")
    else:
        print(f"\n[+] Successfully submitted {submitted_count} attendance entry/entries!")
    
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
