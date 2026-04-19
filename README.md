# Blisk-EL42 AI System

Blisk-EL42 is an artificial intelligence system that uses some open-source models and OpenAI APIs with powerful web-searching engine and LangChain implementation.

---

## What can Blisk-EL42 do?

Blisk-EL42 can answer as a normal LLM thanks to the AI models he uses.
The power of Blisk-EL42 is the possibility of infinite plugins joining differents AI models and different tools.

Using these plugins, Blisk-EL42 is going to be able to carry out a lot of different tasks.

## The BEL42-TSS, the searching engine of Blisk-EL42

BEL42-TSS means Blisk-EL42 Tool Strong Search, because actually Blisk-EL42 has two differents web-searching systems:

- BEL42-TS (Blisk-EL42 Tool Search)
- BEL42-TSS (Blisk-EL42 Tool Strong Search)

The first is simpler than the second, so currently the main function of the model in the code (the function calle `blisk`, that we will see) uses only the BEL42-TSS.



## How does BEL42-TSS work 

BEL42-TSS works using the module `duckduckgo_search` to do the research, and the `cosine_similiarity` of `torch.nn.functional` for checking if research results are related to the text, and the system takes only the top 5 results with the best similiarity rate with the original query.
This similiarity-checking is because the model has to be accurate.

So, as soon as the model get the results, he does a ranking of the results based on their similiarity rate, takes the top 5, and then we have two differente modes:

- summary mode
- direct mode

If the current mode is summary mode, the summary-model (not the same model, another for this specific task) will make a summary based on the informations got by the 5 results.
If the current mode is direct mode, the model will get directly the results without any summary.

## Using LangChain for the model

LangChain is a very important part of Blisk-EL42, and it's employed for the model chain.
So, the file where the chain is made is `chatmemory_models.py`, where we can find the chain and the memory mechanism, that for now is only with JSON files.
We don't use just the standard library of `json` (Python), but you can find in the file `BEL42_Json.py` in the directory `BEL42_UTILS`, the class `BEL42_Json`, that is a very useful class for managing JSON files.

## The model with audio

The speech mode of Blisk-EL42 is being tested, as you can see in the directory `BEL42_AUDIO`, there is the directory `TEST`.
For now, this mode is not really implemented.

## The LICENSE 

The License of Blisk-EL42 is the **Apache 2.0** License.
You can find it in the directory `Docs`.

## Coming soon

- Chat memory linked to PostgreSQL or SQLite
- Audio mode working
- GUI and design


---
Valerio De Marchis 
valedemarchis2010@gmail.com


