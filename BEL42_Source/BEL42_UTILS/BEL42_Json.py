import json 
import os 
from setutils import (
    add_gitignore_files,
    get_jsondir_pos
)

from BEL42_TS import (
    getErrorMsg_FileNoExists,
    getErrorMsg_NoneValue,
    getErrorMsg_ValueError_Empty
)

# this file is for utils about json that we will definitely need in the future


class BEL42_Json:
    def __init__(self, 
                _MainJsonValue: dict | None = {},
                _JsonFileName: str = "",
                _gitignore_presence: bool = True,
                _add_mjv_given: bool = False):
        
        self._MainJsonValue = _MainJsonValue
        self._JsonFileName = _JsonFileName 
        self._gitignore_presence = _gitignore_presence
        self._add_mjv_given = _add_mjv_given
        
        self._jsonDirPos = get_jsondir_pos()
        self._add_json_to_gitignore = add_gitignore_files

        self._this_path = os.path.join(self._jsonDirPos, self._JsonFileName)
        if not os.path.exists(self._this_path):
            errmsg = getErrorMsg_FileNoExists("BEL42_Json.__init__", self._this_path)
            raise FileExistsError(errmsg)
        
        if self._add_mjv_given:
            if self._MainJsonValue == None:
                errmsg = getErrorMsg_NoneValue(
                    functName="BEL42_Json.__init__", parameter="_MainJsonValue", parameter_t="string",
                    _addingMsg="And it cannot be None because you put '_add_mjv_given' in True, so '_MainJsonValue' is expected."
                )
                raise ValueError(errmsg)
            
            with open(self._this_path, "w") as jfile:
                json.dump(self._MainJsonValue, jfile)
        
        with open(self._this_path, "r") as jfile:
            content = json.load(jfile)
        
        self.content = content 

        if self._gitignore_presence:
            self._add_json_to_gitignore([self._this_path])

    def get_value(self, _key: str = ""):
        return self.content.get(_key)
    
    def get_data(self) -> dict:
        return self.content 

    def load_data(self, dt: dict):
        if not dt:
            errmsg = getErrorMsg_ValueError_Empty(
                functionName="BEL42_Json.load_data", parameter="dt", parameterType="dict"
            )
            raise ValueError(errmsg)
        
        with open(self._this_path, "w") as jfile:
            json.dump(dt, jfile)


    def set_value(self, key, _nvalue):
        self.content[key] = _nvalue 
        self.load_data(self.content)










        

