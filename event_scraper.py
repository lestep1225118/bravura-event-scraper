from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from bs4 import BeautifulSoup
import re
import time
import openpyxl
import requests
from urllib.parse import urljoin, urlparse

import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global variables
global event_counter


# --- CONFIGURATION ---
URL = "https://thetradeshowcalendar.com/orbus/index.php?"
WAIT_SECONDS = 7  # Increase if your internet is slow or the table loads slowly
CONTACT_SCRAPE_DELAY = 2  # Delay between website visits to be respectful

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not found! Company name extraction will be limited to website scraping only.")

# Token counter for ChatGPT usage
chatgpt_token_count = 0

# Event counter for processing limited events
event_counter = 0
MAX_EVENTS = 600  # Limit to 20 events



def get_company_name_from_chatgpt(event_name, event_info, api_key=None):
    """
    Use ChatGPT to extract the company/organizer name from event information.
    """
    # Use provided API key or fall back to environment variable
    if api_key:
        api_key_to_use = api_key
    else:
        api_key_to_use = OPENAI_API_KEY
    
    if not api_key_to_use:
        print(f"    ERROR: OpenAI API key not set. Skipping ChatGPT extraction.")
        return ""
    
    try:
        prompt = f"""Extract the company or organizer name from this trade show event.

Event Information: {event_info}

Examples:
- "American Academy of Family Physicians - AAFP FUTURE" → "American Academy of Family Physicians"
- "The Foodservice Conference - International Fresh Produce Association" → "International Fresh Produce Association"
- "Black Hat USA" → "Black Hat"
- "Louisiana Restaurant Association - LRA Showcase" → "Louisiana Restaurant Association"
- "RE+ Storage" → "RE+"
- "Abilities Expo - Houston" → "Abilities Expo"
- "The Foodservice Conference" → "International Fresh Produce Association" (from context)

Look for:
1. The main organizing company/association before any dash or hyphen
2. The company name that appears before "Conference", "Expo", "Show", "Event"
3. The primary organization hosting the event

Please provide ONLY the company/organizer name, nothing else. If you can't determine it, respond with 'Unknown'."""
        
        client = openai.OpenAI(api_key=api_key_to_use)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts company names from trade show event information. Look for the main organizing company or association. Be more aggressive in extracting company names - many event names contain the company name. Respond with only the company name or 'Unknown' if you can't determine it."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        company_name = response.choices[0].message.content.strip()
        
        # Track token usage
        global chatgpt_token_count
        if hasattr(response, 'usage') and response.usage:
            tokens_used = response.usage.total_tokens
            chatgpt_token_count += tokens_used
        
        # Clean up the response - only filter out actual "unknown" responses
        if company_name.lower() in ['unknown', 'none', 'n/a', 'not found', 'cannot determine', 'no company found', '']:
            return ""
        
        return company_name
        
    except Exception as e:
        print(f"Error getting company name from ChatGPT: {e}")
        return ""

def extract_company_name_from_website(website_url, event_name):
    """
    Extract company name by scraping the event website with improved accuracy.
    """
    if not website_url:
        return ""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(website_url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Look for company name in specific, high-priority locations
        company_name = ""
        extraction_methods = []
        
        # 1. Check for specific "About" or "Contact" sections first
        about_sections = soup.find_all(['div', 'section'], class_=re.compile(r'about|contact|company|organization', re.IGNORECASE))
        about_result = "Not found"
        for section in about_sections:
            section_text = section.get_text().lower()
            # Look for very specific patterns in about sections
            specific_patterns = [
                r'organized by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'hosted by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'sponsored by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'presented by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'produced by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'managed by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'we are\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'our company\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                r'our organization\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)'
            ]
            for pattern in specific_patterns:
                match = re.search(pattern, section_text)
                if match:
                    potential_name = match.group(1).strip()
                    if len(potential_name) > 3 and not any(word in potential_name.lower() for word in ['conference', 'expo', 'show', 'event', 'the', 'and', 'or']):
                        company_name = potential_name.title()
                        about_result = f"Found: {company_name}"
                        break
            if company_name:
                break
        extraction_methods.append(f"1. About/Contact sections: {about_result}")
        
        # 2. Check footer for company info (often most reliable)
        footer_result = "Not found"
        if not company_name:
            footer = soup.find(['footer', 'div'], class_=re.compile(r'footer|bottom', re.IGNORECASE))
            if footer:
                footer_text = footer.get_text()
                # Look for copyright or company info in footer
                copyright_patterns = [
                    r'©\s*\d{4}\s*([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                    r'copyright\s*\d{4}\s*([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                    r'all rights reserved\s*([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                    r'powered by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|\.|,|$)'
                ]
                for pattern in copyright_patterns:
                    match = re.search(pattern, footer_text, re.IGNORECASE)
                    if match:
                        potential_name = match.group(1).strip()
                        if len(potential_name) > 3:
                            company_name = potential_name.title()
                            footer_result = f"Found: {company_name}"
                            break
        extraction_methods.append(f"2. Footer copyright: {footer_result}")
        
        # 3. Check meta tags for organization info
        og_result = "Not found"
        org_result = "Not found"
        author_result = "Not found"
        desc_result = "Not found"
        
        if not company_name:
            # Check Open Graph site name (often contains company name)
            og_site_name = soup.find('meta', attrs={'property': 'og:site_name'})
            if og_site_name:
                company_name = og_site_name.get('content', '').strip().title()
                og_result = f"Found: {company_name}"
            
            if not company_name:
                meta_org = soup.find('meta', attrs={'name': 'organization'})
                if meta_org:
                    company_name = meta_org.get('content', '').strip().title()
                    org_result = f"Found: {company_name}"
            
            if not company_name:
                meta_author = soup.find('meta', attrs={'name': 'author'})
                if meta_author:
                    author_content = meta_author.get('content', '')
                    if '@' not in author_content:  # Not an email
                        company_name = author_content.strip().title()
                        author_result = f"Found: {company_name}"
            
            if not company_name:
                # Check meta description for company mentions
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    desc_text = meta_desc.get('content', '').lower()
                    # Look for "organized by" or "hosted by" patterns in description
                    desc_patterns = [
                        r'organized by\s+([a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                        r'hosted by\s+([a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                        r'sponsored by\s+([a-zA-Z\s&]+?)(?:\s|\.|,|$)',
                        r'presented by\s+([a-zA-Z\s&]+?)(?:\s|\.|,|$)'
                    ]
                    for pattern in desc_patterns:
                        match = re.search(pattern, desc_text)
                        if match:
                            potential_name = match.group(1).strip()
                            if len(potential_name) > 3 and not any(word in potential_name.lower() for word in ['conference', 'expo', 'show', 'event']):
                                company_name = potential_name.title()
                                desc_result = f"Found: {company_name}"
                                break
        
        extraction_methods.append(f"3. Open Graph site name: {og_result}")
        extraction_methods.append(f"4. Organization meta tag: {org_result}")
        extraction_methods.append(f"5. Author meta tag: {author_result}")
        extraction_methods.append(f"6. Meta description: {desc_result}")
        
        # 7. Check title tag (but be more selective)
        title_result = "Not found"
        if not company_name:
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Only extract if title looks like it contains company name
                if ' - ' in title_text or ' | ' in title_text:
                    parts = re.split(r'\s*[-|]\s*', title_text)
                    if len(parts) > 1:
                        potential_name = parts[0].strip()
                        if len(potential_name) > 3 and not any(word in potential_name.lower() for word in ['conference', 'expo', 'show', 'event']):
                            company_name = potential_name.title()
                            title_result = f"Found: {company_name}"
        extraction_methods.append(f"7. Title tag: {title_result}")
        
        # 8. Check domain name as last resort (but be more careful)
        domain_result = "Not found"
        if not company_name:
            domain = urlparse(website_url).netloc
            if domain:
                domain_parts = domain.replace('www.', '').split('.')
                if len(domain_parts) > 0:
                    domain_name = domain_parts[0]
                    # Only use domain if it looks like a company name (not generic)
                    if len(domain_name) > 3 and not any(word in domain_name.lower() for word in ['event', 'show', 'expo', 'conference', 'trade', 'fair']):
                        domain_name = domain_name.replace('-', ' ').replace('_', ' ')
                        company_name = domain_name.title()
                        domain_result = f"Found: {company_name}"
        extraction_methods.append(f"8. Domain name: {domain_result}")
        
        # Print all extraction methods for this website
        print(f"  Website extraction methods for {event_name}:")
        for method in extraction_methods:
            print(f"    {method}")
        
        # Clean up the company name
        if company_name:
            # Remove common suffixes
            suffixes = [' Inc', ' LLC', ' Corp', ' Corporation', ' Company', ' Co', ' Ltd', ' Limited']
            for suffix in suffixes:
                if company_name.endswith(suffix):
                    company_name = company_name[:-len(suffix)]
                    break
            
            # Clean up extra spaces and common words
            company_name = ' '.join(company_name.split())
            
            # Remove common prefixes that aren't part of company name
            prefixes_to_remove = ['The ', 'Welcome to ', 'Home - ', 'About - ']
            for prefix in prefixes_to_remove:
                if company_name.startswith(prefix):
                    company_name = company_name[len(prefix):]
                    break
            
            print(f"  Final result: {company_name}")
            return company_name
        
        print(f"  Final result: Not found")
        return ""
        
    except Exception as e:
        print(f"Error extracting company name from website for {event_name}: {e}")
        return ""

def get_company_name_hybrid(event_name, event_info, website_url="", api_key=None):
    """
    Try ChatGPT first, then fall back to website extraction if ChatGPT fails.
    Returns tuple: (company_name, source)
    """
    # Try ChatGPT first (faster and more accurate for event names)
    company_name = get_company_name_from_chatgpt(event_name, event_info, api_key)
    
    if company_name:
        return company_name, "ChatGPT"
    
    # Fall back to website extraction if ChatGPT failed
    if website_url:
        company_name = extract_company_name_from_website(website_url, event_name)
        
        if company_name:
            return company_name, "Website"
    
    return "", "None"

def extract_contact_info(website_url, event_name):
    """
    Extract contact information from an event website.
    Returns a dictionary with contact details.
    """
    contact_info = {
        'website': website_url,
        'email': '',
        'company_name': ''
    }
    
    try:
        # Use requests for faster initial check
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(website_url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for contact information patterns
        page_text = soup.get_text().lower()
        
        # Email patterns
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'info@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'contact@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'events@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'sales@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        
        for pattern in email_patterns:
            emails = re.findall(pattern, page_text)
            if emails:
                contact_info['email'] = emails[0]
                break
        

        
        # If no email found, try to find contact page and scrape from there
        if not contact_info['email']:
            contact_links = soup.find_all('a', href=True)
            contact_keywords = ['contact', 'about', 'info', 'reach', 'connect']
            
            for link in contact_links:
                link_text = link.get_text().lower()
                href = link.get('href', '').lower()
                
                if any(keyword in link_text or keyword in href for keyword in contact_keywords):
                    try:
                        contact_url = urljoin(website_url, link['href'])
                        contact_response = requests.get(contact_url, headers=headers, timeout=10, verify=False)
                        contact_response.raise_for_status()
                        contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                        contact_text = contact_soup.get_text().lower()
                        
                        # Look for emails on contact page
                        for pattern in email_patterns:
                            emails = re.findall(pattern, contact_text)
                            if emails:
                                contact_info['email'] = emails[0]
                                break
                        

                                
                        break  # Found contact page, no need to check more links
                        
                    except Exception as e:
                        print(f"Could not scrape contact page for {event_name}: {e}")
                        continue
        
    except Exception as e:
        print(f"Error scraping contact info for {event_name} ({website_url}): {e}")
    
    return contact_info

def extract_website_url(row_element):
    """
    Extract website URL from a table row element.
    """
    try:
        # Look for links in the event name column
        name_cell = row_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
        links = name_cell.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                return href
        
        # If no direct link, look for any links in the row
        all_links = row_element.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                return href
                
    except Exception as e:
        print(f"Error extracting website URL: {e}")
    
    return ""

def click_next_button(driver):
    try:
        # Find the <td class="next">
        next_td = driver.find_element(By.CSS_SELECTOR, "td.next")
        # Try clicking the <td> directly
        driver.execute_script("arguments[0].scrollIntoView(true);", next_td)
        try:
            next_td.click()
            return True
        except Exception:
            # If that fails, try clicking the <div> with onclick via JS
            clickable_div = next_td.find_element(By.XPATH, ".//div[@onclick]")
            driver.execute_script("arguments[0].click();", clickable_div)
            return True
    except Exception as e:
        print("Could not click next button:", e)
        return False



def main():
    """Main function to run the scraper"""
    global event_counter, chatgpt_token_count
    
    # Reset counters
    event_counter = 0
    chatgpt_token_count = 0
    
    print("Starting event scraper...")
    
    # --- SELENIUM SETUP ---
    options = Options()
    options.add_argument('--headless')  # Run in headless mode (no browser window)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(options=options)  # Or use webdriver.Firefox()
    driver.get(URL)
    wait = WebDriverWait(driver, 30)
    
    # --- Select 'May' in the Month dropdown (name='vMo', value='5') ---
    try:
        month_select = wait.until(EC.visibility_of_element_located((By.NAME, "vMo")))
        select = Select(month_select)
        select.select_by_value("5")
    except Exception as e:
        print("Could not select month:", e)
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        return

    # --- Click the Search button ---
    try:
        # The search button is a <button> with class 'sc-button-submit'
        search_button = driver.find_element(By.CLASS_NAME, "sc-button-submit")
        search_button.click()
        time.sleep(WAIT_SECONDS)
    except Exception as e:
        print("Could not click search button:", e)
        with open("debug_search.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        return

    # --- Scrape all results for specified months in the USA (with pagination if needed) ---
    months = [
        ("July", "7", ["JUL", "JULY"]),
        ("August", "8", ["AUG", "AUGUST"]),
        ("September", "9", ["SEP", "SEPT", "SEPTEMBER"]),
        ("October", "10", ["OCT", "OCTOBER"]),
        ("November", "11", ["NOV", "NOVEMBER"]),
        ("December", "12", ["DEC", "DECEMBER"]),
    ]
    year = "2025"
    events = []
    for month_name, month_value, month_aliases in months:
        print(f"\nProcessing {month_name} {year}...")
        # Reload the page to reset state for each month
        driver.get(URL)
        time.sleep(WAIT_SECONDS)
        # Select the month in the dropdown
        try:
            month_select = wait.until(EC.visibility_of_element_located((By.NAME, "vMo")))
            select = Select(month_select)
            select.select_by_value(month_value)
        except Exception as e:
            print(f"Could not select month {month_name}:", e)
            with open(f"debug_{month_name.lower()}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
            return

        # Click the Search button
        try:
            search_button = driver.find_element(By.CLASS_NAME, "sc-button-submit")
            search_button.click()
            time.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"Could not click search button for {month_name}:", e)
            with open(f"debug_search_{month_name.lower()}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
            return

        page = 1
        while True:
            print(f"Processing {month_name} - Page {page}")
            
            # Get all row elements using Selenium for better link extraction
            row_elements = driver.find_elements(By.CSS_SELECTOR, "tr.row")
            
            for row_element in row_elements:
                try:
                    cols = row_element.find_elements(By.TAG_NAME, "td")
                    if len(cols) < 6:
                        continue
                        
                    name = cols[0].text.strip()
                    dates = cols[1].text.strip()
                    city = cols[2].text.strip()
                    country = cols[3].text.strip()
                    attendance = cols[4].text.strip()
                    exhibitors = cols[5].text.strip()

                    # Filter for US events and the current month/year, allowing for multiple month aliases
                    if (
                        "united states" in country.lower() and
                        any(alias in dates.upper() for alias in month_aliases) and
                        year in dates
                    ):
                        # Check if we've reached the maximum number of events
                        if event_counter >= MAX_EVENTS:
                            print(f"Reached maximum events ({MAX_EVENTS}). Stopping.")
                            break
                        
                        event_counter += 1
                        print(f"Processing event {event_counter}/{MAX_EVENTS}: {name}")
                        
                        # Extract website URL
                        website_url = extract_website_url(row_element)
                        
                        # Initialize contact info
                        contact_info = {
                            'website': website_url,
                            'email': '',
                            'company_name': ''
                        }
                        
                        # Get company name using hybrid approach (ChatGPT first, then website)
                        event_info = f"Event: {name}, Dates: {dates}, City: {city}, Country: {country}, Attendance: {attendance}, Exhibitors: {exhibitors}"
                        company_name, source = get_company_name_hybrid(name, event_info, website_url, OPENAI_API_KEY)
                        
                        if company_name:
                            contact_info['company_name'] = company_name
                        
                        # Scrape contact information if website URL is found
                        if website_url:
                            website_contact_info = extract_contact_info(website_url, name)
                            # Preserve the company name from hybrid extraction, only update website and email
                            contact_info['website'] = website_contact_info['website']
                            contact_info['email'] = website_contact_info['email']
                            time.sleep(CONTACT_SCRAPE_DELAY)  # Be respectful to websites
                        
                        # Add event with contact info and source
                        events.append([
                            name, dates, city, country, attendance, exhibitors,
                            contact_info['website'], contact_info['email'], contact_info['company_name'], source
                        ])
                        
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue

            # Check if we've reached max events and break out of pagination loop
            if event_counter >= MAX_EVENTS:
                break

            # Try to click the Next button for this month, regardless of event presence
            if click_next_button(driver):
                page += 1
                time.sleep(WAIT_SECONDS)
            else:
                break
    
    # --- SAVE TO EXCEL ---
    print(f"Total US events to save: {len(events)}")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "US Events with Contact Info"
    ws.append([
        "Event Name", "Dates", "City", "Country", "Attendance", "Exhibitors",
        "Website", "Email", "Company Name", "Company Name Source"
    ])
    for event in events:
        ws.append(event)
    wb.save("events.xlsx")

    if events:
        print(f"Saved {len(events)} events with contact information to events.xlsx")
    else:
        print("No US events found for the selected months.")

    # Print summary of contact information found
    if events:
        events_with_website = sum(1 for event in events if event[6])  # Website column
        events_with_email = sum(1 for event in events if event[7])    # Email column
        events_with_company = sum(1 for event in events if event[8])  # Company Name column
        
        # Count sources
        chatgpt_sources = sum(1 for event in events if event[9] == "ChatGPT")
        website_sources = sum(1 for event in events if event[9] == "Website")
        none_sources = sum(1 for event in events if event[9] == "None")
        
        print(f"\n--- CONTACT INFORMATION SUMMARY ---")
        print(f"Total events: {len(events)}")
        print(f"Events with website: {events_with_website}")
        print(f"Events with email: {events_with_email}")
        print(f"Events with company name: {events_with_company}")
        print(f"Company names from ChatGPT: {chatgpt_sources}")
        print(f"Company names from Website: {website_sources}")
        print(f"Company names not found: {none_sources}")
        print(f"Contact information found for {events_with_email + events_with_company} events")

    # Clean up
    driver.quit()

    # Print final token usage summary
    if chatgpt_token_count > 0:
        print(f"\n--- CHATGPT USAGE SUMMARY ---")
        print(f"Total tokens used: {chatgpt_token_count}")

    print("\nScraping completed!")

if __name__ == "__main__":
    main() 