#asyncio used to write concurrent code using the  async and await syntax used for asynchronpus prgm 
#boto3 ->allows py pgm to communicate with AWS
#pull current AWS infra data

"""AeroDrift AWS ingestion layer code"""

import asyncio
import boto3

#EC2 -> Elastic compute cloude
#creates AWS client for EC2 service

ec2 = boto3.client("ec2", region_name="us-east-1")

#async boto3 wraper
#**kwargs -> to pass optional arguments
async def async_boto3_call(func, **kwargs): #async function
  
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
        None,
        lambda: func(**kwargs)
    )

#EC2 instance -> delivers secure, reliable virtual servers known as instance

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

#subnet -> a logically isolated virtual network in the AWS to launch and secure resources

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

#security gropus ->a virtual firewall that controls incoming and outgoing trafiic for AWS resources such as EC2

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

#cloude state

async def get_aws_state():

    ec2_task = get_ec2_instances()
    subnet_task = get_subnets()
    sg_task = get_security_groups()

    ec2s, subnets, security_groups = await asyncio.gather(
        ec2_task,
        subnet_task,
        sg_task
    )
