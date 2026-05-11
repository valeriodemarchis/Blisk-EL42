
import torch 
from .settings import (
    DefaultMaxLength,
    DefaultTruncation,
)

from .BEL42_TS import (
    tokenizer, 
    model
)

from BEL42_UTILS.error_utils import (
    check_parameter_value_error_if_empty_string
)

def tokenize_blisk_output(blisk_output: str = "") -> torch.Tensor:
    check_parameter_value_error_if_empty_string(
        parameter=blisk_output, parameterName="blisk_output",
        functName="tokenize_blisk_output", ParamT="string"
    )
    
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


def simple_tokenize(simple_query: str = ""):
    check_parameter_value_error_if_empty_string(
        parameter=simple_query, parameterName="simple_query",
        functName="simple_tokenize", ParamT="string"
    )

    encoding = tokenizer(
        simple_query, 
        padding=True,
        max_length=DefaultMaxLength,
        truncation=DefaultTruncation,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**encoding)
    
    return outputs.last_hidden_state
    