#ast -> Abstract Syntax Tree
#an ast represents python code as a structured tree of objects, such as function calls, atrributes, arguments, values
#instead of manually building a string caontaining py code, construct the function call as an AST and then convert it into py source code

import ast
import asyncio

#import mock aws data
from mock_aws import get_aws_state

#remediation functon
#drift -> input parameter containing information about the detected cloud configuration drift
def generate_remediation(drift):
    if drift.get("drift type") != "open_sg_port":
        raise ValueError("Unsupported Drift Type")
    
    sg_id = drift.get("security_group_id")
    port = drift.get("port")
    protocol = drift.get("protocol", "tcp")
    cidr = drift.get("cidr")


    #validating the input
    #isinstance -> checks value is string
    #startwith -> check prefix
    if not isinstance(sg_id, str) or not sg_id.startswith("sg-"):
        raise ValueError("Invalid Security Group ID")

    #checks port number
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Invalid port number")

    #checks protocol
    if protocol not in ("tcp", "udp", "icmp", "-1"):
        raise ValueError("Unsupported protocol")

    #checks CIDR values
    if not isinstance(cidr, str) or not cidr:
        raise ValueError("CIDR is required")

