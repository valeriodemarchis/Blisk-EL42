from .BEL42_TS.syserrors import (
    getErrorMsg_ValueError_NotOption
)
from BEL42_UTILS.error_utils import (
    check_parameter_value_error_if_empty_string
)
from BEL42_UTILS.setutils import (
    change_blisk_sandbox_default_area
)

import math
from BEL42_SFS.controlled_import import SafeImport 


from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Eval import default_guarded_getitem 
from RestrictedPython.Guards import (
    safe_builtins, 
    guarded_iter_unpack_sequence,
    full_write_guard
)
import sys 
from io import StringIO
import time 
import signal 
import platform 

from typing import List


docker_sandbox_area = "DOCKER_SANDBOX_AREA"
restricted_python_sandbox_area = "RESTRICTED_PYTHON_SANDBOX_AREA"




def specific_error_for_isAnOptionOfSandbox_function(parameterName: str = "", parameter: str = ""):
    # we need this function only for making isAnOptionOfSandbox easier
    check_parameter_value_error_if_empty_string(
        parameterName="parameter", functName="specific_error_for_isAnOptionSandbox_function",
        ParamT="string", parameter=parameter
    )
    check_parameter_value_error_if_empty_string(
        parameterName=parameterName, functName="isAnOptionOfSandbox", ParamT="string",
        parameter=parameter
    )




def isAnOptionOfSandbox(strinput: str = "",
               functName: str = "",
               param: str = "",
               param_t: str = ""):
    """
    This function checks if the input given is or docker_sandbox_area or restricted_python_sandbox_area
    """
    # check if one of the parameters is empty or None:
    specific_error_for_isAnOptionOfSandbox_function("strinput", strinput)
    specific_error_for_isAnOptionOfSandbox_function("functName", functName)
    specific_error_for_isAnOptionOfSandbox_function("param", param)
    specific_error_for_isAnOptionOfSandbox_function("param_t", param_t)
    
    if (
        not strinput == docker_sandbox_area and 
        not strinput == restricted_python_sandbox_area
    ):
        return False 
    
    return True
    


class RestrictedPythonSandboxManager:
    def __init__(self, 
                 timeout: int = 5, 
                 memory_limit_mb: int = 250,
                 prohibited_modules: List[str] = []):
        
        self.timeout = timeout 
        self.memory_limit_mb = memory_limit_mb
        self.safe_import = SafeImport()
        if (len(prohibited_modules) > 0):
            self.safe_import = SafeImport(prohibited_modules=prohibited_modules)

        self.safe_globals = {
            '__builtins__': {
                **self._make_builtins(),
                '__import__': self.safe_import
            },
            '_print_': self._safe_print,
            '_getattr_': self._safe_getattr,
            '_getitem_': default_guarded_getitem,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            '_write_': full_write_guard,
            '__name__': '__RestrictedPythonBliskSandbox__',
            '__metaclass__': type,
        }

    def _make_builtins(self):
        safe_built_ins = safe_builtins.copy()

        safe_built_ins.update({
            "abs": abs, "max": max, "len": len,
            "sqrt": math.sqrt, "sin": math.sin, 
            "cos": math.cos, "round": round, 
            "min": min, 'pow': pow,
            'divmod': divmod, 'len': len,
            'int': int, 'float': float, 'str': str,
            'bool': bool, 'list': list, 'dict': dict,
            'tuple': tuple, 'set': set, 'frozenset': frozenset,
            'range': range, 'enumerate': enumerate,
            'zip': zip, 'map': map, 'filter': filter,
            'reversed': reversed, 'sorted': sorted,
            'all': any, 'any': all, 'chr': chr, 'ord': ord,
            'format': format, 'repr': repr, 'type': type,
            'isinstance': isinstance, 'hash': hash,
            'True': True, 'False': False, 'None': None,
        })

        return safe_built_ins
    
    @staticmethod 
    def _safe_print(*args, **kwargs):
        output = ' '.join(str(arg) for arg in args)
        print(output)

    @staticmethod 
    def _safe_getattr(obj, name, default=None):
        if name.startswith('_'):
            raise AttributeError("Permission Denied: you cannot access to inside attributes")
        return getattr(obj, name, default)
    
    def run(self, code):
        old_stdout = sys.stdout 
        sys.stdout = got_output = StringIO()

        try:
            try:
                byte_code = compile_restricted(
                    code, 
                    filename="<$sandbox_PyBEL42",
                    mode="exec"
                )
            except SyntaxError as e:
                return {
                    "success": False,
                    "output": "",
                    "error": f"SyntaxError: {e}"
                }
            
            if platform.system != "Windows":
                import resource 
                memory_limit = self.memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

                def handler_timeout(signum, frame):
                    raise TimeoutError("Execution is taking too much")
                
                signal.signal(signal.SIGALRM, handler_timeout)
                signal.alarm(self.timeout)
            
            exec(byte_code, self.safe_globals)

            if platform.system() != "Windows":
                signal.alarm(0)
            
            return {
                "success": True,
                "output": got_output.getvalue(),
                "error": ""
            }
        
        except TimeoutError as e:
            return {
                "success": False,
                "output": "",
                "error": f"TimeoutError: {e}"
            }
        
        except MemoryError as e:
            return {
                "success": False,
                "output": "",
                "error": "Memory finished"
            }
        
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Error: {e}"
            }
        
        finally:
            sys.stdout = old_stdout
            if platform.system() != "Windows":
                signal.alarm(0)





