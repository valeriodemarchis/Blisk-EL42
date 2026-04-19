try:
	from duckduckgo_search import DDGS
	from duckduckgo_search.exceptions import DuckDuckGoSearchException
	from transformers import BertTokenizer, BertModel
	
	import tiktoken
	import torch
	import torch.nn.functional as F
	from typing import List
		
	
	from openai import OpenAI
	from dotenv import load_dotenv
	import re 
	import os
	
except ImportError:
	raise ImportError("One of these libraries (or more than 1) is not installed: duckduckgo_search, beautifulsoup4, tiktoken, torch, transformers")
	
from checkAI import _summaryAI_modelcall
from syserrors import getErrorMsg_ValueError_Empty
from BEL42_UTILS.setutils import get_bert_model

load_dotenv()



DEFAULT_MAX_RESULTS_NUMBER = 20
DEFAULT_MIN_SIMPERC_AMOUNT = 65.00
DEFAULT_REASONING_EFFORT = "medium"

modelname = get_bert_model()
cosine_similiarity = F.cosine_similiarty
tokenizer = BertTokenizer.from_pretrained(modelname)
model = BertModel.from_pretrained(modelname)

DefaultMaxLength = 600
DefaultTruncation = True

model.eval()

class Article:
	def __init__(self, title: str, href: str, body: str, sim_percentage: float):
		self.title = title
		self.href = href
		self.body = body 
		self.sim_percentage = 0.00
	

def getResultsFromQuery(_mrn: int = DEFAULT_MAX_RESULTS_NUMBER, query: str = "") -> List[Article]:
	cresults = []
	if not query:
		errmsg = getErrorMsg_ValueError_Empty("getResultsFromQuery", "query", "string")
		raise ValueError(errmsg)
	
	with DDGS() as ddgs:
		results = list(ddgs.text(query, max_results=_mrn))
		for r in results:
			cresult = Article(title=r['title'], href=r['href'], body=r['body'])
			cresults.append(cresult)
			
	return cresults
	

def fsimiliarity(pquery1: str = "", pquery2: str = ""):
	if not pquery1 or not pquery2:
		raise ValueError("There is a problem about the method 'findSimiliarityWithQuery': the parameter 'pquery1' (string) or 'pquery2' (string) is empty.")
		
	# the encoding for query number 1 and 2:
	encoding1 = tokenizer(
		pquery1,
		padding=True,
		truncation=DefaultTruncation,
		max_length=DefaultMaxLength,
		return_tensors="pt"
	)
	
	encoding2 = tokenizer(
		pquery2,
		padding=True,
		truncation=DefaultTruncation,
		max_length=DefaultMaxLength,
		return_tensors="pt"
	)
	
	with torch.no_grad():
		outputs = model(**encoding1)
		outputs2 = model(**encoding2)
	
	ptensor1 = outputs.last_hidden_state
	ptensor2 = outputs2.last_hidden_state
	
	simperc = cosine_similiarity(ptensor1, ptensor2) * 100
	return simperc.item().mean()
	


class SearcherWithInherence:
	"""
	The SearcherWithInerence class is the searching mechanism of Blisk-ELK42.
	The class requires two parameters:
	
	==========================================================================
	        query        ||                   STRING
	==========================================================================
	   max_res_num       ||              INTEGER (BUT EXISTS THE DEFAULT)
	==========================================================================
	
	"""
	def __init__(self,
		query: str = "", 
		max_res_num: int = DEFAULT_MAX_RESULTS_NUMBER):
		
		if not query:
			raise ValueError("There is a problem using the class 'SearcherWithInerence': value of 'query' is empty.")
			
			
		self.query = query 
		self.max_res_num = max_res_num
		
	def activate(self) -> List[Article] | str:
		"""
		This method activates effectively the searcher, the result is a list of the results in type [object] Article.
		
		RETURN TYPE -> List[Article] OR STRING (it means that there is an error like ERROR::NO_RESULT).
		"""
		cresults = getResultsFromQuery(_mrn=self.max_res_num, query=self.query)
		sresults = []
		outputs = []
		
		for cres in cresults:
			sresult = f"""
			Title: {cres.title}
			Link: {cres.href}
			Body: {cres.body}
			"""
			sresults.append(sresult)
		
		for i, sres in enumerate(sresults):
			perc = fsimiliarity(self.query, sres)
			cresults[i].sim_percentage = perc
		
		outputs = sorted(cresults, key=lambda cres: cres.sim_percentage)
		outputs = outputs[:5]
			
		if len(outputs) == 0:
			return "ERROR::NO_RESULT"
		
		return outputs 
		



# with these two functions we implemented the searching mechanism for Blisk-EL42 (BEL42)
# let's implement the functions for analizing if the model needs our searching mechanism 

def analizeModel_O(model_output: str = "") -> str:
	modelAsk_forSearch = r"[% SEARCH | (.*?) %]"
	mafs = re.search(modelAsk_forSearch, model_output)
	if mafs:
		return mafs.group()
	else:
		return "NOT_NEEDED"
	
	
def BEL42_TSearch(model_output: str = "", output: str = "objects"):
	if not model_output:
		errmsg = getErrorMsg_ValueError_Empty("BEL42_TSearch", "model_output", "string")
		raise ValueError(errmsg)
	
	analizres = analizeModel_O(model_output=model_output)
	if analizres == "NOT_NEEDED":
		return None
	
	searcher = SearcherWithInherence(query=analizres)
	outputs = searcher.activate()
	sresult = ""
	
	if output == "objects":
		return outputs 
		
	for output in outputs:
		sres = f"""
		Title: {output.title}
		Link: {output.href}
		Body: {output.body}
		"""
		sresult += sres 
	
	result = _summaryAI_modelcall(ToSum=sresult)
	return result 




		

	
	
	

		
		
	
		
	
		
	
	
	
	
		
	
		
	
		
				
		
		
			
			
		
	
		
	
	
		
		
		
		
	


