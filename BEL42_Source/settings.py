import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APIKEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")

BASE_DIR = Path(__file__).resolve().parent

JSON_FILES_DIR = os.path.join(BASE_DIR, "JSON")
DOTENV_FILE_PATH = os.path.join(BASE_DIR, ".env")
DOCS_DIR = os.path.join(BASE_DIR, "Docs")

BERT_MODEL = os.getenv("BERT_MODEL", "bert-base-uncased")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL")

DEFAULT_MAX_RESULTS_NUMBER = 20
DEFAULT_MIN_SIMPERC_AMOUNT = 65.00
DEFAULT_REASONING_EFFORT = "medium"
DefaultMaxLength = 600
DefaultTruncation = True

BLISK_MODE_SEARCH_SUMMARY = "summary"
BLISK_MODE_SEARCH_DIRECT = "direct"

BLISK_DEFAULT_CAN_MKF = False

BLISK_OUTPUT_FORMAT_TENSOR = "pt"
BLISK_OUTPUT_FORMAT_TEXT = "text"

BLISK_DEFAULT_OUTPUT_FORMAT = BLISK_OUTPUT_FORMAT_TEXT

RESEARCH_ABILITY = True

BLISK_SANDBOX_OPTION_AREA = "RESTRICTED_PYTHON_SANDBOX_AREA"

CODE_EXECUTION_ABILITY = True

DEFAULT_PROHIBITED_MODULES = [
    "os", "shutil", "subprocess", "requests", "ctypes"
]

DEFAULT_TIMEOUT = 5
DEFAULT_MEMORY_LIMIT_MB = 250
