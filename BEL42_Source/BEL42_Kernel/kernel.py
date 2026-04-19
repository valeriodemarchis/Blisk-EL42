from BEL42_Source.BEL42_Kernel.chatmemory_models import Blisk_EL42_JsonMemoryHistory
from BEL42_Source.BEL42_TS import (
    getErrorMsg_ValueError_Empty,
    TSS_Searcher,
    BEL42_TSSearch,
    getErrorMsg_ValueError_NotOption,
    getErrorMsg_NoneValue
)

from BEL42_Source.BEL42_SFS import analizeModel_OSFS_AndExec
from BEL42_Source.BEL42_UTILS import get_default_reasoning_effort
from BEL42_Source.settings import (
    BLISK_MODE_SEARCH_SUMMARY,
    BLISK_DEFAULT_CAN_MKF,
    SUMMARY_MODEL,
    BLISK_DEFAULT_OUTPUT_FORMAT,
    RESEARCH_ABILITY
)

from BEL42_Source.BEL42_UTILS import tokenize_blisk_output
import torch

default_reasoning_effort = get_default_reasoning_effort()

def  blisk(
            binput: str = "",
            reasoning_effort: str = default_reasoning_effort,
            blisk_mode_search: str = BLISK_MODE_SEARCH_SUMMARY,
            blisk_can_mkf: bool = BLISK_DEFAULT_CAN_MKF,
            summary_modeln: str = SUMMARY_MODEL,
            output_format: str = BLISK_DEFAULT_OUTPUT_FORMAT,
            research_ability: bool = RESEARCH_ABILITY,
            session_id: str = ""
        ) -> str | torch.Tensor:
    
    """
    This is the BLISK-EL42 main function.
    You can use this function for getting answers from Blisk-EL42.

    It takes:

    binput (string) => this is the user input (binput = blisk input)
    ---
    reasoning_effort (string) => the reasoning level of the model, default is medium
    ---
    blisk_mode_search (string) => is the mode that blisk will use if he needs to search, default is summary
    ---
    blisk_can_mkf (bool) => if blisk can make files, currently no
    ---
    summary_modeln (string) => the name of the summary-model
    ---
    output_format (string) => can be 'pt' or 'text', so output as a tensor or as a text
    --- 
    research_ability (bool) => if blisk can search, currently yes
    """

    if not binput:
        errmsg = getErrorMsg_ValueError_Empty(
            functionName="blisk", parameter="binput", parameterType="string"
        )
        raise ValueError(errmsg)
    
    if not session_id:
        errmsg = getErrorMsg_ValueError_Empty(
            functionName="blisk", parameter="session_id", parameterType="string"
        )
        raise ValueError(errmsg)
    
    if output_format != "pt" and output_format != "text":
        errmsg = getErrorMsg_ValueError_NotOption(
            "blisk", "output_format", "string",
            ["pt", "text"]
        )
        raise ValueError(errmsg)
    
    config = {"configurable": {"session_id": session_id}}

    response = Blisk_EL42_JsonMemoryHistory.invoke(
        input=binput, config=config
    ).content 

    if research_ability:
        research_result = BEL42_TSSearch(
            modelmsg=response, reasoning_effort=reasoning_effort, 
            output=blisk_mode_search, summary_modeln=summary_modeln
        )
        if research_result == None:
            if output_format == "text":
                return response 
            
            if output_format == "pt":
                return tokenize_blisk_output(response)
        
        result = f"now answer to the user with this data: {research_result}"
        final = Blisk_EL42_JsonMemoryHistory.invoke(
            input=result, config=config
        ).content 
        if output_format == "text":
            return final 
        if output_format == "pt":
            return tokenize_blisk_output(final)
        
    
    if blisk_can_mkf:
        analizeModel_OSFS_AndExec(modelmsg=response)
        final = Blisk_EL42_JsonMemoryHistory.invoke(
            input="FILE CREATED SUCCESSIFULLY; now continue with the user", config=config
        ).content 
        if output_format == "text":
            return final 
        if output_format == "pt":
            return tokenize_blisk_output(final)


    if output_format == "text":
        return response 

    if output_format == "pt":
        return tokenize_blisk_output(response)
    


    



    



