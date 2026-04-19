try:
    from duckduckgo_search import DDGS 
    import torch.nn.functional as funct 
    from typing import List 
    from openai import OpenAI
    from transformers import BertTokenizer, BertModel 
    from dotenv import load_dotenv
    import os
    from torch import no_grad

except ImportError:
    raise ImportError("One of the following modules (or more than 1) is not installed: torch, dotenv, duckduckgo_search, torch, openai, transformers")

from TSearch import (
    DEFAULT_MAX_RESULTS_NUMBER,
    DEFAULT_MIN_SIMPERC_AMOUNT,
    DEFAULT_REASONING_EFFORT,
    modelname,
    DefaultMaxLength,
    DefaultTruncation,
    Article
)

from syserrors import (
    getErrorMsg_ValueError_Empty,
    getErrorMsg_ValueError_NotOption
)

from checkAI import _summaryAI_modeladvanced_call
from TSearch import analizeModel_O
from settings import SUMMARY_MODEL

similiarity = funct.cosine_similarity


class TSS_Article:
	def __init__(self):
		self.title = ""
		self.href = ""
		self.body = ""
		self.attributes = [self.title, self.href, self.body, self.sim]
		self.sim = 0.00
	
	def set_title(self, _nt: str = "") -> None:
		if not _nt:
			errmsg = getErrorMsg_ValueError_Empty("TSS_Article.set_title", "_nt", "string")
			raise ValueError(errmsg)
		
		self.title = _nt 
		self.attributes[0] = _nt
	
	def set_href(self, _hf: str = "") -> None:
		if not _hf:
			errmsg = getErrorMsg_ValueError_Empty("TSS_Article.set_href", "_hf", "string")
			raise ValueError(errmsg)
		
		self.href = _hf
		self.attributes[1] = _hf
	
	def set_body(self, _bd: str = "") -> None:
		if not _bd:
			errmsg = getErrorMsg_ValueError_Empty("TSS_Article.set_body", "_bd", "string")
			raise ValueError(errmsg)
		
		self.body = _bd 
		self.attributes[2] = _bd

	def set_sim(self, _sim: float = 0.00) -> None:
		self.sim = _sim
		self.attributes[3] = _sim

	def to_simple_article(self) -> Article:
		article = Article(self.title, self.href, self.body)
		return article
	
	def to_list(self) -> List[str]:
		return self.attributes
	



class TSS_Searcher:
    """
    The class TSS_Searcher is more powerful than the simple SearcherWithInerence of TSearch.py
    Here you can put the max_res_num (int), so the maximum number of results given by the research,
    the reasoning_effort (string), so the level of reasoning the model will use for giving the response (the default is 'medium') 
    and the summary_model (string), that is the model that will do the summary, the default is google/gemma-4-26b-a4b-it:free.

    This class do at the __init__ method:
    - setup of attributes
    - checking if query is empty
    - search informations
    - get all in classes (TSS_Article: object)
    - using the BERT tokenizer and model for encoding
    - calculating the similiarity with the query
    
    The method _findTop does:
    - ranking the top 5 results with higher similiarity rate
    
    The method _makeSummary does:
    - make a unique text from all the results
    - make a summary about this text
    - returns the summary (so the final output)

    The method _retdirect does:
    - DOESN'T make the summary
    - just return the unique text of all the results
    """
    def __init__(self,
                squery: str = "",
                max_res_num: int = DEFAULT_MAX_RESULTS_NUMBER,
                reasoning_effort: str = DEFAULT_REASONING_EFFORT,
                summary_model: str = SUMMARY_MODEL,
                ):
        
        
        # we will use it for saving the top results of our research:
        self.top = []

        # settings the attributes:
        self.reasoning_effort = reasoning_effort
        self.summary_model = summary_model
        
        # this Searcher is stronger becuase we can add more arguments and make a more precise setup
        # if search query is empty (squery: string) we can't continue:
        if not squery:
            errormsg = getErrorMsg_ValueError_Empty("TSS_Searcher.__init__", "squery", "string")
            raise ValueError(errormsg)
        
        # now search:
        with DDGS() as ddgs:
            results = list(ddgs.text(squery, max_results=max_res_num))
            self.fresults = []
            for res in results:
                obj = TSS_Article()
                obj.set_title(res['title'])
                obj.set_href(res['href'])
                obj.set_body(res['body'])
                self.fresults.append(obj)
            
        # we saved all results in a list of classes (TSS_Article: object)
        # now tokenizer and model:

        self.tokenizer = BertTokenizer.from_pretrained(modelname)
        self.model = BertModel.from_pretrained(modelname)

        encoding_query = self.tokenizer(
                squery, padding=True, truncation=DefaultTruncation,
                max_length=DefaultMaxLength, return_tensors="pt"
            )

        with no_grad():
            query_outputs = self.model(**encoding_query)
        
        self.tquery = query_outputs.last_hidden_state

        # now let's make all the objects we got in strings:

        self.sresults = [] # results in strings
        for res in self.fresults:
            sres = f"""
            Title: {res.title}
            Link: {res.href}
            Body: {res.body}
            """
            self.sresults.append(sres)

        for i, el in enumerate(self.sresults):
            encoding = self.tokenizer(
                el, padding=True, truncation=DefaultTruncation, max_length=DefaultMaxLength,
                return_tensors="pt"
            )

            with no_grad():
                outputs = self.model(**encoding)
                
            tensor = outputs.last_hidden_state

            sim = similiarity(self.tquery, tensor)
            self.fresults[i].set_sim(float(sim))

    
    def _findTop(self, top: int = 5) -> None:
        self.fresults = sorted(self.fresults, key=lambda fres: fres.sim)
        self.top = self.fresults[:top]
        
    def _makeSummary(self):
        final = ""
        for res in self.top:
            rtop = f"""
            title: {res.title}
            link: {res.href}
            body: {res.body}
            """
            final += f"\n{rtop}"
        
        summary = _summaryAI_modeladvanced_call(
            to_summary=final, modelname=self.summary_model, 
            reasoning_effort=self.reasoning_effort
        )

        return summary 
    
    def _retdirect(self):
        "So you don't like the summaries..."
        final = ""
        for res in self.top:
            rtop = f"""
            title: {res.title}
            link: {res.href}
            body: {res.body}
            """
            final += f"\n{rtop}"
        
        return final
    

def BEL42_TSSearch(modelmsg: str = "",
                   max_res_num: int = DEFAULT_MAX_RESULTS_NUMBER,
                   reasoning_effort: str = DEFAULT_REASONING_EFFORT,
                   summary_modeln: str = SUMMARY_MODEL,
                   output: str = "summary") -> str | None:
    """
    The BEL42_TSSearch function return a summary (or directly results if you set 'output' to 'direct') 
    of the research.
    You can put directly the model message, this function will check if the model needs a research:
    - if the model needs a research, the function will search and returns a message with instructions and the
    research result, that you can directly send to the model.
    - if the model doesn't need the research, the function will return None.
    """

    if not modelmsg: 
        errmsg = getErrorMsg_ValueError_Empty("BEL42_TSSearch", "modelmsg", "string")
        raise ValueError(errmsg)
    
    if (output != "summary" and output != "direct"):
          errmsg = getErrorMsg_ValueError_NotOption(
                "BEL42_TSSearch", "output", "string", ["summary", "direct"]
          )
          raise ValueError(errmsg)
    
    analizeres = analizeModel_O(model_output=modelmsg)
    if analizeres == "NOT_NEEDED":
        return None

    searcher = TSS_Searcher(
        squery=analizeres,
        max_res_num=max_res_num,
        reasoning_effort=reasoning_effort,
        summary_model=summary_modeln
    )
    searcher._findTop()
    
    if output == "summary":
        return searcher._makeSummary()
    
    if output == "direct":
         return searcher._retdirect()

    

    

    
    
    


    

        
        


        
        
        


          
          
        



            

            
        
        




        

