from BEL42_SFS.sfs import (
    RestrictedPythonSandboxManager
)
from BEL42_SFS.utils import (
    handle_restricted_python_result
)
from BEL42_UTILS.error_utils import check_parameter_value_error_if_empty_string
from BEL42_TS.syserrors import getErrorMsg_ValueError_Empty

from typing import List
from settings import (
    DEFAULT_PROHIBITED_MODULES,
    DEFAULT_MEMORY_LIMIT_MB,
    DEFAULT_TIMEOUT
)
import re 

exec_code_str = r"exec-code\{(.*?)\}"

def defualt_params_code_execution(code_to_exec: str) -> str:
    """
    This is a simple function that uses the class 'RestrictedPythonSandboxManager' to execute code 
    with default parameters
    """
    # let's create the object
    sandbox_manager = RestrictedPythonSandboxManager()

    # getting the outcome of the code
    outcome = sandbox_manager.run(code=code_to_exec)

    # we return a dictionary of the result
    return handle_restricted_python_result(outcome=outcome)


def customed_params_code_execution(code_to_exec: str = "",
                                   prohibited_modules: List[str] = [],
                                   timeout: int = 5,
                                   memory_limit_mb: int = 250) -> str:
    """
    This function execute code with more params, like:
    prohibited_modules, timeout, memory_limit_mb

    So prohibited_modules are the modules that the model will not be allowed to import.
    timeout is the max time we can wait for the output.
    memory_limit_mb is the memory limit of the code execution in megabites.
    """

    check_parameter_value_error_if_empty_string(
        parameter=code_to_exec, parameterName="code_to_exec",
        functName="customed_params_code_execution", ParamT="string"
    )

    if not len(prohibited_modules) > 0:
        ErrorMessage = getErrorMsg_ValueError_Empty(
            functionName="customed_params_code_execution",
            parameter="prohibited_modules", parameterType="string"
        )
        raise ValueError(ErrorMessage)
    
    sandbox_manager = RestrictedPythonSandboxManager(
        timeout=timeout, memory_limit_mb=memory_limit_mb, prohibited_modules=prohibited_modules,
    )

    outcome = sandbox_manager.run()
    result = handle_restricted_python_result(outcome=outcome)
    
    return result 
    

def code_execution(binput: str = "",
                    prohibited_modules: List[str] = DEFAULT_PROHIBITED_MODULES,
                    timeout: int = DEFAULT_TIMEOUT,
                    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB):
    """
    This function searchs in the Blisk's output there is a reference for code:

    exec-code{
    // here he puts the code
    }

    If there is, this function executes it.
    Otherwise, just returns nothing.
    """
    
    result = re.search(exec_code_str, binput)
    if result:
        code = result.group()
        customed_params_code_execution(
            code, prohibited_modules, timeout, memory_limit_mb
        )

    return 

