

# now we can handle the result of the RestritedPython execution and then make the message ready for the model
# with the function 'handle_restricted_python_result' we do exactly this


def handle_restricted_python_result(outcome: dict) -> str:
    if outcome["success"]:
        final = f"""
        The code has been executed with success.
        The output is:
        {outcome["output"]}
        """
        return final 
    else:
        final = f"""
        The code has been executed with errors. 
        The error is:
        {outcome["error"]}
        """ 
        return final 
    
