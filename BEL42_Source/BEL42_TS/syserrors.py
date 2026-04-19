# this module is for helping us using errors more comfortable
from typing import List


def getErrorMsg_ValueError_Empty(functionName: str, parameter: str, parameterType: str) -> str:
    return f"""
    There is a problem in function '{functionName}': parameter '{parameter}' ({parameterType}) is empty.
    """

def getErrorMsg_ValueError_NotOption(
            functionName: str, 
            parameter: str,
            parameterType: str,
            options: List[str]
        ) -> str:
    output = f"""
    There is a problem at function '{functionName}': the parameter '{parameter}' ({parameterType})
    Can be ONLY '{options[0]}' or '{options[1]}'. 
    Other values are NOT allowed.
    """
    return output


def getErrorMsg_FileNoExists(
                funct_name: str = "",
                file_p: str = "",
            ) -> str:
    
    if not funct_name:
        errmsg = getErrorMsg_ValueError_Empty("getErrorMsg_FileNoExists", "funct_name", "string")
        raise ValueError(errmsg)
    
    if not file_p:
        errmsg = getErrorMsg_ValueError_Empty("getErrorMsg_FileNoExists", "file_p", "string")
        raise ValueError(errmsg)
    
    output = f"""
    There is a problem at function '{funct_name}': the file '{file_p}' does not exist.
    """
    return output


def getErrorMsg_NoneValue(
                functName: str = "",
                parameter: str = "",
                parameter_t: str = "",
                _addingMsg: str | None = ""
            ):
    
    if not functName:
        errmsg = getErrorMsg_ValueError_Empty("getErrorMsg_NoneValue", "functName", "string")
        raise ValueError(errmsg)

    if not parameter:
        errmsg = getErrorMsg_ValueError_Empty("getErrorMsg_NoneValue", "parameter", "string")
        raise ValueError(errmsg)
    
    if not parameter_t:
        errmsg = getErrorMsg_ValueError_Empty("getErrorMsg_NoneValue", "parameter_t", "string")

    if _addingMsg == None or not _addingMsg:
        output = f"""
        There is a problem at function '{functName}': parameter '{parameter}' ({parameter_t}) has value None.
        """
        return output
    
    output = f"""
    There is a problem at function '{functName}': parameter '{parameter}' ({parameter_t}) has value None.
    {_addingMsg}
    """
    return output
    

    


    