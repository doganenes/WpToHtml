# WpToHtml 

## Overview
WpToHtml extracts WhatsApp messages containing a specific keyword and displays them in an HTML format. The project utilizes web scraping and automation tools to process chat data efficiently.

## Features
- Extracts messages from a WhatsApp chat export.
- Filters messages based on a user-specified keyword.
- Displays messages in a styled HTML page using Bootstrap.
- Uses Flask to serve a simple web interface.
- Uses Selenium for automation (requires `chromedriver.exe`).

## Requirements
- Python 3.x
- Flask
- Tkinter
- Selenium
- BeatifulSoup
- Chrome WebDriver

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/doganenes/WpToHtml.git
   cd WpToHtml
   ```
2. Install dependencies:
   ```bash
   pip install flask selenium
   ```
3. Ensure `chromedriver.exe` is in the project directory.

## Usage
1. Export your WhatsApp chat as a `.html` file.
2. Place the exported chat file in the project directory.
3. Start the Flask web server:
   ```bash
   python scraper.py
   ```
4. Open your browser and go to `http://127.0.0.1:5000/`.
5. Enter keywords in the input field and click "Search messages" to view filtered messages.

## Contribution
Feel free to contribute by submitting pull requests or reporting issues.

## License
This project is licensed under the MIT License.

