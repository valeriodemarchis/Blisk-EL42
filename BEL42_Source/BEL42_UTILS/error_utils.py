from BEL42_TS.syserrors import *

def check_parameter_value_error_if_empty_string(parameter: str = "", 
                                         parameterName: str = "",
                                         functName: str = "",
                                         ParamT: str = ""):
    
    """
    This function directly control if the parameter is empty, and if it is throws ValueError.
    """
    # checking if the parameter is empty or None:
    
    if parameter is None or parameter == "" or parameter.replace(" ", "") == "":
        ErrorMsg: str = getErrorMsg_ValueError_Empty(
            functionName=functName, parameter=parameterName, parameterType=ParamT
        )
        raise ValueError(ErrorMsg) # if it is, raise value error
    
    return # if it is not, just return
    