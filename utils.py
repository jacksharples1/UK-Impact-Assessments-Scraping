import requests
from io import BytesIO
import os
import csv
import logging
import time
from constants import RETRY_AMOUNT

def download_pdf(url):
    for _ in range(RETRY_AMOUNT):
        try:
            response = requests.get(url, timeout=30)  # Increased timeout
            return BytesIO(response.content)
        except ConnectionError as e:
            logging.error(f"Connection error during requests to {url} : {str(e)}")
            time.sleep(2)  # Wait for 2 seconds before trying again
        except Exception as e:
            logging.error(f"Error during requests to {url} : {str(e)}")
            break
    return None

# Function to save PDF to a file
def save_pdf(pdf_stream, filename):
    with open(filename, 'wb') as f:
        f.write(pdf_stream.getbuffer())
        logging.debug(f'Saved PDF to {filename}')

def save_to_csv(list_of_dictionaries, field_names, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(list_of_dictionaries)
    logging.debug(f'Saved data to CSV file {filename}')

def make_directories(output_folder):
    os.makedirs(os.path.join(output_folder, "csv"), exist_ok=True)
    os.makedirs(os.path.join(output_folder, "pdfs"), exist_ok=True)
    logging.debug(f'Created necessary directories')
