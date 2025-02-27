# Dark Web Intelligence Scanner

![Dark Web Scanner](static/images/dark-web-icon.svg)

A comprehensive dark web search tool designed to identify potential data breaches and leaked personal information.

## Features

- **Multiple Search Types**: Search for emails, domains, phone numbers, and usernames
- **Comprehensive Sources**: Searches across multiple categories of dark web sources
- **Real-time Progress Tracking**: Visual feedback on search progress for each engine
- **Risk Assessment**: Automatic risk scoring of found information
- **Detailed Results**: Complete context for each found mention
- **Secure**: Uses Tor for anonymous searching
- **User-friendly UI**: Modern interface with clear visualization of results
- **JSON Result Logging**: Store search results in structured JSON format for further analysis
- **Automated Scheduling**: Run periodic scans on a schedule to monitor for new breaches

## Search Engine Categories

The Dark Web Intelligence Scanner searches across multiple categories of sources:

- **General search engines**: Common dark web search engines
- **Breach databases**: Known repositories of leaked data
- **Paste sites**: Sites like Pastebin where data is often shared
- **Hacking forums**: Communities where breached data is discussed
- **Dark web marketplaces**: Places where data is bought and sold
- **Ransomware leak sites**: Where stolen corporate data is published
- **Specialized search services**: Focused on specific types of dark web content

## Screenshots

### Home Screen
![Home Screen](static/images/screenshot-home.png)

### Search Progress
![Search Progress](static/images/screenshot-progress.png)

### Results Display
![Results](static/images/screenshot-results.png)

## Installation

1. Ensure you have Python 3.8+ installed
2. Clone this repository
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Install and configure Tor (required for accessing dark web sources)
5. Run the application:
```
python app.py
```

## Automated Scanning

The Dark Web Intelligence Scanner can be configured to run periodic scans automatically.

### Scheduling Options

- **Manual Scheduling**: Run individual scans using the command line
- **Cron-based Scheduling**: Set up system cron jobs for periodic scans
- **Built-in Scheduler**: Use the included scheduler daemon

### Setup Automated Scans

1. Set up the scheduler daemon to run at system startup:
```
python setup_cron.py --setup-scheduler
```

2. Add scheduled scans through the scheduler:
```
python scheduler.py --add --query "example@email.com" --type email --frequency daily --time "03:00"
```

3. Alternatively, add cron jobs directly:
```
python setup_cron.py --add-scan --query "example@email.com" --type email --schedule daily
```

4. Check scheduled scan status:
```
python scheduler.py --status
```

## JSON Result Analysis

All scan results are automatically saved in JSON format for further analysis.

- Result files are stored in the `results` directory
- Each file contains full context of mentions and risk assessments
- Analysis metadata is included with each result
- Results can be imported into other analysis tools

## Security Considerations

- This tool is designed for legitimate security research and personal data monitoring
- Always respect legal and ethical boundaries when using this tool
- The tool may expose you to sensitive or disturbing content
- Use with caution and only for legal purposes

## Technical Implementation

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **Networking**: Tor for anonymous connections
- **Parsing**: BeautifulSoup for content extraction
- **Threading**: Multi-threaded for parallel searching

## Privacy

- No search data is stored on external servers
- Search results are only stored locally
- Personal information is never shared

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided for educational and research purposes only. Users are responsible for ensuring their use of this tool complies with all applicable laws and regulations.

---

*Note: To protect user privacy, all script files (.sh) and database files are excluded from the repository.*
