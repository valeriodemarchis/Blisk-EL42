try:
    from openai import OpenAI
    from dotenv import load_dotenv
    import os 
except ImportError:
    raise ImportError("One of the following modules (or more than one) is not installed: openai, dotenv")


load_dotenv()

from BEL42_Source.BEL42_TS.syserrors import getErrorMsg_ValueError_Empty
from BEL42_Source.BEL42_TS.TSearch import DEFAULT_REASONING_EFFORT

def _summaryAI_modelcall(ToSum: str = ""):
    """
    This function let you to get a summary of all informations you got by the research system.
    It gets just one parameter: ToSum (string), that is the text the model will do a summary about.

    The model used in this function is google/gemma-4-26b-a4b-it:free.
    """
    if not ToSum:
        errmsg = getErrorMsg_ValueError_Empty("_summaryAI_modelcall", "ToSum", "string")
        raise ValueError(errmsg)
    
    client = OpenAI(
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("OPENROUTER_APIKEY")
    )

    prompt = f"""
        Make a summary of this informations got by a research. Please don't forget to put the sources. 
        The informations:
        {ToSum}
        """

    response = client.chat.completions.create(
        model=os.getenv("SUMMARY_MODEL"),
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content 


def _summaryAI_modeladvanced_call(to_summary: str = "",
                                  modelname: str = os.getenv("SUMMARY_MODEL"),
                                  reasoning_effort: str = DEFAULT_REASONING_EFFORT
                                  ):
    """
    This function let you get a summary of all informations got by the research system.
    The difference between this function and the '_summaryAI_modelcall' simple function is that here you 
    can specify modelname and reasoning_effort, that for default is 'medium'.
    parameters:

    to_summary (string) => is the text contains the informations got by the research
    modelname (string) => the name of the model we will use for doing the summary
    reasoning_effort (string) => is the level of reasoning the model will do, default is 'medium'

    The defualt model for summary is Google/Gemma-4-26b-a4b-it:free.
    """
    if not to_summary:
        errmsg = getErrorMsg_ValueError_Empty("_summaryAI_modeladvanced_call", "to_summary", "string")
        raise ValueError(errmsg)
    
    client = OpenAI(
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("OPENROUTER_APIKEY")
    )

    prompt = f"""
        Make a summary of this informations got by a research. Please don't forget to put the sources. 
        The informations:
        {to_summary}
        """
    
    response = client.chat.completions.create(
        model=modelname,
        reasoning_effort=reasoning_effort,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content 
    
    
    

