import os 
import re 

from BEL42_TS import getErrorMsg_ValueError_Empty

MKFILE_REGEX = r"""
[% NEW-FILE %]
<file-name: (.*?)>
{ block content }
(.*?)
{ block content }
"""

def analizeModel_OSFS_AndExec(modelmsg: str = ""):
    """
    This function analizes the model output and if the model requires to open a file the 
    function will do that. This is a simple version for local computer.
    """
    res = re.search(MKFILE_REGEX, modelmsg)
    if res:
        fname = res.group(1)
        content = res.group(2)
    
    with open(fname, "w") as sc:
        sc.write(content)

    
