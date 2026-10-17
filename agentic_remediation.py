#ast -> Abstract Syntax Tree
#an ast represents python code as a structured tree of objects, such as function calls, atrributes, arguments, values
#instead of manually building a string caontaining py code, construct the function call as an AST and then convert it into py source code

import ast

#remediation functon
#drift -> input parameter containing information about the detected cloud configuration drift
def generate_remediation(drift):
    if drift.get("drift type") != "open_sg_port":
        raise ValueError("Unsupported Drift Type")
    
    sg_id = drift.get("security_group_id")
    port = drift.get("port")
    protocol = drift.get("protocol", "tcp")
    cidr = drift.get("cidr")