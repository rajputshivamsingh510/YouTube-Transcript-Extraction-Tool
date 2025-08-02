import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    NoSuchElementException, 
    ElementNotInteractableException, 
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import os

# Config
CHROMEDRIVER_PATH = "chromedriver.exe"
GOOGLE_SHEET_CSV = "https://docs.google.com/spreadsheets/d/1cZy-PhqwI9lT_mDm5sfe59cPJqwjh6IgSMS9n27l-bQ/export?format=csv"
OUTPUT_EXCEL = "youtube_transcripts_output.xlsx"

# Setup Chrome driver with additional options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Set up WebDriverWait
wait = WebDriverWait(driver, 10)

# Load video URLs from Google Sheet
df_links = pd.read_csv(GOOGLE_SHEET_CSV)
print(f"✅ Loaded {len(df_links)} rows from Google Sheet.")

transcripts = []

def safe_click(element, driver):
    """Safely click an element using multiple methods"""
    try:
        # Method 1: Regular click
        element.click()
        return True
    except ElementClickInterceptedException:
        try:
            # Method 2: JavaScript click
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                # Method 3: ActionChains click
                ActionChains(driver).move_to_element(element).click().perform()
                return True
            except:
                return False

def debug_page_structure(driver):
    """Debug function to understand page structure"""
    try:
        print("🔍 DEBUG: Analyzing page structure...")
        
        # Look for any elements containing "transcript" in various attributes
        transcript_related = driver.find_elements(By.XPATH, "//*[contains(@class, 'transcript') or contains(@id, 'transcript') or contains(@aria-label, 'transcript') or contains(text(), 'transcript')]")
        print(f"🔍 Found {len(transcript_related)} elements related to 'transcript'")
        
        for i, elem in enumerate(transcript_related[:5]):  # Show first 5
            try:
                print(f"  Element {i+1}: {elem.tag_name}, class='{elem.get_attribute('class')}', id='{elem.get_attribute('id')}', text='{elem.text[:50]}'")
            except:
                pass
        
        # Look for elements that might contain timestamps (pattern like 0:00, 1:23, etc.)
        timestamp_elements = driver.find_elements(By.XPATH, "//*[contains(text(), ':') and string-length(text()) < 10]")
        print(f"🔍 Found {len(timestamp_elements)} potential timestamp elements")
        
        for i, elem in enumerate(timestamp_elements[:5]):  # Show first 5
            try:
                if ':' in elem.text and len(elem.text.strip()) < 10:
                    print(f"  Timestamp {i+1}: '{elem.text}' in {elem.tag_name}")
            except:
                pass
                
        # Check if transcript panel is visible
        transcript_panels = driver.find_elements(By.XPATH, "//*[contains(@class, 'transcript') and contains(@class, 'panel')]")
        print(f"🔍 Found {len(transcript_panels)} transcript panels")
        
    except Exception as e:
        print(f"🔍 DEBUG error: {e}")

def extract_transcript_from_url(url, driver, wait):
    """Extract transcript from a single YouTube URL"""
    print(f"\n🔗 Processing: {url}")
    
    try:
        driver.get(url)
        sleep(3)  # Wait for page to load
        
        # Wait for the page to be ready
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Step 1: Try to expand description (optional step)
        try:
            more_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-button[@id='expand']")))
            safe_click(more_btn, driver)
            sleep(2)
            print("✅ Expanded description")
        except (NoSuchElementException, TimeoutException):
            print("⚠️ 'More' button not found or not needed")
        
        # Step 2: Find and click "Show transcript" button
        transcript_selectors = [
            "//button[contains(@aria-label, 'Show transcript')]",
            "//button[contains(text(), 'Show transcript')]",
            "//yt-button-shape/button[contains(text(), 'Show transcript')]",
            "//ytd-button-renderer//button[contains(@aria-label, 'transcript')]"
        ]
        
        show_transcript_btn = None
        for selector in transcript_selectors:
            try:
                show_transcript_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                break
            except TimeoutException:
                continue
        
        if not show_transcript_btn:
            print("⚠️ 'Show transcript' button not found")
            return []
        
        # Scroll the button into view
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_transcript_btn)
        sleep(1)
        
        # Try to click the transcript button
        if not safe_click(show_transcript_btn, driver):
            print("⚠️ Could not click 'Show transcript' button")
            return []
        
        print("✅ Clicked 'Show transcript' button")
        sleep(3)  # Wait for transcript to load
        
        # Debug the page structure
        debug_page_structure(driver)
        
        # Step 3: Extract transcript segments with extended wait time
        print("🔍 Looking for transcript container...")
        
        # Wait longer for transcript to fully load
        sleep(5)
        
        # More comprehensive selectors for transcript container
        transcript_selectors = [
            "//ytd-transcript-segment-list-renderer[@id='body']",
            "//ytd-transcript-segment-list-renderer",
            "//div[contains(@class, 'ytd-transcript-segment-list-renderer')]",
            "//*[@id='segments-container']",
            "//*[contains(@class, 'segment-list')]",
            "//div[contains(@class, 'transcript')]//div[contains(@class, 'segment')]/.."
        ]
        
        transcript_box = None
        for i, selector in enumerate(transcript_selectors):
            try:
                print(f"🔍 Trying selector {i+1}: {selector}")
                transcript_box = driver.find_element(By.XPATH, selector)
                print(f"✅ Found transcript container with selector {i+1}")
                break
            except NoSuchElementException:
                print(f"❌ Selector {i+1} failed")
                continue
        
        if not transcript_box:
            print("⚠️ Transcript container not found with any selector")
            # Debug: Print page source around transcript area
            try:
                body_html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
                if "transcript" in body_html.lower():
                    print("🔍 'transcript' found in page HTML - container might have different structure")
                    # Try to find any element containing transcript-related classes
                    transcript_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'transcript') or contains(@id, 'transcript')]")
                    print(f"🔍 Found {len(transcript_elements)} elements with 'transcript' in class/id")
                    for elem in transcript_elements[:3]:  # Check first 3
                        print(f"🔍 Element: {elem.tag_name}, class: {elem.get_attribute('class')}, id: {elem.get_attribute('id')}")
                else:
                    print("❌ No 'transcript' text found in page HTML")
            except Exception as debug_e:
                print(f"❌ Debug error: {debug_e}")
            return []
        
        # Look for transcript segments with multiple selectors
        segment_selectors = [
            ".//ytd-transcript-segment-renderer",
            ".//div[contains(@class, 'segment')]",
            ".//div[contains(@class, 'transcript-segment')]",
            ".//*[contains(@class, 'segment-timestamp')]/..",
            ".//*[contains(text(), ':')]/.."  # Look for elements containing timestamps
        ]
        
        segments = []
        for i, selector in enumerate(segment_selectors):
            try:
                print(f"🔍 Looking for segments with selector {i+1}: {selector}")
                segments = transcript_box.find_elements(By.XPATH, selector)
                if segments:
                    print(f"✅ Found {len(segments)} segments with selector {i+1}")
                    break
                else:
                    print(f"❌ No segments found with selector {i+1}")
            except Exception as e:
                print(f"❌ Selector {i+1} error: {e}")
                continue
        
        if not segments:
            print("⚠️ No transcript segments found")
            # Additional debug info
            try:
                container_html = transcript_box.get_attribute("innerHTML")[:500]  # First 500 chars
                print(f"🔍 Container HTML preview: {container_html}")
            except:
                pass
            return []
        
        print(f"🔍 Processing {len(segments)} transcript segments...")
        lines = []
        
        for i, segment in enumerate(segments):
            try:
                # Multiple approaches to extract timestamp and text
                timestamp = None
                text = None
                
                # Approach 1: Look for specific classes
                timestamp_selectors = [
                    ".//div[contains(@class, 'segment-timestamp')]",
                    ".//span[contains(@class, 'segment-timestamp')]",
                    ".//*[contains(@class, 'timestamp')]",
                    ".//div[contains(@class, 'time')]"
                ]
                
                text_selectors = [
                    ".//div[contains(@class, 'segment-text')]",
                    ".//span[contains(@class, 'segment-text')]",
                    ".//*[contains(@class, 'text')]",
                    ".//div[not(contains(@class, 'timestamp')) and not(contains(@class, 'time'))]"
                ]
                
                # Try to find timestamp
                for ts_selector in timestamp_selectors:
                    try:
                        timestamp_elem = segment.find_element(By.XPATH, ts_selector)
                        timestamp = timestamp_elem.text.strip()
                        if timestamp and ':' in timestamp:  # Basic validation
                            break
                    except NoSuchElementException:
                        continue
                
                # Try to find text
                for text_selector in text_selectors:
                    try:
                        text_elem = segment.find_element(By.XPATH, text_selector)
                        text = text_elem.text.strip()
                        if text and text != timestamp:  # Make sure it's not the timestamp
                            break
                    except NoSuchElementException:
                        continue
                
                # Fallback: try to extract from segment's direct text
                if not timestamp or not text:
                    segment_text = segment.text.strip()
                    if segment_text and ':' in segment_text:
                        # Try to split timestamp from text
                        parts = segment_text.split('\n', 1)
                        if len(parts) == 2:
                            potential_timestamp = parts[0].strip()
                            potential_text = parts[1].strip()
                            if ':' in potential_timestamp and len(potential_timestamp) < 20:
                                timestamp = timestamp or potential_timestamp
                                text = text or potential_text
                
                if timestamp and text:
                    lines.append({
                        "url": url, 
                        "timestamp": timestamp, 
                        "text": text
                    })
                    if i < 3:  # Show first few for debugging
                        print(f"✅ Segment {i+1}: {timestamp} - {text[:50]}...")
                elif i < 5:  # Debug first few failed segments
                    print(f"❌ Segment {i+1} failed - segment text: '{segment.text[:100]}'")
                    
            except Exception as e:
                if i < 5:  # Only show errors for first few segments
                    print(f"❌ Error processing segment {i+1}: {e}")
        
        if lines:
            print(f"✅ Fetched {len(lines)} transcript lines")
        else:
            print("⚠️ No transcript lines found")
        
        return lines
        
    except Exception as e:
        print(f"❌ Error processing {url}: {str(e)}")
        return []

# Main processing loop
for idx, row in df_links.iterrows():
    # Fix the deprecation warning by using .iloc
    url = row.iloc[0] if hasattr(row, 'iloc') else str(row.values[0])
    
    transcript_lines = extract_transcript_from_url(url, driver, wait)
    transcripts.extend(transcript_lines)
    
    # Small delay between videos to be respectful
    sleep(2)

# Save transcripts to Excel
if transcripts:
    df_transcripts = pd.DataFrame(transcripts)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_EXCEL) if os.path.dirname(OUTPUT_EXCEL) else '.', exist_ok=True)
    
    # Try to save to Excel, with fallback filename if file is locked
    saved_successfully = False
    attempt = 0
    
    while not saved_successfully and attempt < 5:
        try:
            current_filename = OUTPUT_EXCEL if attempt == 0 else f"youtube_transcripts_output_{attempt}.xlsx"
            df_transcripts.to_excel(current_filename, index=False)
            print(f"\n✅ All transcripts saved to: {current_filename}")
            saved_successfully = True
        except PermissionError:
            attempt += 1
            if attempt < 5:
                print(f"⚠️ File locked, trying alternative filename...")
            else:
                print(f"❌ Could not save Excel file after {attempt} attempts.")
                print("💡 Please close the Excel file if it's open and run the script again.")
                # Save as CSV as backup
                csv_filename = OUTPUT_EXCEL.replace('.xlsx', '.csv')
                df_transcripts.to_csv(csv_filename, index=False)
                print(f"📄 Saved as CSV instead: {csv_filename}")
                saved_successfully = True
    
    if saved_successfully:
        print(f"📊 Total transcript lines extracted: {len(transcripts)}")
        print(f"📊 Videos processed: {df_transcripts['url'].nunique()}")
        
        # Show sample of extracted data
        print(f"\n📋 Sample transcript data:")
        for i, row in df_transcripts.head().iterrows():
            print(f"  {row['timestamp']} - {row['text'][:60]}...")
else:
    print("\n⚠️ No transcripts extracted.")

driver.quit()
print("\n🏁 Script completed!")