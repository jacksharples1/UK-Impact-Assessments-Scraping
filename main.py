import requests
from bs4 import BeautifulSoup
import time
import re
import os
import logging
from process import process_page, legislation_links
from utils import save_to_csv, make_directories
from constants import (
    BASE_URL,
    IMPACT_ASSESSMENT_ROUTE,
    OUTPUT_FOLDER,
    FIELD_NAMES,
    REQUEST_DELAY,
    STARTING_PAGE,
    LOGGING_FORMAT,
    RETRY_AMOUNT
)

logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)


def main(starting_page=STARTING_PAGE):
    # Create the output folders if they don't exist
    make_directories(OUTPUT_FOLDER)

    page = starting_page

    impact_assessments = []

    while True:
        logging.debug(f"Processing page {page}")
        soup = None  # Initialize the variable to None
        current_page_url = f"{BASE_URL+IMPACT_ASSESSMENT_ROUTE}&page={page}"
        for _ in range(RETRY_AMOUNT):  # Try 5 times
            try:
                response = requests.get(
                    current_page_url, timeout=120
                )  # Increased timeout
                soup = BeautifulSoup(response.text, "html.parser")
                break  # If the request was successful, break out of the inner loop
            except ConnectionError as e:
                logging.error(
                    f"Connection error during requests to {current_page_url} : {str(e)}"
                )
                time.sleep(2)  # Wait for 2 seconds before trying again
            except Exception as e:
                logging.error(f"Error during requests to {current_page_url} : {str(e)}")
                time.sleep(2)
                break  # If another type of exception occurred, break out of the inner loop

        if soup is None:
            logging.error(f"Error during requests to {current_page_url} : {str(e)}")
            break

        uk_href_pattern = re.compile(r"^/uk[a-zA-Z]*/")
        nisr_href_pattern = re.compile(r"^/ni[a-zA-Z]*/")

        uk_article_links = soup.find_all(
            lambda tag: legislation_links(tag, uk_href_pattern)
        )
        nisr_article_links = soup.find_all(
            lambda tag: legislation_links(tag, nisr_href_pattern)
        )

        uk_articles = process_page(uk_article_links, "uk", page)
        nisr_articles = process_page(nisr_article_links, "nisr", page)

        impact_assessments.extend(uk_articles)
        impact_assessments.extend(nisr_articles)

        logging.debug(
            f"UK articles: {len(uk_articles)}, NISR articles: {len(nisr_articles)}"
        )

        if len(uk_articles + nisr_articles) != 20:
            logging.warning(
                f"Missing articles on page {page}, check if this is the final page"
            )
            save_to_csv(
                impact_assessments,
                FIELD_NAMES,
                os.path.join(OUTPUT_FOLDER, "csv", "output.csv"),
            )
            break

        logging.info(f"Completed page {page}")
        page += 1
        time.sleep(REQUEST_DELAY)


if __name__ == "__main__":
    main()
