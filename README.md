# Event Scraper - Trade Show Data Discovery Tool

A comprehensive GUI application for scraping trade show events with contact information and company data. Built with Python, Tkinter, and Selenium, this tool automates the collection of event data from trade show calendars.

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
2. Create a `.env` file in the same directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
3. Run the executable directly

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
4. **Monitor progress** through the real-time log
5. **View results** by clicking "Open Results" when complete

### Settings Configuration

#### OpenAI API Configuration
- **API Key**: Required for company name extraction
- **Auto-load**: Automatically loads from environment variables

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

## 🔧 Development

### Project Structure
```
prospect-data-discovery-project/
├── event_scraper_gui.py      # Main GUI application
├── event_scraper.py          # Core scraping logic
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── env_example.txt          # Environment variables template
├── .gitignore              # Git ignore rules
├── EventScraper.exe        # Pre-built executable
└── venv/                   # Virtual environment (not in repo)
```

### Building the Executable
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name EventScraper event_scraper_gui.py
```

### Key Components

#### GUI Architecture
- **Tkinter-based**: Cross-platform GUI framework
- **Tabbed Interface**: Main and Settings tabs
- **Threading**: Non-blocking scraping operations
- **Event-driven**: Responsive user interface

#### Scraping Engine
- **Selenium WebDriver**: Browser automation
- **BeautifulSoup**: HTML parsing
- **Requests**: HTTP client for website scraping
- **OpenAI API**: Intelligent text processing

#### Data Processing
- **Excel Export**: Structured data output
- **Contact Extraction**: Email and website parsing
- **Company Name Detection**: AI-powered extraction
- **Data Filtering**: US events with date validation

## ⚠️ Important Notes

### API Usage
- **OpenAI API**: Required for company name extraction
- **Rate Limits**: Respect API usage limits
- **Costs**: API calls may incur charges
- **Fallback**: Works without API key (limited functionality)

### Scraping Ethics
- **Respectful Scraping**: Built-in delays to avoid overwhelming servers
- **Terms of Service**: Ensure compliance with target websites
- **Rate Limiting**: Configurable delays between requests
- **Error Handling**: Graceful handling of network issues

### Performance Considerations
- **Memory Usage**: Large datasets may require significant RAM
- **Processing Time**: Scraping can take 30+ minutes for large datasets
- **Network Speed**: Faster internet improves scraping speed
- **Browser Resources**: Chrome WebDriver requires system resources

## 🐛 Troubleshooting

### Common Issues

#### Application Won't Start
- **Check Python version**: Ensure Python 3.8+ is installed
- **Verify dependencies**: Run `pip install -r requirements.txt`
- **Chrome WebDriver**: Ensure Chrome browser is installed
- **Virtual environment**: Activate venv before running

#### Scraping Errors
- **Network issues**: Check internet connection
- **Website changes**: Target site may have updated structure
- **Rate limiting**: Increase wait times in settings
- **API errors**: Verify OpenAI API key is valid

#### Performance Issues
- **Slow scraping**: Increase wait times in settings
- **Memory errors**: Reduce max events limit
- **GUI freezing**: Ensure scraping runs in background thread
- **Browser crashes**: Enable headless mode

### Debug Mode
For development, run with console output:
```bash
python event_scraper_gui.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For issues and questions:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check this README for usage instructions
- **Configuration**: Review settings in the GUI

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with GUI interface
- Individual month/year control
- OpenAI integration for company extraction
- Excel export functionality
- Comprehensive error handling
- Pre-built executable for Windows

## 🎉 Acknowledgments

- **Selenium**: Browser automation framework
- **OpenAI**: GPT-4 API for intelligent text processing
- **Tkinter**: GUI framework
- **PyInstaller**: Executable packaging
- **BeautifulSoup**: HTML parsing library

---

**Note**: This tool is designed for legitimate data collection purposes. Always respect website terms of service and implement appropriate rate limiting when scraping web content.