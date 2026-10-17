import ast

def generate_remediation(drift):
    if drift.get("drift type") != "open_sg_port":
        raise ValueError("Unsupported Drift Type")
    
    sg_id = drift.get("security_group_id")
    port = drift.get("port")
    protocol = drift.get("protocol", "tcp")
    cidr = drift.get("cidr")