#asyncio used to write concurrent code using the  async and await syntax used for asynchronpus prgm 
#boto3 ->allows py pgm to communicate with AWS
#pull current AWS infra data

"""AeroDrift AWS ingestion layer code"""

import asyncio

class MockEC2Client:
#fetching EC2, subnet and security grps
#EC2 -> Elastic compute cloude

#ec2 -> creates AWS client for EC2 service
    def describe_instances(self, **kwargs):
        return {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-mock-app001",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "running"},
                            "SubnetId": "subnet-mock-public",
                            "SecurityGroups": [
                                {"GroupId": "sg-mock-app"}
                            ]
                        },
                        {
                            "InstanceId": "i-mock-db001",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "running"},
                            "SubnetId": "subnet-mock-private",
                            "SecurityGroups": [
                                {"GroupId": "sg-mock-db"}
                            ]
                        }
                    ]
                }
            ]
        }
    
#subnet -> a logically isolated virtual network in the AWS to launch and secure resources
#asynchronous function for retrieve AWS subnet info
    def describe_subnets(self, **kwargs):
        return {
            "Subnets": [
                {
                    "SubnetId": "subnet-mock-public",
                    "VpcId": "vpc-mock001",
                    "CidrBlock": "10.0.1.0/24",
                    "AvailabilityZone": "us-east-1a",
                    "State": "available"
                },
                {
                    "SubnetId": "subnet-mock-private",
                    "VpcId": "vpc-mock001",
                    "CidrBlock": "10.0.2.0/24",
                    "AvailabilityZone": "us-east-1b",
                    "State": "available"
                }
            ]
        }

#security gropus ->a virtual firewall that controls incoming and outgoing trafiic for AWS resources such as EC2
#asynchronous function for retriving security groups
    def describe_security_groups(self, **kwargs):
        return {
            "SecurityGroups": [
                {
                    "GroupId": "sg-mock-app",
                    "GroupName": "app-security",
                    "VpcId": "vpc-mock001",
                    "IpPermissions": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 22,
                            "ToPort": 22,
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ],
                    "IpPermissionsEgress": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ]
                },
                {
                    "GroupId": "sg-mock-db",
                    "GroupName": "database-security",
                    "VpcId": "vpc-mock001",
                    "IpPermissions": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 5432,
                            "ToPort": 5432,
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ],
                    "IpPermissionsEgress": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ]
                }
            ]
        }

# Use local mock data instead of making real AWS API calls.
ec2 = MockEC2Client()

async def async_boto3_call(func, **kwargs):
   
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
        None,
        lambda: func(**kwargs)
    )

async def get_ec2_instances():
    response = await async_boto3_call(
        ec2.describe_instances
    )

    instances = []

    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):

            instances.append({
                "instance_id": instance.get("InstanceId"),
                "instance_type": instance.get("InstanceType"),
                "state": instance.get("State", {}).get("Name"),
                "subnet_id": instance.get("SubnetId"),
                "security_groups": [
                    sg["GroupId"]
                    for sg in instance.get("SecurityGroups", [])
                ]
            })

    return instances

async def get_subnets():
    response = await async_boto3_call(
        ec2.describe_subnets
    )

    subnets = []

    for subnet in response.get("Subnets", []):

        subnets.append({
            "subnet_id": subnet.get("SubnetId"),
            "vpc_id": subnet.get("VpcId"),
            "cidr_block": subnet.get("CidrBlock"),
            "availability_zone": subnet.get("AvailabilityZone"),
            "state": subnet.get("State")
        })

    return subnets

async def get_security_groups():
    response = await async_boto3_call(
        ec2.describe_security_groups
    )

    security_groups = []

    for sg in response.get("SecurityGroups", []):

        security_groups.append({
            "group_id": sg.get("GroupId"),
            "group_name": sg.get("GroupName"),
            "vpc_id": sg.get("VpcId"),
            "ingress_rules": sg.get("IpPermissions", []),
            "egress_rules": sg.get("IpPermissionsEgress", [])
        })

    return security_groups

async def get_aws_state():

    ec2_task = get_ec2_instances()
    subnet_task = get_subnets()
    sg_task = get_security_groups()

    ec2s, subnets, security_groups = await asyncio.gather(
        ec2_task,
        subnet_task,
        sg_task
    )

    return {
        "ec2": ec2s,
        "subnets": subnets,
        "security_groups": security_groups
    }

async def main():

    state = await get_aws_state()

    print("\n===== EC2 INSTANCES =====")
    for instance in state["ec2"]:
        print(instance)

    print("\n===== SUBNETS =====")
    for subnet in state["subnets"]:
        print(subnet)

    print("\n===== SECURITY GROUPS =====")
    for sg in state["security_groups"]:
        print(sg)


if __name__ == "__main__":
    asyncio.run(main())