# Trade Show Event Contact Information Scraper

Scrapes US trade show events from The Trade Show Calendar and extracts comprehensive contact information including company names, email addresses, and website URLs.

## Information

- Scrapes US trade show events for July-December 2025
- Uses OpenAI GPT-4 for company name extraction, with fallback to website scraping
- Extracts email addresses and website URLs from event websites
- Includes delays between requests to be respectful to servers
- Saves all data to a structured Excel file with contact information

## Setup Instructions

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up OpenAI API Key
- Get an API key from https://platform.openai.com/api-keys
- Create a `.env` file in the project directory with:
  ```
  OPENAI_API_KEY=your-api-key-here
  ```
- Or set it as an environment variable:
  ```bash
  export OPENAI_API_KEY="your-api-key-here"
  ```

### 3. Install ChromeDriver
- Download ChromeDriver from https://sites.google.com/chromium.org/driver/
- Add it to your system PATH or place it in the same directory as the script

### 4. Run the Script
```bash
python event_scraper.py
```

## Output

The script generates an Excel file named `events.xlsx` with the following columns:

- **Event Name**: Name of the trade show event
- **Dates**: Event dates
- **City**: Event location city
- **Country**: Event location country
- **Attendance**: Expected attendance numbers
- **Exhibitors**: Number of exhibitors
- **Website**: Event website URL
- **Email**: Contact email address (if found)
- **Company Name**: Extracted company/organizer name
- **Company Name Source**: Source of company name (ChatGPT, Website, or None)

## Configuration

You can modify these settings in `event_scraper.py`:

- `WAIT_SECONDS`: Time to wait for pages to load (default: 7 seconds)
- `CONTACT_SCRAPE_DELAY`: Delay between website visits (default: 2 seconds)
- `MAX_EVENTS`: Maximum number of events to process (default: 600)
- `months`: List of months to scrape (currently July-December 2025)

## How It Works

1. **Event Discovery**: Scrapes The Trade Show Calendar for US events in specified months
2. **Website Extraction**: Extracts website URLs from event listings
3. **Company Name Extraction**: 
   - First attempts to extract company names using OpenAI GPT-4
   - Falls back to website scraping if GPT-4 fails
   - Uses multiple extraction methods including meta tags, footer information, and content analysis
4. **Contact Information**: Visits each event website to extract email addresses
5. **Data Export**: Saves all information to Excel with source tracking

## Performance Features

- **Headless browser**: Runs Chrome in headless mode for faster execution
- **Intelligent delays**: Respects website servers with configurable delays
- **Error handling**: Gracefully handles website access issues and timeouts
- **Progress tracking**: Shows detailed progress and statistics during execution
- **Token monitoring**: Tracks OpenAI API usage and provides cost estimates

## Troubleshooting

- **SSL errors**: The script automatically disables SSL warnings
- **ChromeDriver issues**: Ensure ChromeDriver is in your PATH or project directory
- **Slow internet**: Increase `WAIT_SECONDS` for slower connections
- **API key issues**: Check that your OpenAI API key is properly set in `.env` file
- **Rate limiting**: The script includes delays to avoid being blocked by websites

## Notes

- The script is configured to scrape July-December 2025 events
- Company name extraction uses advanced AI techniques for better accuracy
- All scraping is done respectfully with appropriate delays
- The script provides detailed console output for monitoring progress
- Token usage displayed at the end of execution

## Dependencies

- `selenium`: Web automation and browser control
- `beautifulsoup4`: HTML parsing and web scraping
- `openpyxl`: Excel file creation and manipulation
- `requests`: HTTP requests for website access
- `openai`: OpenAI API integration for company name extraction
- `python-dotenv`: Environment variable management