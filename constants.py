BASE_URL = "https://www.legislation.gov.uk"
IMPACT_ASSESSMENT_ROUTE = "/ukia?stage=Final"
OUTPUT_FOLDER = "output"
FIELD_NAMES = [
    "article name",
    "reference",
    "text",
    "method",
    "origin",
    "page number",
]
REQUEST_DELAY = 0.5
WORD_COUNT_THRESHOLD = 2
STARTING_PAGE = 1
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
RETRY_AMOUNT = 4
