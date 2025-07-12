import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TistoryPoster:
    def __init__(self):
        self.tistory_username = os.getenv('TISTORY_USERNAME')
        self.tistory_password = os.getenv('TISTORY_PASSWORD')
        self.tistory_url = os.getenv('TISTORY_URL')
        
        if not self.tistory_username:
            raise ValueError("TISTORY_USERNAME environment variable is required")
        if not self.tistory_password:
            raise ValueError("TISTORY_PASSWORD environment variable is required")
        if not self.tistory_url:
            raise ValueError("TISTORY_URL environment variable is required")
    
    def setup_chrome_driver(self):
        """Setup Chrome WebDriver with headless mode for GitHub Actions"""
        chrome_options = Options()
        # Enable headless mode for GitHub Actions
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        print("[DEBUG] Setting up Chrome WebDriver...")
        
        # Use ChromeDriverManager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"[DEBUG] WebDriver created successfully")
        return driver
    
    def login_to_tistory(self, driver):
        """Login to Tistory using Kakao account"""
        try:
            print("[DEBUG] Starting Tistory login process...")
            
            # Navigate to Tistory login page
            login_url = "https://www.tistory.com/auth/login"
            print(f"[DEBUG] Navigating to: {login_url}")
            driver.get(login_url)
            
            print(f"[DEBUG] Current URL after navigation: {driver.current_url}")
            print(f"[DEBUG] Page title: {driver.title}")
            
            # Wait for page to be fully loaded
            print("[DEBUG] Waiting for page to be fully loaded...")
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for JavaScript to complete execution
            WebDriverWait(driver, 2).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for Kakao login button to load with multiple selectors
            print("[DEBUG] Waiting for Kakao login button to load...")
            kakao_login_button = None
            
            # Try different selectors for Kakao login button
            kakao_selectors = [
                "#cMain > div > div > div > a.btn_login.link_kakao_id",
                "a.btn_login.link_kakao_id",
                "a[href*='kakao']",
                ".link_kakao_id"
            ]
            
            for selector in kakao_selectors:
                try:
                    kakao_login_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Kakao login button found using selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[DEBUG] Selector {selector} not found, trying next...")
                    continue
            
            if not kakao_login_button:
                print("[DEBUG] Kakao login button not found with any selector, trying alternative approach...")
                # Try finding by text content
                kakao_login_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '카카오') or contains(@class, 'kakao')]"))
                )
                print("[DEBUG] Kakao login button found by text/class content")
            
            # Click Kakao login button
            kakao_login_button.click()
            print("[DEBUG] Kakao login button clicked")
            
            # Wait for Kakao login page to load
            print("[DEBUG] Waiting for Kakao login page...")
            
            # Wait for URL change to confirm navigation
            WebDriverWait(driver, 5).until(
                lambda d: "kakao" in d.current_url.lower() or "accounts" in d.current_url.lower()
            )
            
            print(f"[DEBUG] Current URL after Kakao button click: {driver.current_url}")
            print(f"[DEBUG] Page title: {driver.title}")
            
            # Wait for page to be fully loaded
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for Kakao login form with multiple attempts
            print("[DEBUG] Waiting for Kakao login form...")
            email_field = None
            
            # Try multiple selectors for email field
            email_selectors = ["#loginId--1", "input[type='email']"]
            
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Email field found using selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[DEBUG] Email selector {selector} not found, trying next...")
                    continue
            
            if not email_field:
                # Fallback to name attribute
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
                print("[DEBUG] Email field found using name attribute")
            
            print("[DEBUG] Kakao login form loaded")
            
            # Fill email field (already found above)
            print("[DEBUG] Filling email field...")
            email_field.clear()
            email_field.send_keys(self.tistory_username)
            print(f"[DEBUG] Email entered: {self.tistory_username}")
            
            # Find and fill password field with multiple selectors
            print("[DEBUG] Finding password field...")
            password_field = None
            
            password_selectors = ["input[name='password']", "#password--2", "input[type='password']"]
            
            for selector in password_selectors:
                try:
                    password_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Password field found using selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[DEBUG] Password selector {selector} not found, trying next...")
                    continue
            
            if not password_field:
                # Fallback to name attribute
                password_field = driver.find_element(By.NAME, "password")
                print("[DEBUG] Password field found using name attribute")
            
            password_field.clear()
            password_field.send_keys(self.tistory_password)
            print("[DEBUG] Password entered")
            
            # Click login button with multiple selectors
            print("[DEBUG] Looking for Kakao login submit button...")
            login_submit_button = None
            
            submit_selectors = [
                "button[type='submit']",
                ".btn_confirm",
                ".btn_login",
                "input[type='submit']",
                "button.submit"
            ]
            
            for selector in submit_selectors:
                try:
                    login_submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Submit button found using selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[DEBUG] Submit selector {selector} not found, trying next...")
                    continue
            
            if not login_submit_button:
                # Fallback to text-based search
                login_submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '로그인') or contains(text(), '확인')]"))
                )
                print("[DEBUG] Submit button found by text content")
            
            print(f"[DEBUG] Kakao login submit button found: {login_submit_button.text}")
            login_submit_button.click()
            print("[DEBUG] Kakao login submit button clicked")
            
            # Wait for login to complete with better detection
            print("[DEBUG] Waiting for login to complete...")
            
            # Check for various possible outcomes after login
            for attempt in range(30):  # Check for 30 seconds
                current_url = driver.current_url
                page_title = driver.title
                
                print(f"[DEBUG] Attempt {attempt + 1}: URL = {current_url}")
                print(f"[DEBUG] Attempt {attempt + 1}: Title = {page_title}")
                
                # Check for successful redirect to Tistory
                if "tistory.com" in current_url and "login" not in current_url.lower():
                    print("[DEBUG] ✅ Login successful - redirected to Tistory")
                    return True
                
                # Check for 2FA (Two-Factor Authentication) page
                two_factor_indicators = [
                    "2fa" in current_url.lower(),
                    "verify" in current_url.lower(),
                    "인증" in page_title,
                    "verification" in page_title.lower(),
                    "보안" in page_title,
                    len(driver.find_elements(By.CSS_SELECTOR, ".verification, .two-factor, .sms-auth")) > 0
                ]
                
                if any(two_factor_indicators):
                    print("[DEBUG] 🔐 2FA/Verification page detected")
                    print(f"[DEBUG] Current URL: {current_url}")
                    print(f"[DEBUG] Page title: {page_title}")
                    
                    # Take screenshot of 2FA page
                    driver.save_screenshot("2fa_page.png")
                    print("[DEBUG] 2FA page screenshot saved as 2fa_page.png")
                    
                    # Look for SMS verification input
                    sms_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], input[name*='code'], input[name*='verification']")
                    if sms_inputs:
                        print("[DEBUG] 📱 SMS verification input found")
                        print("[DEBUG] Please enter the verification code you received via SMS")
                        
                        # Wait for user to enter verification code
                        verification_entered = False
                        for i in range(300):  # Wait up to 5 minutes for verification
                            time.sleep(1)
                            
                            # Re-find SMS inputs to avoid stale element reference
                            try:
                                current_sms_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], input[name*='code'], input[name*='verification']")
                                
                                # Check if user has entered something
                                for sms_input in current_sms_inputs:
                                    try:
                                        if sms_input.get_attribute("value"):
                                            print(f"[DEBUG] Verification code entered: {sms_input.get_attribute('value')}")
                                            verification_entered = True
                                            break
                                    except:
                                        # Element became stale, continue with next
                                        continue
                                
                                if verification_entered:
                                    break
                                    
                                # Check if we've been redirected (verification completed)
                                if "tistory.com" in driver.current_url and "login" not in driver.current_url.lower():
                                    print("[DEBUG] ✅ 2FA completed - redirected to Tistory")
                                    return True
                            except:
                                # If we can't find inputs anymore, check if redirected
                                if "tistory.com" in driver.current_url and "login" not in driver.current_url.lower():
                                    print("[DEBUG] ✅ 2FA completed - redirected to Tistory")
                                    return True
                            
                            if i % 30 == 0:
                                print(f"[DEBUG] Waiting for verification code entry... ({i + 1}/300 seconds)")
                        
                        if not verification_entered:
                            print("[DEBUG] ❌ No verification code entered within timeout")
                            return False
                    
                    # Look for continue/proceed buttons after 2FA
                    try:
                        continue_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '계속하기') or contains(text(), '계속') or contains(text(), '확인') or contains(text(), 'Continue') or contains(text(), 'Proceed')]")
                        if continue_buttons:
                            for btn in continue_buttons:
                                try:
                                    if btn.is_displayed() and btn.is_enabled():
                                        print(f"[DEBUG] Found continue button: {btn.text}")
                                        btn.click()
                                        print("[DEBUG] Continue button clicked")
                                        time.sleep(2)
                                        break
                                except:
                                    # Button became stale, continue with next
                                    continue
                    except:
                        # If no continue buttons found, continue with flow
                        pass
                    
                    # Continue waiting for 2FA completion
                    print("[DEBUG] Waiting for 2FA completion...")
                    for i in range(120):  # Wait up to 2 minutes for 2FA
                        time.sleep(1)
                        
                        # Check for continue buttons during wait
                        try:
                            continue_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '계속하기') or contains(text(), '계속') or contains(text(), '확인') or contains(text(), 'Continue') or contains(text(), 'Proceed')]")
                            if continue_buttons:
                                for btn in continue_buttons:
                                    try:
                                        if btn.is_displayed() and btn.is_enabled():
                                            print(f"[DEBUG] Found continue button during wait: {btn.text}")
                                            btn.click()
                                            print("[DEBUG] Continue button clicked during wait")
                                            time.sleep(2)
                                            break
                                    except:
                                        # Button became stale, continue with next
                                        continue
                            else:
                                # If no continue button, try clicking login button again (might be enabled after 2FA)
                                login_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '로그인')]")
                                if login_buttons:
                                    for btn in login_buttons:
                                        try:
                                            if btn.is_displayed() and btn.is_enabled():
                                                print(f"[DEBUG] Found login button during wait: {btn.text}")
                                                btn.click()
                                                print("[DEBUG] Login button clicked during wait")
                                                time.sleep(2)
                                                break
                                        except:
                                            # Button became stale, continue with next
                                            continue
                        except:
                            # If element finding fails, continue with next iteration
                            pass
                        
                        if "tistory.com" in driver.current_url and "login" not in driver.current_url.lower():
                            print("[DEBUG] ✅ 2FA completed - redirected to Tistory")
                            return True
                        if i % 10 == 0:
                            print(f"[DEBUG] Waiting for 2FA completion... ({i + 1}/120 seconds)")
                    print("[DEBUG] ❌ 2FA timeout")
                    return False
                
                # Check for error messages
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".error_box, .msg_error, .error_msg, .alert")
                if error_elements:
                    for error in error_elements:
                        if error.is_displayed():
                            print(f"[DEBUG] ❌ Error found: {error.text}")
                
                # Check for login form still present (login failed)
                if "accounts.kakao.com" in current_url and "login" in current_url:
                    login_form = driver.find_elements(By.CSS_SELECTOR, "form, .login_form")
                    if login_form:
                        print("[DEBUG] ❌ Still on login page - login may have failed")
                        # Take a screenshot for debugging
                        driver.save_screenshot(f"login_debug_{attempt}.png")
                        print(f"[DEBUG] Screenshot saved as login_debug_{attempt}.png")
                        
                        # Check for specific error indicators
                        if "error" in current_url.lower():
                            print("[DEBUG] Error detected in URL")
                        
                        # Look for captcha or additional verification
                        captcha_elements = driver.find_elements(By.CSS_SELECTOR, ".captcha, .recaptcha")
                        if captcha_elements:
                            print("[DEBUG] 🤖 Captcha detected - manual intervention required")
                            return False
                
                # Check page source for debugging
                if attempt % 5 == 0:  # Every 5 attempts
                    page_source_snippet = driver.page_source[:500]
                    print(f"[DEBUG] Page source snippet: {page_source_snippet}")
                
                time.sleep(1)
            
            print("[DEBUG] ❌ Login timeout - final check")
            final_url = driver.current_url
            print(f"[DEBUG] Final URL: {final_url}")
            
            # Final screenshot
            driver.save_screenshot("login_final_state.png")
            print("[DEBUG] Final screenshot saved as login_final_state.png")
            
            return False
            
        except Exception as e:
            print(f"[DEBUG] Error during login: {e}")
            print(f"[DEBUG] Current URL: {driver.current_url}")
            # Take a screenshot for debugging
            try:
                driver.save_screenshot("login_exception.png")
                print("[DEBUG] Screenshot saved as login_exception.png")
            except:
                pass
            return False
    
    def post_to_tistory(self, driver, title, content, tags):
        """Post content to Tistory blog"""
        try:
            print("[DEBUG] Starting Tistory posting process...")
            
            # Navigate to write page using the configured URL
            blog_url = f"{self.tistory_url}/manage/newpost/"
            print(f"[DEBUG] Navigating to: {blog_url}")
            driver.get(blog_url)
            
            # Handle any alert that might pop up immediately
            time.sleep(2)
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"[DEBUG] Initial alert detected: {alert_text}")
                alert.dismiss()  # Dismiss any initial alert
                print("[DEBUG] Initial alert dismissed")
            except:
                print("[DEBUG] No initial alert found")
            
            print(f"[DEBUG] Current URL: {driver.current_url}")
            print(f"[DEBUG] Page title: {driver.title}")
            
            # Wait for the page to load
            print("[DEBUG] Waiting for write page to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Handle potential alert about saved draft - try multiple times
            for attempt in range(3):
                try:
                    print(f"[DEBUG] Checking for alert (attempt {attempt + 1})")
                    time.sleep(1)  # Wait a bit for alert to appear
                    
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    print(f"[DEBUG] Alert detected: {alert_text}")
                    
                    if "저장된 글이 있습니다" in alert_text or "이어서 작성하시겠습니까" in alert_text:
                        print("[DEBUG] Found saved draft alert - dismissing to start fresh")
                        alert.dismiss()  # Click "아니오" to start fresh
                    else:
                        print("[DEBUG] Accepting alert")
                        alert.accept()
                        
                    print("[DEBUG] Alert handled successfully")
                    break
                except:
                    print(f"[DEBUG] No alert found on attempt {attempt + 1}")
                    if attempt == 2:
                        print("[DEBUG] No alert found after 3 attempts")
            
            # Wait for JavaScript to complete
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Take screenshot of write page
            driver.save_screenshot("write_page.png")
            print("[DEBUG] Write page screenshot saved as write_page.png")
            
            # Try different selectors for title input
            print("[DEBUG] Looking for title input field...")
            title_input = None
            title_selectors = [
                "#post-title-inp",
                "input[placeholder='제목을 입력하세요']",
                "input[placeholder*='제목']",
                "#title", 
                "input[name='title']", 
                ".title-input"
            ]
            
            for selector in title_selectors:
                try:
                    title_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Title input found using selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[DEBUG] Title selector {selector} not found, trying next...")
                    continue
            
            if not title_input:
                print("[DEBUG] ❌ Title input not found")
                return False
            
            # Enter title
            print(f"[DEBUG] Entering title: {title}")
            title_input.clear()
            title_input.send_keys(title)
            
            # Switch to Markdown mode for content editing
            print("[DEBUG] Switching to Markdown mode...")
            try:
                # Click editor mode button
                editor_mode_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-layer-btn-open"))
                )
                editor_mode_btn.click()
                print("[DEBUG] Editor mode button clicked")
                
                # Wait for the layer to appear and click Markdown mode
                markdown_mode_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-markdown"))
                )
                markdown_mode_btn.click()
                print("[DEBUG] Markdown mode button clicked")
                
                # Handle alert
                try:
                    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                    alert_text = alert.text
                    print(f"[DEBUG] Alert detected: {alert_text}")
                    alert.accept()
                    print("[DEBUG] Alert accepted")
                except:
                    print("[DEBUG] No alert found or alert already handled")
                
                # Wait for Markdown editor to load
                time.sleep(2)
                print("[DEBUG] Markdown editor mode activated")
                
            except Exception as e:
                print(f"[DEBUG] Error switching to Markdown mode: {e}")
                print("[DEBUG] Continuing with default editor mode")
            
            # Look for content editor
            print("[DEBUG] Looking for content editor...")
            
            # Try different approaches for content editor
            content_editor = None
            content_selectors = [
                "#markdown-editor-container > div.mce-edit-area > div > div > div.CodeMirror-scroll > div.CodeMirror-sizer > div > div > div > div.CodeMirror-code > div > pre",
                "#markdown-editor-container .CodeMirror-code pre",
                ".CodeMirror-code pre",
                "iframe#editor-tistory_ifr",
                "div[contenteditable='true']",
                ".ProseMirror",
                ".ql-editor",
                "#content", 
                ".editor-content", 
                "textarea[name='content']",
                "iframe[title='Rich Text Area']",
                ".fr-element"
            ]
            
            for selector in content_selectors:
                try:
                    content_editor = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Content editor found using selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[DEBUG] Content selector {selector} not found, trying next...")
                    continue
            
            if content_editor:
                print(f"[DEBUG] Entering content...")
                
                # Check if this is the Markdown editor (CodeMirror)
                if "CodeMirror" in content_editor.get_attribute("class") or content_editor.tag_name == "pre":
                    # Markdown editor with CodeMirror
                    try:
                        # Wait for CodeMirror to be ready
                        time.sleep(3)
                        
                        # CodeMirror 내부의 실제 textarea 찾아서 send_keys로 입력
                        textareas = driver.find_elements(By.CSS_SELECTOR, ".CodeMirror textarea")
                        print(f"[DEBUG] Found {len(textareas)} textareas")
                        
                        editor = None
                        for i, textarea in enumerate(textareas):
                            print(f"[DEBUG] Checking textarea {i}: visible={textarea.is_displayed()}, enabled={textarea.is_enabled()}")
                            if textarea.is_displayed() and textarea.is_enabled():
                                editor = textarea
                                print(f"[DEBUG] Using textarea {i}")
                                break
                        
                        if not editor and textareas:
                            editor = textareas[-1]  # 마지막 textarea 사용
                            print(f"[DEBUG] Fallback to last textarea")
                        
                        if editor:
                            # 스크롤하여 보이게 하기
                            driver.execute_script("arguments[0].scrollIntoView(true);", editor)
                            time.sleep(0.5)
                            
                            # 클릭하여 포커스
                            try:
                                editor.click()
                                time.sleep(0.5)
                                print("[DEBUG] Textarea clicked successfully")
                            except:
                                print("[DEBUG] Click failed, trying to focus with JavaScript")
                                driver.execute_script("arguments[0].focus();", editor)
                                time.sleep(0.5)
                            
                            # 마크다운 형태로 내용 입력
                            editor.send_keys(content)
                            print("[DEBUG] Content entered into Markdown editor via textarea")
                        else:
                            raise Exception("No suitable textarea found")
                        
                    except Exception as e:
                        print(f"[DEBUG] Error with textarea approach: {e}")
                        # Try JavaScript approach as fallback
                        try:
                            # Use JavaScript to set content in CodeMirror
                            driver.execute_script("""
                                var editor = document.querySelector('.CodeMirror').CodeMirror;
                                if (editor) {
                                    editor.setValue(arguments[0]);
                                    editor.refresh();
                                }
                            """, content)
                            print("[DEBUG] Content entered into Markdown editor using JavaScript")
                        except Exception as e2:
                            print(f"[DEBUG] Error with JavaScript approach: {e2}")
                            # Try direct send_keys as final fallback
                            try:
                                # Scroll to element
                                driver.execute_script("arguments[0].scrollIntoView(true);", content_editor)
                                time.sleep(1)
                                
                                # Click to focus
                                content_editor.click()
                                time.sleep(1)
                                
                                # Try to clear and send keys
                                content_editor.clear()
                                content_editor.send_keys(content)
                                print("[DEBUG] Content entered into Markdown editor via direct send_keys")
                            except Exception as e3:
                                print(f"[DEBUG] All approaches failed: {e3}")
                                return False
                # Handle other editor types
                elif content_editor.tag_name == "iframe" or content_editor.get_attribute("id") == "editor-tistory_ifr":
                    # Handle Tistory iframe specifically
                    try:
                        driver.switch_to.frame(content_editor)
                        content_body = driver.find_element(By.TAG_NAME, "body")
                        
                        # Use send_keys for plain text input
                        content_body.clear()
                        content_body.send_keys(content)
                        print("[DEBUG] Content entered via send_keys in iframe")
                        
                        driver.switch_to.default_content()
                        print("[DEBUG] Content entered into Tistory iframe")
                    except Exception as e:
                        print(f"[DEBUG] Error with iframe: {e}")
                        driver.switch_to.default_content()
                        # Try direct approach with send_keys
                        content_editor.clear()
                        content_editor.send_keys(content)
                        print("[DEBUG] Content entered directly after iframe error")
                else:
                    # Direct content editor
                    content_editor.clear()
                    content_editor.send_keys(content)
                    print("[DEBUG] Content entered directly")
            else:
                print("[DEBUG] ❌ Content editor not found")
                return False
            
            # Add tags if available
            if tags:
                print(f"[DEBUG] Adding tags: {tags}")
                tag_selectors = ["#tagText", "input[name='tag']", ".tag-input"]
                
                for selector in tag_selectors:
                    try:
                        tag_input = driver.find_element(By.CSS_SELECTOR, selector)
                        tag_input.clear()
                        tag_input.send_keys(tags)
                        print(f"[DEBUG] Tags added using selector: {selector}")
                        break
                    except:
                        print(f"[DEBUG] Tag selector {selector} not found, trying next...")
                        continue
            
            time.sleep(3)

            # Look for publish button
            print("[DEBUG] Looking for publish button...")
            publish_selectors = [
                "#publish-layer-btn",
                "button:contains('발행')",
                "button:contains('게시')",
                "button:contains('저장')",
                "button[data-action='publish']",
                ".btn-publish",
                "button[type='submit']",
                "input[type='submit']",
                ".publish-btn"
            ]
            
            for selector in publish_selectors:
                try:
                    publish_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"[DEBUG] Publish button found using selector: {selector}")
                    publish_btn.click()
                    print("[DEBUG] Publish button clicked")
                    break
                except:
                    print(f"[DEBUG] Publish selector {selector} not found, trying next...")
                    continue
            else:
                # Try XPath for text-based search
                try:
                    publish_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '발행') or contains(text(), '게시') or contains(text(), '저장')]"))
                    )
                    print("[DEBUG] Publish button found using XPath")
                    publish_btn.click()
                    print("[DEBUG] Publish button clicked")
                except:
                    print("[DEBUG] ❌ Publish button not found")
                    return False
            
            # Wait for publish layer to appear
            print("[DEBUG] Waiting for publish layer to appear...")
            time.sleep(2)
            
            # Set post to public (공개)
            try:
                print("[DEBUG] Setting post to public...")
                public_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='radio'][id='open20'][value='20']"))
                )
                public_radio.click()
                print("[DEBUG] Public radio button clicked")
            except Exception as e:
                print(f"[DEBUG] Could not find public radio button: {e}")
                # Try alternative selector
                try:
                    public_radio = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='basicSet'][value='20']"))
                    )
                    public_radio.click()
                    print("[DEBUG] Public radio button clicked (alternative selector)")
                except:
                    print("[DEBUG] ❌ Could not set post to public")
            
            # Click final publish button
            try:
                print("[DEBUG] Looking for final publish button...")
                final_publish_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#publish-btn"))
                )
                final_publish_btn.click()
                print("[DEBUG] Final publish button clicked")
            except Exception as e:
                print(f"[DEBUG] Could not find final publish button: {e}")
                # Try alternative selectors
                try:
                    final_publish_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '공개 발행')]"))
                    )
                    final_publish_btn.click()
                    print("[DEBUG] Final publish button clicked (XPath)")
                except:
                    print("[DEBUG] ❌ Could not find final publish button")
                    return False
            
            # Wait for confirmation or success message
            print("[DEBUG] Waiting for post confirmation...")
            time.sleep(5)
            
            # Take screenshot of result
            driver.save_screenshot("post_result.png")
            print("[DEBUG] Post result screenshot saved as post_result.png")
            
            print("[DEBUG] ✅ Post completed successfully")
            return True
            
        except Exception as e:
            print(f"[DEBUG] ❌ Error posting to Tistory: {e}")
            driver.save_screenshot("post_error.png")
            print("[DEBUG] Error screenshot saved as post_error.png")
            return False


def test_tistory_poster():
    """Test function for Tistory posting functionality"""
    print("Testing Tistory posting functionality...")
    
    # Test data
    test_title = "테스트 포스트 제목"
    test_content = """## 테스트 포스트입니다

이것은 **테스트** 포스트의 내용입니다.

### 주요 특징

- 마크다운 형식 지원
- 자동 포스팅 기능
- 태그 추가 가능

> 인용문 테스트입니다.

[링크 테스트](#)"""
    
    test_tags = "테스트, 자동포스팅, 마크다운"
    
    poster = TistoryPoster()
    driver = None
    
    try:
        # Setup Chrome driver
        driver = poster.setup_chrome_driver()
        print("Chrome driver setup successful")
        
        # Test login
        if poster.login_to_tistory(driver):
            print("Login successful")
            
            # Test posting
            if poster.post_to_tistory(driver, test_title, test_content, test_tags):
                print("Post successful")
            else:
                print("Post failed")
        else:
            print("Login failed")
            
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        if driver:
            driver.quit()
    
    print("Tistory poster test completed!")


if __name__ == "__main__":
    test_tistory_poster()