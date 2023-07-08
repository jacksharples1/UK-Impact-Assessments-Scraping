import time
import requests
from bs4 import BeautifulSoup
import os
from utils import download_pdf, save_pdf
import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from pdf2image import convert_from_bytes
import pytesseract
import logging
from tqdm import tqdm
from constants import BASE_URL, OUTPUT_FOLDER, WORD_COUNT_THRESHOLD, REQUEST_DELAY, RETRY_AMOUNT

def legislation_links(tag, href_pattern):
        if tag.name == "a" and "href" in tag.attrs:
            return (
                href_pattern.match(tag["href"])
                and "/cy/ukia?stage=Final&amp" not in tag["href"]
                and not tag["href"].endswith("Final")
            )
        return False


# Function to process a page of articles
def process_page(articles, origin, page_number):
    page_info = []

    # Links get repeated, so skip every other link
    for article in tqdm(articles[::2]):
        article_url = BASE_URL + article["href"]
        article_name = article.get_text()
        logging.debug(f"Processing article: {article_name}")
        text, method, reference = process_article_page(
            article_url, article_name, page_number
        )
        article_info = {
            "article name": article_name,
            "reference": reference,
            "text": text,
            "method": method,
            "origin": origin,
            "page number": page_number,
        }

        page_info.append(article_info)
        time.sleep(REQUEST_DELAY)

    return page_info

# Function to process an article page: download the PDF, convert it to text, and save it to a file
def process_article_page(url, article_name, page_number):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the PDF links on the page
    trys_left = RETRY_AMOUNT

    while trys_left:
        time.sleep(0.1)
        pdf_links = soup.select("a.pdfLink[href$='.pdf']")
        if pdf_links:
            pdf_url = BASE_URL + pdf_links[0]["href"]
            reference = pdf_links[0]["href"].split("/")[-1]
            pdf_filename = os.path.join(OUTPUT_FOLDER, "pdfs", reference)

            logging.debug(f"Downloading: {pdf_url}")
            pdf_stream = download_pdf(pdf_url)

            # Save the PDF file
            logging.debug(f"Saving PDF as: {pdf_filename}")
            save_pdf(pdf_stream, pdf_filename)

            logging.debug(f"Extracting text from: {article_name}")

            try:
                text, method = extract_text_from_pdf(pdf_stream)
                return text, method, reference
            except PDFSyntaxError:
                logging.error(
                    f"Error in pdf_to_text on page {page_number} on article {article_name}"
                )
                text = None
                method = "PDFSyntaxError"
                return text, method, reference
        trys_left -= 1
    else:
        logging.error(f"Missing pdf link in page, response: {response}")
        text = None
        method = "Missing pdf link in page"
        reference = None
        return text, method, reference

def extract_text_from_pdf(pdf_stream):
    method = "pdfplumber"
    main_text = pdfplumber_on_pdf(pdf_stream)
    word_count = len(main_text.split())

    if word_count < WORD_COUNT_THRESHOLD:
        logging.info(f"Word cound using pdfplumber: {word_count}")
        method = "OCR"
        main_text = ocr_on_pdf(pdf_stream)
        word_count = len(main_text.split())
        logging.info(f"Word cound using OCR: {word_count}")

    if word_count < WORD_COUNT_THRESHOLD:
        method = "Possible error or blank page"
        logging.error(f"Possible error on pdfplumber and OCR or blank page")

    return main_text, method

def pdfplumber_on_pdf(pdf_stream):
    text = ""
    with pdfplumber.open(pdf_stream) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text is not None:
                text += page_text

    return text


def ocr_on_pdf(pdf_stream):
    text = ''
    pdf_stream.seek(0)  # Reset the stream position to the beginning
    images = convert_from_bytes(pdf_stream.read())
    for image in images:
        ocr_text = pytesseract.image_to_string(image, lang="eng")
        text += ocr_text
    return text
