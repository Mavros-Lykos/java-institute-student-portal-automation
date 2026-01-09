import re
import time
from datetime import datetime
from typing import Optional
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from config_manager import ConfigManager


class ZoomAutomation:
    def __init__(self, user_credentials, log_callback, status_callback):
        self.credentials = user_credentials
        self.log = log_callback
        self.update_status = status_callback
        self.config = ConfigManager()
        self.driver: Optional[webdriver.Chrome] = None
        self.should_stop = False
        self.zoom_link = None
        self.class_name = None
        self.class_time = None

    def stop(self):
        self.should_stop = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def get_driver(self):
        """Try to get Chrome driver, fall back to Edge"""
        try:
            self.log("🔧 Attempting to launch Google Chrome...", "info")
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_experimental_option("detach", True)  # Keep browser open

            # Disable automation flags
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            self.log(f"⚠️ Chrome launch failed: {e}", "warning")
            self.log("🔧 Attempting to launch Microsoft Edge...", "info")
            try:
                options = webdriver.EdgeOptions()
                options.add_argument("--start-maximized")
                options.add_experimental_option("detach", True)

                # Disable automation flags
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"]
                )
                options.add_experimental_option("useAutomationExtension", False)

                service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)
                return driver
            except Exception as e2:
                self.log(f"❌ Edge launch failed: {e2}", "error")
                raise Exception(
                    "Could not launch Chrome or Edge. Please ensure one is installed."
                )

    def run(self):
        try:
            self.driver = self.get_driver()

            # Step 1: Login
            if not self.login():
                return

            # Step 2: Select class
            if not self.select_class():
                return

            # Step 3: Handle Zoom registration
            self.handle_zoom_popup()

            # Keep browser open is handled by 'detach' option, but we can also loop/wait here if needed
            self.log("✅ Automation complete. Browser will remain open.", "success")
            self.update_status("✅ Completed - Browser Open", "success")

            # Infinite wait (optional, since detach works, but good for keeping thread alive without exit)
            try:
                while not self.should_stop:
                    time.sleep(1)
            except:
                pass

        except Exception as e:
            self.log(f"❌ Automation error: {str(e)}", "error")
            self.update_status("❌ Error occurred", "error")
            # Don't raise here to keep GUI alive, but log it

    def login(self):
        try:
            self.log("🌐 Navigating to login page...", "info")
            self.update_status("🌐 Loading login page...", "info")

            # Decrypt password
            password = self.config.decrypt_password(self.credentials["password"])

            self.driver.get(self.credentials["site_url"])
            wait = WebDriverWait(self.driver, 10)

            self.log("📝 Entering credentials...", "info")

            # Username
            username_field = None
            try:
                username_field = wait.until(
                    EC.element_to_be_clickable((By.ID, "username"))
                )
            except:
                try:
                    username_field = self.driver.find_element(By.NAME, "Username")
                except:
                    try:
                        username_field = self.driver.find_element(By.NAME, "username")
                    except:
                        username_field = self.driver.find_element(
                            By.CSS_SELECTOR, "input[type='text']"
                        )

            username_field.clear()
            username_field.send_keys(self.credentials["username"])
            time.sleep(0.5)

            # Password
            password_field = None
            try:
                password_field = self.driver.find_element(By.ID, "password")
            except:
                try:
                    password_field = self.driver.find_element(By.NAME, "Password")
                except:
                    try:
                        password_field = self.driver.find_element(By.NAME, "password")
                    except:
                        password_field = self.driver.find_element(
                            By.CSS_SELECTOR, "input[type='password']"
                        )

            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)

            # Click Sign In
            # Try to find button by text or class or type
            try:
                sign_in_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Sign In')]"
                )
            except:
                sign_in_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                )

            sign_in_btn.click()

            # Wait for login success (more robust)
            self.log("⏳ Waiting for dashboard to load...", "info")
            try:
                # Use any_of for multiple possible results
                wait.until(
                    EC.any_of(
                        EC.title_contains("Dashboard"),
                        EC.url_contains("home"),
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "mt-element-ribbon")
                        ),
                        EC.presence_of_element_located(
                            (By.ID, "online_attendance_panel")
                        ),
                    )
                )
            except:
                # Fallback: Just wait a bit if explicit conditions fail
                self.log(
                    "⚠️ Success indicators not detected, but waiting for page load...",
                    "warning",
                )
                time.sleep(5)

            self.log("✅ Logged in successfully", "success")
            self.update_status("✅ Logged in", "success")
            return True

        except Exception as e:
            self.log(f"❌ Login failed: {str(e)}", "error")
            self.log(
                "⚠️ Please check the browser and login manually if needed", "warning"
            )
            self.update_status("❌ Login failed", "error")
            return False

    def select_class(self):
        try:
            self.log("🔍 Searching for today's classes...", "info")
            self.update_status("🔍 Searching classes...", "info")

            now = datetime.now()
            today_date = now.strftime("%Y-%m-%d")

            wait = WebDriverWait(self.driver, 10)

            # Wait for cards
            try:
                wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.mt-element-ribbon")
                    )
                )
            except TimeoutException:
                self.log("⚠️ No class cards found on page", "warning")
                return False

            time.sleep(2)

            class_cards = self.driver.find_elements(
                By.CSS_SELECTOR, "div.mt-element-ribbon.tt-height"
            )
            # Filter for green background manually if needed, or assume all ribbons are relevant

            count = len(class_cards)

            if count == 0:
                self.log("⚠️ No class cards found", "warning")
                return False

            self.log(f"📚 Found {count} class card(s)", "info")

            nearest_card = None
            nearest_time = None

            for index, card in enumerate(class_cards):
                try:
                    text = card.text

                    # Parse date and time
                    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
                    time_match = re.search(
                        r"(\d{1,2}:\d{2} [AP]M) to (\d{1,2}:\d{2} [AP]M)", text
                    )

                    if date_match and time_match:
                        class_date_str = date_match.group(1)
                        start_time_str = time_match.group(1)
                        end_time_str = time_match.group(2)

                        if class_date_str != today_date:
                            continue

                        # Format: YYYY-MM-DD HH:MM AM/PM
                        class_start = datetime.strptime(
                            class_date_str + " " + start_time_str, "%Y-%m-%d %I:%M %p"
                        )
                        class_end = datetime.strptime(
                            class_date_str + " " + end_time_str, "%Y-%m-%d %I:%M %p"
                        )

                        lines = text.strip().split("\n")
                        class_title = lines[0] if lines else "Zoom Class"

                        self.log(f"📅 Class found: {class_title}", "info")
                        self.log(
                            f"   ⏰ Time: {start_time_str} - {end_time_str}", "info"
                        )

                        if class_start <= now <= class_end:
                            self.log(
                                f"✅ Class is ongoing! Selecting this class", "success"
                            )
                            nearest_time = class_start
                            nearest_card = card
                            self.class_name = class_title
                            self.class_time = f"{start_time_str} - {end_time_str}"
                            break
                        elif class_start <= now and (
                            nearest_time is None or class_start > nearest_time
                        ):
                            nearest_time = class_start
                            nearest_card = card
                            self.class_name = class_title
                            self.class_time = f"{start_time_str} - {end_time_str}"
                except:
                    continue

            if nearest_card:
                self.log(f"🎯 Selecting class: {self.class_name}", "success")
                self.update_status(f"🎯 Selected: {self.class_name}", "success")

                # Click the card
                nearest_card.click()
                time.sleep(1)

                # Click the first link inside
                try:
                    link = nearest_card.find_element(By.TAG_NAME, "a")
                    link.click()
                    self.log("✅ Clicked class link", "success")
                    return True
                except:
                    self.log("⚠️ Could not find link inside card", "warning")
                    return False
            else:
                self.log("⚠️ No suitable class found for today", "warning")
                return False

        except Exception as e:
            self.log(f"❌ Error selecting class: {str(e)}", "error")
            return False

    def handle_zoom_popup(self):
        try:
            self.log("⏳ Waiting for Zoom registration page...", "info")
            self.update_status("⏳ Waiting for Zoom registration page...", "info")

            # Switch to new window handle
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.number_of_windows_to_be(2))

            original_window = self.driver.current_window_handle
            for handle in self.driver.window_handles:
                if handle != original_window:
                    self.driver.switch_to.window(handle)
                    break

            self.log("✅  Zoom registration page detected!", "success")


            self.fill_zoom_form()

        except Exception as e:
            self.log(f"⚠️ No Zoom registration page detected or error: {str(e)}", "warning")

    def fill_zoom_form(self):
        try:
            self.log("📝 Filling Zoom registration form...", "info")
            wait = WebDriverWait(self.driver, 10)

            # Using partial matches or names to be safe, assuming IDs might change or using standard zoom form IDs
            # Standard Zoom usually uses IDs like 'question_first_name', 'question_last_name', etc.
            # But the site might embed it. Let's try name attributes or labels.

            # Helper to find and fill
            def fill_field(name_attr, value):
                try:
                    elem = self.driver.find_element(By.NAME, name_attr)
                    elem.clear()
                    elem.send_keys(value)
                    time.sleep(0.3)
                    return True
                except:
                    # Try label text locators if names fail in future versions
                    return False

            # Fill fields - mapping based on standard form expectations
            # Note: actual field names on the Zoom registration page should be verified.
            # Common names: first_name, last_name, email, etc.
            # Looking at playwight code: "First Name", "Last Name" etc were used with get_by_role("textbox", name=...)
            # That corresponds to aria-label or associated label.

            # Let's try to find by ID patterns commonly used or by Label text via XPath

            # First Name
            try:
                self.driver.find_element(By.ID, "question_first_name").send_keys(
                    self.credentials["first_name"]
                )
            except:
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[name*='first_name']"
                ).send_keys(self.credentials["first_name"])

            # Last Name
            try:
                self.driver.find_element(By.ID, "question_last_name").send_keys(
                    self.credentials["last_name"]
                )
            except:
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[name*='last_name']"
                ).send_keys(self.credentials["last_name"])

            # Email
            try:
                self.driver.find_element(By.ID, "question_email").send_keys(
                    self.credentials["email"]
                )
            except:
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='email']"
                ).send_keys(self.credentials["email"])

            # Other custom questions might need specific indices or loop
            # Playwright was: "NIC Number", "Contact Number". These are likely custom questions.
            # Zoom custom questions often stick to inputs.
            # We can try to match the label text to the input.

            # NIC Number
            try:
                self.driver.find_element(By.ID, "question_NICNumber").send_keys(
                    self.credentials["nic_number"]
                )
            except:
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='text']"
                ).send_keys(self.credentials["nic_number"])

            # Contact Number
            try:
                self.driver.find_element(By.ID, "question_ContactNumber").send_keys(
                    self.credentials["contact_number"]
                )
            except:
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='text']"
                ).send_keys(self.credentials["contact_number"])

            """ custom_inputs = {
                "NIC Number": self.credentials['nic_number'],
                "Contact Number": self.credentials['contact_number']
            }
            
            for label_text, value in custom_inputs.items():
                try:
                    # XPath to find label containing text, then following input
                    xpath = f"//label[contains(text(), '{label_text}')]/following::input[1]"
                    # Or possibly looking for input with aria-label
                    inp = self.driver.find_element(By.XPATH, xpath)
                    inp.clear()
                    inp.send_keys(value)
                except:
                    pass
            """
            self.log("✅ Form filled successfully", "success")

            # Click Register
            try:
                # Try multiple selectors for Register button
                btn = None
                selectors = [
                    (By.XPATH, "//button[.//span[text()='Register and Join']]"),
                    # XPath using contains (safer if text slightly changes)
                    (By.XPATH, "//span[contains(text(),'Register')]/ancestor::button"),
                    # CSS selector using class (works if class is unique)
                    (By.CSS_SELECTOR, "button.zoom-button--primary"),
                    # CSS selector using multiple classes (more specific)
                    ( By.CSS_SELECTOR,"button.zoom-button.zoom-button--md.zoom-button--primary"),
                ]

                for by, val in selectors:
                    try:
                        btn = self.driver.find_element(by, val)
                        if btn.is_displayed():
                            break
                    except:
                        continue

                if btn:
                    btn.click()
                    self.log("✅ Clicked 'Register'", "success")
                else:
                    self.log(
                        "⚠️ Could not find Register button automatically", "warning"
                    )

            except Exception as e:
                self.log(f"⚠️ Error clicking register: {e}", "warning")

            # Wait for "Open Zoom" or redirect
            time.sleep(4)
            self.zoom_link = self.driver.current_url
            self.log("✅ Registration complete - Browser will remain open", "success")
            self.update_status("✅ Form submitted - Check browser", "success")

        except Exception as e:
            self.log(f"⚠️ Form filling error: {str(e)}", "warning")


class AttendanceAutomation:
    def __init__(self, user_credentials, log_callback, status_callback):
        self.credentials = user_credentials
        self.log = log_callback
        self.update_status = status_callback
        self.config = ConfigManager()
        self.driver: Optional[webdriver.Chrome] = None
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def get_driver(self):
        """Try to get Chrome driver, fall back to Edge"""
        try:
            self.log("🔧 Attempting to launch Google Chrome...", "info")
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_experimental_option("detach", True)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception:
            self.log("🔧 Attempting to launch Microsoft Edge...", "info")
            try:
                options = webdriver.EdgeOptions()
                options.add_argument("--start-maximized")
                options.add_experimental_option("detach", True)
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"]
                )
                options.add_experimental_option("useAutomationExtension", False)

                service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)
                return driver
            except Exception as e2:
                self.log(f"❌ Edge launch failed: {e2}", "error")
                raise Exception(
                    "Could not launch Chrome or Edge. Please ensure one is installed."
                )

    def run(self):
        try:
            self.driver = self.get_driver()

            # Step 1: Login
            if not self.login():
                return

            # Step 2: Mark attendance
            self.mark_attendance()

            self.log(
                "✅ Attendance automation complete. Browser will remain open.",
                "success",
            )
            self.update_status("✅ Completed - Browser Open", "success")

            try:
                while not self.should_stop:
                    time.sleep(1)
            except:
                pass

        except Exception as e:
            self.log(f"❌ Automation error: {str(e)}", "error")
            self.update_status("❌ Error occurred", "error")

    def login(self):
        try:
            self.log("🌐 Navigating to login page...", "info")
            self.update_status("🌐 Loading login page...", "info")

            password = self.config.decrypt_password(self.credentials["password"])

            self.driver.get(
                "https://web.javainstitute.org/web-portal/login/student.jsp"
            )
            wait = WebDriverWait(self.driver, 20)

            self.log("📝 Entering credentials...", "info")

            # Validating elements based on original script: text boxes name="Username", "Password"
            try:
                wait.until(
                    EC.presence_of_element_located((By.NAME, "Username"))
                ).send_keys(self.credentials["username"])
            except:
                try:
                    self.driver.find_element(By.NAME, "username").send_keys(
                        self.credentials["username"]
                    )
                except:
                    self.driver.find_element(
                        By.CSS_SELECTOR, "input[type='text']"
                    ).send_keys(self.credentials["username"])

            time.sleep(0.5)

            try:
                self.driver.find_element(By.NAME, "Password").send_keys(password)
            except:
                try:
                    self.driver.find_element(By.NAME, "password").send_keys(password)
                except:
                    self.driver.find_element(
                        By.CSS_SELECTOR, "input[type='password']"
                    ).send_keys(password)

            time.sleep(0.5)

            # Click Sign In - finding by button name "Sign In"
            try:
                self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Sign In')]"
                ).click()
            except:
                # If caps or different selector
                self.driver.find_element(By.CSS_SELECTOR, "button").click()

            time.sleep(3)
            self.log("✅ Logged in successfully", "success")
            self.update_status("✅ Logged in", "success")
            return True

        except Exception as e:
            self.log(f"❌ Login failed: {str(e)}", "error")
            return False

    def mark_attendance(self):
        try:
            self.log("📋 Opening attendance panel...", "info")
            self.update_status("📋 Opening attendance...", "info")

            wait = WebDriverWait(self.driver, 10)

            # Click #online_attendance_panel
            wait.until(
                EC.element_to_be_clickable((By.ID, "online_attendance_panel"))
            ).click()
            time.sleep(2)

            self.log("🔍 Searching for attendance entries...", "info")

            # Find submit buttons
            # Playwright used: get_by_role("button", name="Submit")
            # Selenium: XPath //button[contains(text(), 'Submit')]

            max_attempts = 10
            attempt = 0
            submitted_count = 0

            while attempt < max_attempts:
                try:
                    btns = self.driver.find_elements(
                        By.XPATH, "//button[contains(text(), 'Submit')]"
                    )
                except:
                    btns = []

                count = len(btns)

                if count == 0:
                    self.log(f"✅ No more attendance entries found", "success")
                    break

                submit_btn = btns[0]

                # Check visibility
                if not submit_btn.is_displayed():
                    attempt += 1
                    continue

                try:
                    # Try to log details
                    try:
                        card = submit_btn.find_element(
                            By.XPATH, "./ancestor::div[contains(@class, 'col-md-6')]"
                        )
                        text = card.text
                        lines = [l for l in text.split("\n") if "Submit" not in l]
                        if lines:
                            self.log("   --- Marking Attendance ---", "info")
                            self.log(f"   {lines[0]}", "info")
                    except:
                        pass

                    submit_btn.click()
                    self.log("✅ Clicked Submit", "success")

                    # Handle Alert
                    try:
                        WebDriverWait(self.driver, 5).until(EC.alert_is_present())
                        alert = self.driver.switch_to.alert
                        self.log(f"📢 Alert: {alert.text}", "info")
                        alert.accept()
                        self.log("✅ Alert accepted", "success")
                    except TimeoutException:
                        self.log("⚠️ No alert appeared", "warning")

                    submitted_count += 1
                    self.update_status(f"✅ Submitted {submitted_count}", "success")
                    time.sleep(2)

                except Exception as e:
                    self.log(f"❌ Error submitting: {e}", "error")
                    break

                attempt += 1

            if submitted_count > 0:
                self.log(
                    f"🎉 Successfully submitted {submitted_count} attendance(s)!",
                    "success",
                )
            else:
                self.log("⚠️ No entries to submit", "warning")

        except Exception as e:
            self.log(f"❌ Attendance error: {str(e)}", "error")
