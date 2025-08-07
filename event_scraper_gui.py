import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
import sys
import subprocess
import importlib.util

# Global flag to track if scraper modules are available
SCRAPER_AVAILABLE = False
SCRAPER_MODULES = {}

def load_scraper_modules():
    """Lazy load scraper modules when needed"""
    global SCRAPER_AVAILABLE, SCRAPER_MODULES
    
    if SCRAPER_AVAILABLE:
        return SCRAPER_MODULES
    
    try:
        # Import the original scraper functions
        from event_scraper import (
            get_company_name_from_chatgpt,
            extract_company_name_from_website,
            get_company_name_hybrid,
            extract_contact_info,
            extract_website_url,
            click_next_button
        )
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
        from dotenv import load_dotenv
        
        SCRAPER_MODULES = {
            'get_company_name_from_chatgpt': get_company_name_from_chatgpt,
            'extract_company_name_from_website': extract_company_name_from_website,
            'get_company_name_hybrid': get_company_name_hybrid,
            'extract_contact_info': extract_contact_info,
            'extract_website_url': extract_website_url,
            'click_next_button': click_next_button,
            'webdriver': webdriver,
            'Options': Options,
            'By': By,
            'Select': Select,
            'WebDriverWait': WebDriverWait,
            'EC': EC,
            'NoSuchElementException': NoSuchElementException,
            'ElementNotInteractableException': ElementNotInteractableException,
            'TimeoutException': TimeoutException,
            'BeautifulSoup': BeautifulSoup,
            're': re,
            'time': time,
            'openpyxl': openpyxl,
            'requests': requests,
            'urljoin': urljoin,
            'urlparse': urlparse,

            'openai': openai,
            'load_dotenv': load_dotenv
        }
        SCRAPER_AVAILABLE = True
        print("Scraper modules loaded successfully")
        return SCRAPER_MODULES
    except ImportError as e:
        print(f"Warning: Could not import scraper modules: {e}")
        SCRAPER_AVAILABLE = False
        return {}

class EventScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Event Scraper")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create main tab
        self.create_main_tab()
        
        # Create settings tab
        self.create_settings_tab()
        
        # Scraping variables
        self.scraping_thread = None
        self.is_scraping = False
        
    def load_config(self):
        """Load configuration from file or create default"""
        config_file = "scraper_config.json"
        
        # Try to load from .env file first
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Get API key from environment
        api_key_from_env = os.getenv('OPENAI_API_KEY', '')
        
        default_config = {
            "openai_api_key": api_key_from_env,
            "url": "https://thetradeshowcalendar.com/orbus/index.php?",
            "wait_seconds": 7,
            "contact_scrape_delay": 2,
            "max_events": 600,
            "headless_mode": True,
            "months": [
                {"name": "January", "value": "1", "aliases": ["JAN", "JANUARY"]},
                {"name": "February", "value": "2", "aliases": ["FEB", "FEBRUARY"]},
                {"name": "March", "value": "3", "aliases": ["MAR", "MARCH"]},
                {"name": "April", "value": "4", "aliases": ["APR", "APRIL"]},
                {"name": "May", "value": "5", "aliases": ["MAY"]},
                {"name": "June", "value": "6", "aliases": ["JUN", "JUNE"]},
                {"name": "July", "value": "7", "aliases": ["JUL", "JULY"]},
                {"name": "August", "value": "8", "aliases": ["AUG", "AUGUST"]},
                {"name": "September", "value": "9", "aliases": ["SEP", "SEPT", "SEPTEMBER"]},
                {"name": "October", "value": "10", "aliases": ["OCT", "OCTOBER"]},
                {"name": "November", "value": "11", "aliases": ["NOV", "NOVEMBER"]},
                {"name": "December", "value": "12", "aliases": ["DEC", "DECEMBER"]}
            ],
            "year": "2025"
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                    # Merge with defaults, but prioritize saved config
                    default_config.update(saved_config)
                    # If no API key in saved config but we have one from env, use env
                    if not saved_config.get('openai_api_key') and api_key_from_env:
                        default_config['openai_api_key'] = api_key_from_env
                    return default_config
            else:
                return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config
    
    def save_config(self):
        """Save configuration to file"""
        config_file = "scraper_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def create_main_tab(self):
        """Create the main tab with start button and progress"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        # Title
        title_label = ttk.Label(main_frame, text="Event Scraper", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_button = ttk.Button(status_frame, text="Scrape", command=self.toggle_scraping)
        self.status_button.pack()
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill='x', padx=20, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack()
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create text widget with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(log_container, height=10, wrap='word')
        scrollbar = ttk.Scrollbar(log_container, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.open_results_button = ttk.Button(button_frame, text="Open Results", command=self.open_results)
        self.open_results_button.pack(side='left', padx=5)
        
        self.exit_button = ttk.Button(button_frame, text="Exit Application", command=self.exit_application)
        self.exit_button.pack(side='right', padx=5)
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Create scrollable canvas for settings
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # API Key section
        api_frame = ttk.LabelFrame(scrollable_frame, text="OpenAI API Configuration", padding=10)
        api_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(api_frame, text="OpenAI API Key:").pack(anchor='w')
        self.api_key_var = tk.StringVar(value=self.config.get('openai_api_key', ''))
        api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show='*', width=50)
        api_key_entry.pack(fill='x', pady=2)
        
        ttk.Label(api_frame, text="API Key", 
                 font=("Arial", 8)).pack(anchor='w')
        
        # Scraping Configuration
        scraping_frame = ttk.LabelFrame(scrollable_frame, text="Scraping Configuration", padding=10)
        scraping_frame.pack(fill='x', padx=10, pady=5)
        
        # URL
        ttk.Label(scraping_frame, text="Target URL:").pack(anchor='w')
        self.url_var = tk.StringVar(value=self.config.get('url', 'https://thetradeshowcalendar.com/orbus/index.php?'))
        url_entry = ttk.Entry(scraping_frame, textvariable=self.url_var, width=50)
        url_entry.pack(fill='x', pady=2)
        
        # Wait seconds
        ttk.Label(scraping_frame, text="Wait seconds (increase if internet is slow):").pack(anchor='w')
        self.wait_seconds_var = tk.IntVar(value=self.config.get('wait_seconds', 7))
        wait_seconds_spin = ttk.Spinbox(scraping_frame, from_=1, to=30, textvariable=self.wait_seconds_var, width=10)
        wait_seconds_spin.pack(anchor='w', pady=2)
        
        # Contact scrape delay
        ttk.Label(scraping_frame, text="Contact scrape delay (seconds):").pack(anchor='w')
        self.contact_delay_var = tk.IntVar(value=self.config.get('contact_scrape_delay', 2))
        contact_delay_spin = ttk.Spinbox(scraping_frame, from_=1, to=10, textvariable=self.contact_delay_var, width=10)
        contact_delay_spin.pack(anchor='w', pady=2)
        
        # Max events
        ttk.Label(scraping_frame, text="Maximum events to scrape:").pack(anchor='w')
        self.max_events_var = tk.IntVar(value=self.config.get('max_events', 600))
        max_events_spin = ttk.Spinbox(scraping_frame, from_=1, to=1000, textvariable=self.max_events_var, width=10)
        max_events_spin.pack(anchor='w', pady=2)
        
        # Headless mode
        self.headless_var = tk.BooleanVar(value=self.config.get('headless_mode', True))
        headless_check = ttk.Checkbutton(scraping_frame, text="Run browser in headless mode", variable=self.headless_var)
        headless_check.pack(anchor='w', pady=2)
        
        # Default year (for backward compatibility)
        ttk.Label(scraping_frame, text="Default year:").pack(anchor='w')
        self.year_var = tk.StringVar(value=self.config.get('year', '2025'))
        year_entry = ttk.Entry(scraping_frame, textvariable=self.year_var, width=10)
        year_entry.pack(anchor='w', pady=2)
        

        
        # Months selection
        months_frame = ttk.LabelFrame(scrollable_frame, text="Months to Scrape", padding=10)
        months_frame.pack(fill='x', padx=10, pady=5)
        
        self.month_vars = {}
        self.month_year_vars = {}
        months_data = self.config.get('months', [])
        
        # Calculate default years for display
        for month_data in months_data:
            month_name = month_data['name']
            month_num = int(month_data['value'])
            
            # Fixed default years: 2025 for August-December, 2026 for January-July
            if month_num >= 8:  # August-December (months 8-12)
                default_year = 2025
            else:  # January-July (months 1-7)
                default_year = 2026
            
            # Create frame for each month row
            month_row = ttk.Frame(months_frame)
            month_row.pack(fill='x', pady=2)
            
            # Month checkbox
            self.month_vars[month_name] = tk.BooleanVar(value=True)
            month_check = ttk.Checkbutton(month_row, text=month_name, variable=self.month_vars[month_name])
            month_check.pack(side='left')
            
            # Year label
            ttk.Label(month_row, text="Year:").pack(side='left', padx=(10, 5))
            
            # Year entry
            self.month_year_vars[month_name] = tk.StringVar(value=str(default_year))
            year_entry = ttk.Entry(month_row, textvariable=self.month_year_vars[month_name], width=6)
            year_entry.pack(side='left')
        
        # Save button
        save_button = ttk.Button(scrollable_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update GUI in main thread
        self.root.after(0, self._update_log, log_entry)
    
    def _update_log(self, message):
        """Update log text widget (called from main thread)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, value, text=None):
        """Update progress bar and label"""
        self.root.after(0, self._update_progress, value, text)
    
    def _update_progress(self, value, text):
        """Update progress (called from main thread)"""
        self.progress_var.set(value)
        if text:
            self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    def update_status(self, status):
        """Update status label"""
        self.root.after(0, self._update_status, status)
    
    def _update_status(self, status):
        """Update status (called from main thread)"""
        if not self.is_scraping:
            self.status_button.config(text="Scrape")
        else:
            self.status_button.config(text=status)
        self.root.update_idletasks()
    
    def refresh_month_display(self, *args):
        """Refresh month display when year changes"""
        try:
            # Recreate the months frame with updated years
            for widget in self.notebook.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Canvas):
                            # Find the scrollable frame
                            for canvas_child in child.winfo_children():
                                if isinstance(canvas_child, ttk.Frame):
                                    # Find the months frame and update it
                                    for frame_child in canvas_child.winfo_children():
                                        if isinstance(frame_child, ttk.LabelFrame) and "Months to Scrape" in frame_child.cget("text"):
                                            # Clear existing month rows
                                            for row in frame_child.winfo_children():
                                                row.destroy()
                                            
                                            # Recreate with new years
                                            months_data = self.config.get('months', [])
                                            
                                            for month_data in months_data:
                                                month_name = month_data['name']
                                                month_num = int(month_data['value'])
                                                
                                                # Fixed default years: 2025 for August-December, 2026 for January-July
                                                if month_num >= 8:  # August-December (months 8-12)
                                                    default_year = 2025
                                                else:  # January-July (months 1-7)
                                                    default_year = 2026
                                                
                                                # Create frame for each month row
                                                month_row = ttk.Frame(frame_child)
                                                month_row.pack(fill='x', pady=2)
                                                
                                                # Month checkbox
                                                month_check = ttk.Checkbutton(month_row, text=month_name, variable=self.month_vars[month_name])
                                                month_check.pack(side='left')
                                                
                                                # Year label
                                                ttk.Label(month_row, text="Year:").pack(side='left', padx=(10, 5))
                                                
                                                # Year entry
                                                self.month_year_vars[month_name].set(str(default_year))
                                                year_entry = ttk.Entry(month_row, textvariable=self.month_year_vars[month_name], width=6)
                                                year_entry.pack(side='left')
                                            return
        except Exception as e:
            print(f"Error refreshing month display: {e}")
    
    def yield_to_gui(self):
        """Allow GUI to process events"""
        self.root.update()
    
    def save_settings(self):
        """Save current settings to config"""
        self.config['openai_api_key'] = self.api_key_var.get()
        self.config['url'] = self.url_var.get()
        self.config['wait_seconds'] = self.wait_seconds_var.get()
        self.config['contact_scrape_delay'] = self.contact_delay_var.get()
        self.config['max_events'] = self.max_events_var.get()
        self.config['headless_mode'] = self.headless_var.get()
        self.config['year'] = self.year_var.get()
        
        # Save selected months with their individual years
        selected_months = []
        for month_name, var in self.month_vars.items():
            if var.get():
                # Find the month data from config
                for month_data in self.config.get('months', []):
                    if month_data['name'] == month_name:
                        # Add the individual year to the month data
                        month_data['year'] = self.month_year_vars[month_name].get()
                        selected_months.append(month_data)
                        break
        
        self.config['selected_months'] = selected_months
        
        self.save_config()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def toggle_scraping(self):
        """Toggle between start and stop scraping"""
        if self.is_scraping:
            # Stop scraping
            self.stop_scraping()
        else:
            # Start scraping
            self.start_scraping()
    
    def start_scraping(self):
        """Start the scraping process in a separate thread"""
        # Load scraper modules first
        global SCRAPER_MODULES
        SCRAPER_MODULES = load_scraper_modules()
        
        if not SCRAPER_AVAILABLE:
            messagebox.showerror("Error", "Required modules not available. Please install requirements.")
            return
        
        if self.is_scraping:
            return
        
        # Validate settings
        if not self.api_key_var.get().strip():
            messagebox.showwarning("Warning", "OpenAI API key is not set. Company name extraction will be limited.")
        
        # Start scraping thread
        self.is_scraping = True
        self.status_button.config(text="Stop Scraping")
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.log_text.delete(1.0, tk.END)
        
        self.scraping_thread = threading.Thread(target=self.run_scraper)
        self.scraping_thread.daemon = True
        self.scraping_thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_scraping = False
        self.status_button.config(text="Stopping...")
        self.log_message("Stopping scraper...")
    
    def open_results(self):
        """Open the results file"""
        if os.path.exists("events.xlsx"):
            try:
                os.startfile("events.xlsx")
            except:
                messagebox.showinfo("Results", "Results file: events.xlsx")
        else:
            messagebox.showinfo("Results", "No results file found yet.")
    
    def exit_application(self):
        """Exit the application"""
        if self.is_scraping:
            result = messagebox.askyesno("Exit", "Scraping is in progress. Are you sure you want to exit?")
            if not result:
                return
        
        self.root.quit()
    
    def run_scraper(self):
        """Run the actual scraping process"""
        try:
            self.update_status("Initializing scraper...")
            
            # Set up environment
            os.environ['OPENAI_API_KEY'] = self.api_key_var.get()
            
            # Initialize variables
            global event_counter, chatgpt_token_count
            event_counter = 0
            chatgpt_token_count = 0
            
            # Set up Chrome options
            options = SCRAPER_MODULES['Options']()
            if self.headless_var.get():
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Initialize driver
            driver = SCRAPER_MODULES['webdriver'].Chrome(options=options)
            driver.get(self.url_var.get())
            wait = SCRAPER_MODULES['WebDriverWait'](driver, 30)
            
            # Disable SSL warnings

            
            # Get selected months
            selected_months = self.config.get('selected_months', self.config.get('months', []))
            if not selected_months:
                selected_months = self.config.get('months', [])
            
            total_months = len(selected_months)
            events = []
            
            # Get current date to determine smart year selection
            from datetime import datetime
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            # Determine target year from settings
            target_year = int(self.year_var.get())
            
            for month_idx, month_data in enumerate(selected_months):
                if not self.is_scraping:
                    break
                
                month_name = month_data['name']
                month_value = month_data['value']
                month_aliases = month_data['aliases']
                
                # Get the year from the individual month year input
                search_year = int(self.month_year_vars[month_name].get())
                
                self.update_status(f"Processing {month_name} {search_year}...")
                self.log_message(f"Processing {month_name} {search_year}...")
                
                # Allow GUI to update
                self.yield_to_gui()
                
                # Reload page for each month
                driver.get(self.url_var.get())
                SCRAPER_MODULES['time'].sleep(self.wait_seconds_var.get())
                
                # Select month
                try:
                    month_select = wait.until(SCRAPER_MODULES['EC'].visibility_of_element_located((SCRAPER_MODULES['By'].NAME, "vMo")))
                    select = SCRAPER_MODULES['Select'](month_select)
                    select.select_by_value(month_value)
                except Exception as e:
                    continue
                
                # Click search
                try:
                    search_button = driver.find_element(SCRAPER_MODULES['By'].CLASS_NAME, "sc-button-submit")
                    search_button.click()
                    SCRAPER_MODULES['time'].sleep(self.wait_seconds_var.get())
                except Exception as e:
                    continue
                
                # Process pages
                page = 1
                month_events_found = 0
                
                while self.is_scraping:
                    # Get rows
                    row_elements = driver.find_elements(SCRAPER_MODULES['By'].CSS_SELECTOR, "tr.row")
                    
                    if not row_elements:
                        self.log_message(f"No more events found for {month_name} {search_year}")
                        break
                    
                    for row_element in row_elements:
                        if not self.is_scraping or event_counter >= self.max_events_var.get():
                            break
                        
                        try:
                            cols = row_element.find_elements(SCRAPER_MODULES['By'].TAG_NAME, "td")
                            if len(cols) < 6:
                                continue
                            
                            name = cols[0].text.strip()
                            dates = cols[1].text.strip()
                            city = cols[2].text.strip()
                            country = cols[3].text.strip()
                            attendance = cols[4].text.strip()
                            exhibitors = cols[5].text.strip()
                            
                            # Filter for US events and smart year selection
                            if (
                                "united states" in country.lower() and
                                any(alias in dates.upper() for alias in month_aliases) and
                                str(search_year) in dates
                            ):
                                if event_counter >= self.max_events_var.get():
                                    break
                                
                                event_counter += 1
                                month_events_found += 1
                                self.log_message(f"Processing: {name}")
                                
                                # Allow GUI to update every few events
                                if event_counter % 5 == 0:
                                    self.root.after(50)
                                
                                # Extract website URL
                                website_url = SCRAPER_MODULES['extract_website_url'](row_element)
                                
                                # Initialize contact info
                                contact_info = {
                                    'website': website_url,
                                    'email': '',
                                    'company_name': ''
                                }
                                
                                # Get company name
                                event_info = f"Event: {name}, Dates: {dates}, City: {city}, Country: {country}, Attendance: {attendance}, Exhibitors: {exhibitors}"
                                company_name, source = SCRAPER_MODULES['get_company_name_hybrid'](name, event_info, website_url)
                                
                                if company_name:
                                    contact_info['company_name'] = company_name
                                
                                # Scrape contact information
                                if website_url:
                                    website_contact_info = SCRAPER_MODULES['extract_contact_info'](website_url, name)
                                    contact_info['website'] = website_contact_info['website']
                                    contact_info['email'] = website_contact_info['email']
                                    SCRAPER_MODULES['time'].sleep(self.contact_delay_var.get())
                                
                                # Add event
                                events.append([
                                    name, dates, city, country, attendance, exhibitors,
                                    contact_info['website'], contact_info['email'], contact_info['company_name'], source
                                ])
                                
                                # Update progress
                                progress = (event_counter / self.max_events_var.get()) * 100
                                self.update_progress(progress, f"{event_counter}/{self.max_events_var.get()} events")
                        
                        except Exception as e:
                            continue
                    
                    if event_counter >= self.max_events_var.get():
                        break
                    
                    # Try next page
                    if SCRAPER_MODULES['click_next_button'](driver):
                        page += 1
                        SCRAPER_MODULES['time'].sleep(self.wait_seconds_var.get())
                    else:
                        break
                
                # Log month completion
                if month_events_found > 0:
                    self.log_message(f"Completed {month_name} {search_year}: Found {month_events_found} events")
                else:
                    self.log_message(f"No events found for {month_name} {search_year}")
                
                # Update progress for months
                month_progress = ((month_idx + 1) / total_months) * 100
                self.update_progress(month_progress, f"Month {month_idx + 1}/{total_months}")
            
            # Save results
            if events and self.is_scraping:
                wb = SCRAPER_MODULES['openpyxl'].Workbook()
                ws = wb.active
                ws.title = "US Events with Contact Info"
                ws.append([
                    "Event Name", "Dates", "City", "Country", "Attendance", "Exhibitors",
                    "Website", "Email", "Company Name", "Company Name Source"
                ])
                for event in events:
                    ws.append(event)
                wb.save("events.xlsx")
                
                self.log_message(f"Scraping completed successfully! Saved {len(events)} events to events.xlsx")
                
                self.update_status("Scraping completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Scraping completed! Saved {len(events)} events to events.xlsx"))
            elif not self.is_scraping:
                self.log_message("Scraping was stopped by user.")
                self.update_status("Scraping stopped by user.")
            else:
                self.log_message("No events found matching the criteria.")
                self.update_status("No events found.")
            
            # Clean up
            driver.quit()
            
        except Exception as e:
            self.log_message(f"Error during scraping: {e}")
            self.update_status("Error occurred during scraping")
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred during scraping: {e}"))
        
        finally:
            # Reset UI
            self.is_scraping = False
            self.root.after(0, self._reset_ui)
    
    def _reset_ui(self):
        """Reset UI elements after scraping"""
        self.status_button.config(text="Scrape")
        self.progress_var.set(0)
        self.progress_label.config(text="0%")

def main():
    """Main function to run the GUI"""
    print("Starting EventScraper GUI...")
    print("Initializing tkinter...")
    
    try:
        root = tk.Tk()
        print("Tkinter root created successfully")
    except Exception as e:
        print(f"Error creating tkinter root: {e}")
        return
    
    try:
        app = EventScraperGUI(root)
        print("EventScraperGUI initialized successfully")
    except Exception as e:
        print(f"Error initializing EventScraperGUI: {e}")
        return
    
    # Set icon if available
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # Ensure window is visible and focused
    print("Setting window properties...")
    root.lift()  # Bring window to front
    root.attributes('-topmost', True)  # Make it topmost temporarily
    root.after_idle(root.attributes, '-topmost', False)  # Remove topmost after showing
    root.focus_force()  # Force focus
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    print("GUI starting... Window should be visible now.")
    print("Starting mainloop...")
    
    root.mainloop()

if __name__ == "__main__":
    main()
