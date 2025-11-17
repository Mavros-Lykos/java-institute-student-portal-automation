import re
from datetime import datetime
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from config_manager import ConfigManager

class ZoomAutomation:
    def __init__(self, user_credentials, log_callback, status_callback):
        self.credentials = user_credentials
        self.log = log_callback
        self.update_status = status_callback
        self.config = ConfigManager()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.should_stop = False
        self.zoom_link = None
        self.class_name = None
        self.class_time = None
        
    def stop(self):
        self.should_stop = True
        if self.context:
            try:
                self.context.close()
            except:
                pass
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
    
    def run(self):
        try:
            with sync_playwright() as p:
                # Launch browser in visible mode with downloads disabled
                self.browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                # Create context with download blocking
                self.context = self.browser.new_context(
                    accept_downloads=False,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                self.page = self.context.new_page()
                
                # Step 1: Login
                if not self.login():
                    return
                
                # Step 2: Select class
                if not self.select_class():
                    return
                
                # Step 3: Handle Zoom registration
                self.handle_zoom_popup()
                
                # Keep browser open
                self.log("✅ Automation complete. Browser will remain open until you close it.", 'success')
                self.log("ℹ️ You can now interact with the browser manually.", 'info')
                self.update_status("✅ Completed - Browser Open", 'success')
                
                # Wait indefinitely until user closes
                try:
                    self.page.wait_for_timeout(3600000)  # Wait 1 hour, but user can close anytime
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Automation error: {str(e)}", 'error')
            self.update_status("❌ Error occurred", 'error')
            raise
    
    def login(self):
        try:
            # runtime check for analyzer
            from playwright.sync_api import Page as _Page
            if not isinstance(self.page, _Page):
                raise RuntimeError("Browser page is not initialized")

            self.log("🌐 Navigating to login page...", 'info')
            self.update_status("🌐 Loading login page...", 'info')
            
            # Decrypt password
            password = self.config.decrypt_password(self.credentials['password'])
            
            self.page.goto(self.credentials['site_url'])
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            
            self.log("📝 Entering credentials...", 'info')
            
            # Fill username
            self.page.get_by_role("textbox", name="Username").click()
            self.page.wait_for_timeout(500)
            self.page.get_by_role("textbox", name="Username").fill(self.credentials['username'])
            self.page.wait_for_timeout(500)
            
            # Fill password
            self.page.get_by_role("textbox", name="Password").click()
            self.page.wait_for_timeout(500)
            self.page.get_by_role("textbox", name="Password").fill(password)
            self.page.wait_for_timeout(1000)
            
            # Click sign in
            self.page.get_by_role("button", name="Sign In").click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            
            self.log("✅ Logged in successfully - Check browser", 'success')
            self.update_status("✅ Logged in", 'success')
            return True
            
        except Exception as e:
            self.log(f"❌ Login failed: {str(e)}", 'error')
            self.log("⚠️ Please check the browser and login manually if needed", 'warning')
            self.update_status("❌ Login failed", 'error')
            return False
    
    def select_class(self):
        try:
            from playwright.sync_api import Page as _Page
            if not isinstance(self.page, _Page):
                raise RuntimeError("Browser page is not initialized")

            self.log("🔍 Searching for today's classes...", 'info')
            self.update_status("🔍 Searching classes...", 'info')
            
            now = datetime.now()
            today_date = now.strftime("%Y-%m-%d")
            
            # Wait for class cards to load
            self.page.wait_for_timeout(2000)
            
            # Select all cards with green background
            class_cards = self.page.locator("div.mt-element-ribbon.tt-height").filter(
                has=self.page.locator("[style*='background-color']")
            )
            
            count = class_cards.count()
            
            if count == 0:
                self.log("⚠️ No class cards found on page", 'warning')
                self.update_status("⚠️ No classes found", 'warning')
                return False
            
            self.log(f"📚 Found {count} class card(s)", 'info')
            
            nearest_card = None
            nearest_time = None
            nearest_card_index = -1
            
            for i in range(count):
                card = class_cards.nth(i)
                text = card.inner_text()
                
                # Parse date and time
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
                time_match = re.search(r"(\d{1,2}:\d{2} [AP]M) to (\d{1,2}:\d{2} [AP]M)", text)
                
                if date_match and time_match:
                    class_date_str = date_match.group(1)
                    start_time_str = time_match.group(1)
                    end_time_str = time_match.group(2)
                    
                    # Only consider today's classes
                    if class_date_str != today_date:
                        continue
                    
                    class_start = datetime.strptime(class_date_str + " " + start_time_str, "%Y-%m-%d %I:%M %p")
                    class_end = datetime.strptime(class_date_str + " " + end_time_str, "%Y-%m-%d %I:%M %p")
                    
                    # Extract class name (first line usually)
                    lines = text.strip().split('\n')
                    class_title = lines[0] if lines else "Zoom Class"
                    
                    self.log(f"📅 Class found: {class_title}", 'info')
                    self.log(f"   ⏰ Time: {start_time_str} - {end_time_str}", 'info')
                    
                    # Pick ongoing or nearest past class
                    if class_start <= now <= class_end:
                        self.log(f"✅ Class is ongoing! Selecting this class", 'success')
                        nearest_time = class_start
                        nearest_card = card
                        nearest_card_index = i
                        self.class_name = class_title
                        self.class_time = f"{start_time_str} - {end_time_str}"
                        break
                    elif class_start <= now and (nearest_time is None or class_start > nearest_time):
                        nearest_time = class_start
                        nearest_card = card
                        nearest_card_index = i
                        self.class_name = class_title
                        self.class_time = f"{start_time_str} - {end_time_str}"
            
            if nearest_card:
                self.log(f"🎯 Selecting class: {self.class_name}", 'success')
                self.log(f"   ⏰ {self.class_time}", 'info')
                self.update_status(f"🎯 Selected: {self.class_name}", 'success')
                
                # Click the card
                nearest_card.click()
                self.page.wait_for_timeout(1000)
                
                # Click the first link inside the card
                try:
                    nearest_card.locator("a").first.click()
                    self.page.wait_for_timeout(1000)
                    self.log("✅ Clicked class link", 'success')
                except:
                    self.log("⚠️ Could not find link inside card", 'warning')
                
                return True
            else:
                self.log("⚠️ No suitable class found for today", 'warning')
                self.update_status("⚠️ No classes today", 'warning')
                return False
                
        except Exception as e:
            self.log(f"❌ Error selecting class: {str(e)}", 'error')
            self.update_status("❌ Class selection failed", 'error')
            return False
    
    def handle_zoom_popup(self):
        try:
            from playwright.sync_api import Page as _Page
            if not isinstance(self.page, _Page):
                raise RuntimeError("Browser page is not initialized")

            self.log("⏳ Waiting for Zoom registration popup...", 'info')
            self.update_status("⏳ Waiting for popup...", 'info')
            
            # Wait for popup
            with self.page.expect_popup(timeout=10000) as popup_info:
                self.page.locator(".col-md-12 > a").first.click()
            
            popup = popup_info.value
            self.log("✅ Popup detected!", 'success')
            
            # Store the popup URL as zoom link
            self.zoom_link = popup.url
            
            self.fill_zoom_form(popup)
            
        except Exception as e:
            self.log(f"⚠️ No popup detected or error: {str(e)}", 'warning')
            self.log("ℹ️ Please check browser and join manually if needed", 'info')
    
    def fill_zoom_form(self, popup):
        try:
            self.log("📝 Filling Zoom registration form...", 'info')
            self.update_status("📝 Filling form...", 'info')
            
            popup.wait_for_load_state("networkidle")
            popup.wait_for_timeout(1500)
            
            # Decrypt password for use
            password = self.config.decrypt_password(self.credentials['password'])
            
            # Fill form fields
            popup.get_by_role("textbox", name="First Name").fill(self.credentials['first_name'])
            popup.wait_for_timeout(300)
            
            popup.get_by_role("textbox", name="Last Name").fill(self.credentials['last_name'])
            popup.wait_for_timeout(300)
            
            popup.get_by_role("textbox", name="Email Address").fill(self.credentials['email'])
            popup.wait_for_timeout(300)
            
            popup.get_by_role("textbox", name="NIC Number").fill(self.credentials['nic_number'])
            popup.wait_for_timeout(300)
            
            popup.get_by_role("textbox", name="Contact Number").fill(self.credentials['contact_number'])
            popup.wait_for_timeout(500)
            
            self.log("✅ Form filled successfully", 'success')
            
            # Click Register and Join (improved: try multiple fallbacks)
            try:
                # 1) Preferred: role-based lookup (exact or partial)
                try:
                    popup.get_by_role("button", name="Register").wait_for(state="visible", timeout=3000)
                    popup.get_by_role("button", name="Register").click()
                    popup.wait_for_timeout(1000)
                    self.log("✅ Clicked 'Register' (role selector)", 'success')
                    register_clicked = True
                except:
                    register_clicked = False

                # 2) Fallback: button text
                if not register_clicked:
                    try:
                        btn = popup.locator("button:has-text('Register')").first
                        btn.wait_for(state="visible", timeout=3000)
                        btn.click()
                        popup.wait_for_timeout(800)
                        self.log("✅ Clicked 'Register' (text selector)", 'success')
                        register_clicked = True
                    except:
                        register_clicked = False

                # 3) Fallback: CSS class
                if not register_clicked:
                    try:
                        btn = popup.locator("button.zoom-button.zoom-button--primary").first
                        btn.wait_for(state="visible", timeout=2000)
                        btn.click()
                        popup.wait_for_timeout(800)
                        self.log("✅ Clicked 'Register' (class selector)", 'success')
                        register_clicked = True
                    except:
                        register_clicked = False

                # 4) Last resort: evaluate a DOM click (works when Playwright click is blocked)
                if not register_clicked:
                    try:
                        btn = popup.locator("button:has-text('Register')").first
                        popup.evaluate("(el) => el.click()", btn)
                        popup.wait_for_timeout(800)
                        self.log("✅ Clicked 'Register' (DOM eval)", 'success')
                        register_clicked = True
                    except:
                        register_clicked = False

                if not register_clicked:
                    raise RuntimeError("register-button-click-failed")

            except Exception:
                self.log("⚠️ Could not click register button automatically; please click it manually", 'warning')
            
            # Wait for "Open Zoom" button
            try:
                popup.locator("button", has_text="Open").wait_for(state="visible", timeout=5000)
                self.log("⚠️ POPUP DETECTED - Please check browser!", 'warning')
                self.log("👉 Click the 'Open Zoom' button manually in the browser", 'warning')
                self.update_status("⚠️ Manual action needed - Check browser", 'warning')
                
                # Try to click, but it might not work due to browser restrictions
                try:
                    popup.locator("button", has_text="Open").click()
                    self.log("✅ Attempted to click 'Open Zoom'", 'info')
                except:
                    self.log("ℹ️ Automatic click failed - Please click manually", 'info')
                
            except:
                self.log("ℹ️ 'Open Zoom' button not found - Please handle manually", 'info')
            
            # Keep popup open for manual interaction
            self.log("✅ Registration complete - Browser will remain open", 'success')
            self.log("👉 Please check browser for any additional steps", 'info')
            self.update_status("✅ Form submitted - Check browser", 'success')
            
        except Exception as e:
            self.log(f"⚠️ Form filling error: {str(e)}", 'warning')
            self.log("👉 Please fill the form manually in the browser", 'warning')
            self.update_status("⚠️ Manual form fill needed", 'warning')