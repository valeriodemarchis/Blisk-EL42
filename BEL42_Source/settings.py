import os 
from dotenv import load_dotenv
from pathlib import Path 

from .BEL42_TS import (
    DEFAULT_MAX_RESULTS_NUMBER,
    DEFAULT_MIN_SIMPERC_AMOUNT,
    DEFAULT_REASONING_EFFORT,
    DefaultMaxLength,
    DefaultTruncation
)

from .BEL42_SFS.sfs import (
    docker_sandbox_area, restricted_python_sandbox_area
)

load_dotenv()

APIKEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")

BASE_DIR = Path(__file__).resolve().parent

JSON_FILES_DIR = os.path.join(BASE_DIR, "JSON")
DOTENV_FILE_PATH = os.path.join(BASE_DIR, ".env")
DOCS_DIR = os.path.join(BASE_DIR, "DOCS")


BERT_MODEL = os.getenv("BERT_MODEL")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL")

BLISK_MODE_SEARCH_SUMMARY = "summary"
BLISK_MODE_SEARCH_DIRECT = "direct"

BLISK_DEFAULT_CAN_MKF = False

BLISK_OUTPUT_FORMAT_TENSOR = "pt"
BLISK_OUTPUT_FORMAT_TEXT = "text"

BLISK_DEFAULT_OUTPUT_FORMAT = BLISK_OUTPUT_FORMAT_TEXT

RESEARCH_ABILITY = True 


BLISK_SANDBOX_OPTION_AREA = restricted_python_sandbox_area

CODE_EXECUTION_ABILITY = True 

DEFAULT_PROHIBITED_MODULES = [
    "os", "shutil", "subprocess", "requests", "ctypes"
]

DEFAULT_TIMEOUT = 5
DEFAULT_MEMORY_LIMIT_MB = 250