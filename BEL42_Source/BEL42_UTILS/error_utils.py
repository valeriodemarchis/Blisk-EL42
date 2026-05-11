from .BEL42_TS.syserrors import *
from .BEL42_SFS.sfs import (
    isAnOptionOfSandbox,
    docker_sandbox_area,
    restricted_python_sandbox_area
)

def check_parameter_value_error_if_empty_string(parameter: str = "", 
                                         parameterName: str = "",
                                         functName: str = "",
                                         ParamT: str = ""):
    
    """
    This function directly control if the parameter is empty, and if it is throws ValueError.
    """
    # checking if the parameter is empty or None:
    
    if (parameter == "") or (parameter.replace(" ", "") == "") or (parameter is None):
        ErrorMsg: str = getErrorMsg_ValueError_Empty(
            functionName=functName, parameter=parameterName, parameterType=ParamT
        )
        raise ValueError(ErrorMsg) # if it is, raise value error
    
    return # if it is not, just return
    