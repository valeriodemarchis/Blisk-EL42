import os 
from typing import List
from settings import *
from BEL42_UTILS.error_utils import (
    check_parameter_value_error_if_empty_string,
    isAnOptionOfSandbox,
)

from BEL42_TS.syserrors import (
    getErrorMsg_ValueError_NotOption
)

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



def change_blisk_sandbox_default_area(newArea: str = ""):
    check_parameter_value_error_if_empty_string(
        parameter=newArea, parameterName="newArea", functName="change_blisk_sandbox_default_area",
        ParamT="string"
    )

    if not isAnOptionOfSandbox(
        strinput=newArea, functName="change_blisk_sandbox_default_area",
        param="newArea", param_t="string"
    ):
        ErrorMsg = getErrorMsg_ValueError_NotOption(
            functName="change_blisk_sandbox_default_area",
            parameter="newArea", parameterType="string", 
            options=[docker_sandbox_area, restricted_python_sandbox_area]
        )
        raise ValueError(ErrorMsg)
    
    BLISK_SANDBOX_OPTION_AREA = newArea 
    return 


def get_settings_blisk_execution_code_ability():
    return CODE_EXECUTION_ABILITY

