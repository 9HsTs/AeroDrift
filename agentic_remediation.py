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

    #Build the exact boto3 API call using AST
    #ast.list -> py list
    call = ast.Call(
        #represents accessing an attribute or method on an object
        func=ast.Attribute(
            value=ast.Name(id="ec2", ctx=ast.Load()),
            attr="revoke_security_group_ingress",
            ctx=ast.Load()
        ),

        #building the group id keyword
        args=[],
        keywords=[
            ast.keyword(
                arg="GroupId",
                value=ast.Constant(value=sg_id)
            ),

            #building Ip permission list
            ast.keyword(
                arg="IpPermissions",
                value=ast.List(
                    elts=[      #list elements
                        ast.Dict(
                            keys=[
                                ast.Constant(value="IpProtocol"),
                                ast.Constant(value="FromPort"),
                                ast.Constant(value="ToPort"),
                                ast.Constant(value="IpRanges")
                            ],
                            values=[
                                ast.Constant(value=protocol),
                                ast.Constant(value=port),
                                ast.Constant(value=port),
                                ast.List(
                                    elts=[
                                        ast.Dict(
                                            keys=[
                                                ast.Constant(
                                                    value="CidrIp"
                                                )
                                            ],
                                            values=[
                                                ast.Constant(value=cidr)
                                            ]
                                        )
                                    ],
                                    ctx=ast.Load()
                                )
                            ]
                        )
                    ],
                    ctx=ast.Load()
                )
            )
        ]
    )

    #Convert AST into a Python expression
    expression = ast.Expression(body=call)
    ast.fix_missing_locations(expression)

    #Generate readable Python code
    generated_code = ast.unparse(expression)

    #Validate generated syntax
    #this parses the generated string as a py expression
    ast.parse(generated_code, mode="eval")

    return generated_code

#asynchronous functon
async def main():

    # Import mock cloud state through the ingestion module
    state = await get_aws_state()

    #drift variable init
    drift = None

    # Find a publicly accessible SSH rule
    #iterarting over SG
    for sg in state["security_groups"]:
        for rule in sg["ingress_rules"]:

            #extracting the rule field 
            protocol = rule.get("IpProtocol")
            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")

            for ip_range in rule.get("IpRanges", []):

                cidr = ip_range.get("CidrIp")

                #the drift ditection condition
                if (
                    protocol == "tcp"
                    and from_port <= 22 <= to_port
                    and cidr == "0.0.0.0/0"
                ):
                    #drift dictionary
                    drift = {
                        "drift_type": "open_sg_port",
                        "security_group_id": sg["group_id"],
                        "port": 22,
                        "protocol": protocol,
                        "cidr": cidr
                    }

                    break

            if drift is not None:
                break

        if drift is not None:
            break

    #no drfit case
    if drift is None:
        print("No public SSH drift detected.")
        return

    # Generate remediation code from detected drift
    code = generate_remediation(drift)

    print("\n[Agentic Remediation]")
    print("Detected: Public SSH port is open")
    print("\nDrift data:\n")
    print(drift)

    print("\nGenerated boto3 call:\n")
    print(code)


if __name__ == "__main__":
    asyncio.run(main())


