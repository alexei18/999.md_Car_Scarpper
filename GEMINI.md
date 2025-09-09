# Project Overview

This project contains two main Python scripts for web scraping and automation:

1.  **`hybrid_scraper.py`**: A web scraper for extracting car ad data from the Moldovan classifieds website `999.md`.
2.  **`text.py`**: A Selenium-based automation script for creating videos on the `heygen.com` platform.

The project uses a hybrid approach for scraping `999.md`, combining direct GraphQL API calls for fetching ad listings and a browser automation library (`Playwright`) for extracting data that is not available through the API (specifically, phone numbers).

## Key Files

*   `hybrid_scraper.py`: The main script for scraping car ads from `999.md`.
*   `categorii.txt`: A reference file containing a comprehensive list of filter IDs for `999.md`, used to configure the scraper.
*   `date_masini_999_complet.json`: The output file where the scraped car ad data is stored in JSON format.
*   `text.py`: A Selenium script for automating video creation on `heygen.com`.

## Building and Running

### Prerequisites

This project requires Python and the following libraries:

*   `httpx`
*   `playwright`
*   `selenium`

You can install them using pip:

```bash
pip install httpx playwright selenium
```

You also need to install the Playwright browser binaries:

```bash
playwright install
```

### Running the Scraper

To run the `999.md` scraper, execute the `hybrid_scraper.py` script:

```bash
python hybrid_scraper.py
```

Before running, you may need to manually configure the `SEARCH_PAYLOAD` variable in the script with the desired filter IDs. You can find a complete list of available filter IDs in `categorii.txt`.

### Running the Video Creation Bot

To run the HeyGen video creation bot, execute the `text.py` script:

```bash
python text.py
```

You need to configure the `USER_EMAIL` and `USER_PASSWORD` variables in the script with your HeyGen account credentials.

## Development Conventions

*   The scraper is designed to be incremental. It loads existing data from `date_masini_999_complet.json` and only scrapes new ads that are not already in the file.
*   The scraper has a `IS_TEST_MODE` flag that can be set to `True` to process only a limited number of ads for testing purposes.
*   The `text.py` script uses `logging` to provide detailed information about the automation process. It also includes error handling and takes a screenshot if an error occurs.
