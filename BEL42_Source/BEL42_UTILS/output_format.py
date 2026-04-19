
import torch 
from settings import (
    DefaultMaxLength,
    DefaultTruncation,
)

from BEL42_TS import (
    getErrorMsg_ValueError_Empty,
    tokenizer, 
    model
)


def tokenize_blisk_output(blisk_output: str = "") -> torch.Tensor:
    if not blisk_output:
        errmsg = getErrorMsg_ValueError_Empty("tokenize_blisk_output", "blisk_output", "string")
        raise ValueError(errmsg)
    
    encoding = tokenizer(
        blisk_output,
        padding=True,
        max_length=DefaultMaxLength,
        truncation=DefaultTruncation,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**encoding)
    
    return outputs.last_hidden_state 


    
    