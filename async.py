#this is mock code 
#not include boto3 module
import asyncio

MOCK_EC2 = [
    {
        "InstanceId": "i-001",
        "InstanceType": "t2.micro",
        "State": {"Name": "running"},
        "SubnetId": "subnet-001",
        "SecurityGroups": [
            {"GroupId": "sg-001"}
        ]
    },
    {
        "InstanceId": "i-002",
        "InstanceType": "t2.small",
        "State": {"Name": "running"},
        "SubnetId": "subnet-002",
        "SecurityGroups": [
            {"GroupId": "sg-002"}
        ]
    }
]


MOCK_SUBNETS = [
    {
        "SubnetId": "subnet-001",
        "VpcId": "vpc-001",
        "CidrBlock": "10.0.1.0/24",
        "AvailabilityZone": "us-east-1a",
        "State": "available"
    },
    {
        "SubnetId": "subnet-002",
        "VpcId": "vpc-001",
        "CidrBlock": "10.0.2.0/24",
        "AvailabilityZone": "us-east-1b",
        "State": "available"
    }
]


MOCK_SECURITY_GROUPS = [
    {
        "GroupId": "sg-001",
        "GroupName": "web-server",
        "VpcId": "vpc-001",
        "IpPermissions": [
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80
            }
        ],
        "IpPermissionsEgress": [
            {
                "IpProtocol": "-1"
            }
        ]
    },
    {
        "GroupId": "sg-002",
        "GroupName": "app-server",
        "VpcId": "vpc-001",
        "IpPermissions": [
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22
            }
        ],
        "IpPermissionsEgress": [
            {
                "IpProtocol": "-1"
            }
        ]
    }
]