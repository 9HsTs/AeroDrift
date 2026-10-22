#ast -> Abstract Syntax Tree
#represents py code as a structured tree of objects
#allows sandbox to inspect code without executing it first

import ast
import asyncio

from mock_aws import get_aws_state, MockEC2Client
from agentic_remediation import (
    detect_drifts,
    generate_remediation
)

#valdate the generated remediation code
#allow only ec2.revoke_security_ingress()
def validate_remediation_code(generated_code):
   
    #parse the geneated code
    tree = ast.parse(generated_code, mode="exec")

    # Exactly one top-level statement is allowed.
    if len(tree.body) != 1:
        raise ValueError(
            "Only one remediation statement is allowed"
        )
    #used zero based indexing
    #retrieve the statement
    statement = tree.body[0]

    # check expresion
    if not isinstance(statement, ast.Expr):
        raise ValueError("Only a function call is allowed")

    #extract the function call
    call = statement.value

    #expression == function call
    if not isinstance(call, ast.Call):
        raise ValueError("Invalid remediation call")

    #check function structure
    # Allow only ec2.revoke_security_group_ingress(...)
    if not isinstance(call.func, ast.Attribute):
        raise ValueError("Invalid function")

    #allows only intended method
    if call.func.attr != "revoke_security_group_ingress":
        raise ValueError("Function not allowed")

    #receiver name
    if not isinstance(call.func.value, ast.Name):
        raise ValueError("Invalid function receiver")

    #ec2 receiver
    if call.func.value.id != "ec2":
        raise ValueError("Only the ec2 client is allowed")

    # Reject positional arguments and **kwargs.
    if call.args:
        raise ValueError("Positional arguments are not allowed")

    #define allowed keywords arguments
    allowed_keywords = {"GroupId", "IpPermissions"}

    #collect the supplied keywords
    keyword_names = [kw.arg for kw in call.keywords]

    #reject the dynamic keyword expansion
    if any(name is None for name in keyword_names):
        raise ValueError("Dynamic keyword arguments are not allowed")

    #reuire the exact set of keyword names
    if set(keyword_names) != allowed_keywords:
        raise ValueError("Invalid remediation arguments")

    #reject duplicates
    if len(keyword_names) != len(set(keyword_names)):
        raise ValueError("Duplicate arguments are not allowed")

    # Arguments must contain only literal Python values.
    for keyword in call.keywords:
        try:
            ast.literal_eval(keyword.value)
        except (ValueError, TypeError):
            raise ValueError(
                "Only literal argument values are allowed"
            )

    return generated_code

#sandbox execution code
def execute_sandbox(generated_code, mock_ec2):
   

    safe_code = validate_remediation_code(generated_code)

    # Only the mock EC2 client is provided to the code.
    restricted_globals = {"__builtins__": {}}
    restricted_locals = {"ec2": mock_ec2}

    #built in py function that executes py code dynamically

    exec(
        safe_code,                  #py code -> remediation code
        restricted_globals,         #global namespaces
        restricted_locals           #local namespaces
    )

    print("\nSANDBOX EXECUTION COMPLETED.\n")

async def main():

    print("\n========== AERODRIFT SANDBOX ==========")

    # Load mock cloud state.
    state = await get_aws_state()

    # Detect cloud configuration drifts.
    drifts = detect_drifts(state)

    if not drifts:
        print("No matching drift found.")
        return

    # Create the mock client used for execution.
    mock_ec2 = MockEC2Client()

    for index, drift in enumerate(drifts, start=1):

        print(f"\nDrift {index}: {drift}")

        # Generate rollback code using the existing module.
        generated_code = generate_remediation(drift)

        print("\nGenerated code:")
        print(generated_code)

        # Execute only after validation.
        execute_sandbox(generated_code, mock_ec2)


if __name__ == "__main__":
    asyncio.run(main())