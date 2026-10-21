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

    print("\nDEBUG : Received Drift = ", repr(drift))

    if not isinstance(drift, dict):
        raise TypeError(f"Expected dictionary, got {type(drift).__name__}")
    
    drift_type = drift.get("drift_type")

    print("DEBUG : drift_type =",repr(drift_type))

    if drift_type != "open_sg_port":
        raise ValueError(f"Unsupported Drift Type : {drift_type!r}")
    #if drift.get("drift type") != "open_sg_port":
        #raise ValueError("Unsupported Drift Type")
    
    #remediation parameters
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

 #DRIFT DETECTION FROM MOCK AWS DATA
def detect_drifts(state):
    
    drifts = []

    for sg in state.get("security_groups", []):
        sg_id = sg.get("group_id")

        for rule in sg.get("ingress_rules", []):
            protocol = rule.get("IpProtocol")
            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")

            # This remediation generator handles one exact port.
            # Skip protocols or port ranges it cannot safely handle.
            if protocol not in ("tcp", "udp"):
                continue

            if (
                type(from_port) is not int
                or type(to_port) is not int
                or from_port != to_port
            ):
                continue

            for ip_range in rule.get("IpRanges", []):
                cidr = ip_range.get("CidrIp")

                if cidr == "0.0.0.0/0":
                    drifts.append({
                        "drift_type": "open_sg_port",
                        "security_group_id": sg_id,
                        "port": from_port,
                        "protocol": protocol,
                        "cidr": cidr
                    })

    return drifts

#CONNECT INGESTION -> DETECTION -> REMEDIATION
async def main():

    print("\n========== AERODRIFT ==========")
    print("Loading cloud state from mock_aws.py")

    #Ingest mock cloud state.
    #import mock data
    state = await get_aws_state()

    print("\n[1] MOCK AWS INGESTION")
    print("EC2 instances:", len(state.get("ec2", [])))
    print("Subnets:", len(state.get("subnets", [])))
    print("Security groups:", len(state.get("security_groups", [])))

    #Detect drift using the ingested state.
    drifts = detect_drifts(state)

    print("\n[2] DRIFT DETECTION")

    if not drifts:
        print("No matching public TCP/UDP port exposure detected.")
        return

    for index, drift in enumerate(drifts, start=1):
        print(f"\nDrift No {index}")
        print("Type:", drift["drift_type"])
        print("Security Group:", drift["security_group_id"])
        print("Protocol:", drift["protocol"])
        print("Port:", drift["port"])
        print("Public CIDR:", drift["cidr"])

    #Generate remediation code for each drift.
    print("\n[3] GENERATED REMEDIATION CODE")

    for index, drift in enumerate(drifts, start=1):
        print("\nDEBUG DRIFT : ", drift)
        print("DEBUG DRIFT TYPE : ", repr(drift.get("drift_type")))
        code = generate_remediation(drift)

        print(f"\nRemediation No : {index}")
        print("Target:", drift["security_group_id"])
        print(code)

    print("\n[4] STATUS")
    print("Drift detection completed.")
    print("Remediation code generated; no changes executed.")


if __name__ == "__main__":
    asyncio.run(main())