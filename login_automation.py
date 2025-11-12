import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# --------------------- Load Credentials ---------------------
def load_credentials():
    with open("credentials.json", "r") as file:
        return json.load(file)

# --------------------- Login Function ---------------------
def login(page, credentials):
    page.goto(credentials["site_url"])
    page.wait_for_load_state("networkidle")  # wait for page fully loaded
    page.wait_for_timeout(2000)  # wait 2 seconds for stability

    page.get_by_role("textbox", name="Username").click()
    page.wait_for_timeout(500)
    page.get_by_role("textbox", name="Username").fill(credentials["username"])
    page.wait_for_timeout(500)
    page.get_by_role("textbox", name="Password").click()
    page.wait_for_timeout(500)
    page.get_by_role("textbox", name="Password").fill(credentials["password"])
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_load_state("networkidle")  # ensure page finished loading
    page.wait_for_timeout(2000)
    print("[+] Logged in successfully")

# --------------------- Select Nearest Class ---------------------
def select_class(page):
    now = datetime.now()
    # Select all cards with the green background (flexible)
    class_cards = page.locator("div.mt-element-ribbon.tt-height").filter(has=page.locator("[style*='background-color']"))
    
    nearest_card = None
    nearest_time = None

    count = class_cards.count()
    if count == 0:
        print("[!] No green class cards found")
        return False

    for i in range(count):
        card = class_cards.nth(i)
        text = card.inner_text()
        print(f"[DEBUG] Card {i}:\n{text}\n")  # debug output
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        time_match = re.search(r"(\d{1,2}:\d{2} [AP]M) to (\d{1,2}:\d{2} [AP]M)", text)
        if date_match and time_match:
            class_date_str = date_match.group(1)
            start_time_str = time_match.group(1)
            end_time_str = time_match.group(2)
            class_start = datetime.strptime(class_date_str + " " + start_time_str, "%Y-%m-%d %I:%M %p")
            class_end = datetime.strptime(class_date_str + " " + end_time_str, "%Y-%m-%d %I:%M %p")
            
            # Pick ongoing or nearest past class
            if class_start <= now <= class_end or (class_start <= now and (nearest_time is None or class_start > nearest_time)):
                nearest_time = class_start
                nearest_card = card

    if nearest_card:
        nearest_card.click()
        page.wait_for_timeout(1000)
        # print(f"[+] Selected class:\n{nearest_card.inner_text()}")
        # Click the first <a> or link inside the card
        try:
            nearest_card.locator("a").first.click()
            page.wait_for_timeout(1000)
        except:
            print("[!] Could not find link inside card")
        return True
    else:
        print("[!] No suitable class found for now")
        return False

# --------------------- Fill Zoom Registration ---------------------
def fill_zoom_form(page1, credentials):
    page1.wait_for_load_state("networkidle")
    page1.wait_for_timeout(1500)

    page1.get_by_role("textbox", name="First Name").fill(credentials["first_name"])
    page1.wait_for_timeout(300)
    page1.get_by_role("textbox", name="Last Name").fill(credentials["last_name"])
    page1.wait_for_timeout(300)
    page1.get_by_role("textbox", name="Email Address").fill(credentials["email"])
    page1.wait_for_timeout(300)
    page1.get_by_role("textbox", name="NIC Number").fill(credentials["nic_number"])
    page1.wait_for_timeout(300)
    page1.get_by_role("textbox", name="Contact Number").fill(credentials["contact_number"])
    page1.wait_for_timeout(500)

    # Click Register and Join
    try:
        with page1.expect_download() as download_info:
            page1.get_by_role("button", name="Register and Join").click()
        download_info.value
        print("[+] Zoom registration triggered download")
    except:
        print("[!] No download triggered — maybe manual input required")

    page1.wait_for_timeout(1000)

    # Click Open Zoom
    # Wait and click Open Zoom
    try:
        page1.locator("button", has_text="Open").wait_for(state="visible", timeout=5000)
        page1.locator("button", has_text="Open").click()
        print("[+] Open Zoom button clicked")
    except:
        print("[!] Could not Click the button — please click manually")

# Pause for any extra fields
input("[!] If there are missing fields, please fill manually and press Enter here to continue...")


# --------------------- Main Automation ---------------------
def main():
    credentials = load_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Login
        login(page, credentials)

        # Step 2: Select nearest class
        if select_class(page):
            # Step 3: Handle Zoom popup
            with page.expect_popup() as page1_info:
                page.locator(".col-md-12 > a").first.click()
            page1 = page1_info.value
            fill_zoom_form(page1, credentials)

        page.wait_for_timeout(1000)
        context.close()
        browser.close()
        print("[+] Automation completed!")

if __name__ == "__main__":
    main()
