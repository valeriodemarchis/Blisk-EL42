import os 
from typing import List
from settings import *


def add_gitignore_files(_FilesList: List[str]) -> None:
    _gitignore_file_pos = os.path.join(BASE_DIR, ".gitignore")
    with open(_gitignore_file_pos, "a") as _gitignore:
        for _file in _FilesList:
            _gitignore.write(_file)


def get_jsondir_pos() -> str:
    return JSON_FILES_DIR


def get_default_max_res() -> int:
    return DEFAULT_MAX_RESULTS_NUMBER

def get_default_reasoning_effort() -> str:
    return DEFAULT_REASONING_EFFORT

def get_apikey() -> str:
    return APIKEY 

def get_baseurl() -> str:
    return BASE_URL 

def get_dotenv_filep() -> str:
    return DOTENV_FILE_PATH

def get_default_max_length() -> int:
    return DefaultMaxLength

def get_default_truncation() -> bool:
    return DefaultTruncation


def get_bert_model() -> str:
    return BERT_MODEL


def get_system_prompt() -> str:
    fp = os.path.join(DOCS_DIR, "system_prompt.txt")
    with open(fp, "r") as prompt:
        result = prompt.read()
    return result 


    
