# Event Scraper - Trade Show Data Discovery Tool

A comprehensive GUI application for scraping trade show events with contact information and company data. Built with Python, Tkinter, and Selenium, this tool automates the collection of event data from trade show calendars.

## 📋 Requirements

### System Requirements
- **Windows 10/11** (Primary target)
- **Python 3.8+** (3.12 recommended)
- **Chrome Browser** (for Selenium WebDriver)
- **4GB+ RAM** (for large scraping operations)
- **Internet Connection** (for web scraping and API calls)

### Python Dependencies
```
selenium>=4.0.0
beautifulsoup4>=4.9.0
openpyxl>=3.0.0
requests>=2.25.0
openai>=1.0.0
python-dotenv>=0.19.0
pyinstaller>=5.0.0
```

## 🛠️ Installation

### Option 1: Pre-built Executable (Recommended)
1. Download `EventScraper.exe` from the releases
2. Run the executable directly

### Option 2: From Source
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd prospect-data-discovery-project
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create `.env` file with your OpenAI API key
   - Or set system environment variable `OPENAI_API_KEY`

5. **Run the application**:
   ```bash
   python event_scraper_gui.py
   ```

## 🎯 Usage

### Quick Start
1. **Launch the application** (GUI will appear)
2. **Configure settings** in the Settings tab:
   - Enter your OpenAI API key
   - Adjust scraping parameters if needed
   - Select months and set years (2025/2026)
3. **Start scraping** by clicking "Scrape" in the Main tab
5. **View results** by clicking created excel file

### Settings Configuration

#### Scraping Configuration
- **Target URL**: Trade show calendar website
- **Wait Seconds**: Delay between page loads (7-30 seconds)
- **Contact Delay**: Delay for website scraping (1-10 seconds)
- **Max Events**: Maximum events to collect (1-1000)
- **Headless Mode**: Run browser in background

#### Month Selection
- **Individual Year Control**: Set specific years for each month
- **Smart Defaults**: 
  - August-December: 2025
  - January-July: 2026
- **Selective Scraping**: Choose which months to process

### Output Format

The application generates `events.xlsx` with the following columns:

| Column | Description |
|--------|-------------|
| Event Name | Name of the trade show event |
| Dates | Event dates and duration |
| City | Event location city |
| Country | Event location country |
| Attendance | Expected attendance numbers |
| Exhibitors | Number of exhibitors |
| Website | Event website URL |
| Email | Contact email address |
| Company Name | Extracted company name |
| Company Name Source | Source of company name (GPT/Website) |

### Building the Executable
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name EventScraper event_scraper_gui.py
```

## 🚀 Features

### Core Functionality
- **Web Scraping**: Automated extraction of trade show events from online calendars
- **Contact Information**: Gathers website URLs, email addresses, and company names
- **Smart Filtering**: Focuses on US-based events with intelligent date filtering
- **Excel Export**: Saves results to structured Excel files for easy analysis

### GUI Interface
- **Modern Tkinter GUI**: Clean, intuitive interface with tabbed navigation
- **Real-time Progress**: Live progress tracking with detailed logging
- **Configurable Settings**: Customizable scraping parameters and API keys
- **Individual Month Control**: Set specific years for each month (2025/2026)
- **Stop/Start Control**: Ability to pause and resume scraping operations

### Advanced Features
- **OpenAI Integration**: Uses GPT-4 for intelligent company name extraction
- **Multi-threaded**: Non-blocking GUI with background scraping
- **Error Handling**: Robust error recovery and user-friendly messages
- **Configuration Persistence**: Saves settings between sessions

## ⚠️ Important Notes

### API Usage
- **OpenAI API**: Required for company name extraction
- **Rate Limits**: Respect API usage limits
- **Costs**: API calls may incur charges
- **Fallback**: Works without API key (limited functionality)