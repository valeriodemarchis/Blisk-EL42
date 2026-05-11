import importlib 
from typing import List


class SafeImport:
    def __init__(self, prohibited_modules: List[str]):
        self.prohibited_modules = prohibited_modules or [
            "os", "shutil", "subprocess", "requests", "ctypes"
        ]
    
    def __call__(self, module_name, *args, **kwargs):
        if module_name in self.prohibited_modules:
            raise ImportError(f"ERROR: cannot import {module_name} because it's not allowed")
        
        for module in self.prohibited_modules:
            if module_name.startswith(self.prohibited_modules + '.'):
                raise ImportError(f"ERROR: cannot import {module_name} because is not allowed")
            
        return importlib.import_module(module_name)
    

