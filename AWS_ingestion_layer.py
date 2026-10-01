#asyncio used to write concurrent code using the  async and await syntax used for asynchronpus prgm 
#boto3 ->allows py pgm to communicate with AWS
#pull current AWS infra data


"""AeroDrift AWS ingestion layer code"""

import asyncio
import boto3  #AWS SDK

#fetching EC2, subnet and security grps
#EC2 -> Elastic compute cloude

#ec2 -> creates AWS client for EC2 service
ec2 = boto3.client("ec2", region_name="us-east-1")

#async boto3 wraper
#**kwargs -> to pass optional arguments
async def async_boto3_call(func, **kwargs): # defines async function
  
    loop = asyncio.get_running_loop()   #loop manages asynchronous tasks as task manager

    #running boto3 in another thread
    return await loop.run_in_executor(
        None,
        lambda: func(**kwargs)
    )

#EC2 instance -> delivers secure, reliable virtual servers known as instance
#retrieving EC2 infor
async def get_ec2_instances():
    response = await async_boto3_call(
        ec2.describe_instances
    )

    instances = []  #empty list store EC2 info

    for reservation in response.get("Reservations", []): #loop through reservation in response i.e. describe_instances
        for instance in reservation.get("Instances", []): #each reservation can cantain 1 or more EC2 instances
                                                          #this lopp processes each individual instance

            #add EC2 information in instance list
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

    return instances   #return EC2 data


#subnet -> a logically isolated virtual network in the AWS to launch and secure resources
#asynchronous function for retrieve AWS subnet info
async def get_subnets():
    
    #call AWS ec2 api
    response = await async_boto3_call(
        ec2.describe_subnets
    )

    subnets = []  #empty subnet list

    #loop through AWS subnets response i.e. describe_subnets
    for subnet in response.get("Subnets", []):

        #add subnet information in list
        subnets.append({
            "subnet_id": subnet.get("SubnetId"),
            "vpc_id": subnet.get("VpcId"),
            "cidr_block": subnet.get("CidrBlock"),
            "availability_zone": subnet.get("AvailabilityZone"),
            "state": subnet.get("State")
        })

    return subnets

#security gropus ->a virtual firewall that controls incoming and outgoing trafiic for AWS resources such as EC2
#asynchronous function for retriving security groups
async def get_security_groups():

    #call AWS api
    response = await async_boto3_call(
        ec2.describe_security_groups
    )

    security_groups = []    #empty list for SG
    
    #loop through AWS subnets response i.e. describe_securitygrops
    for sg in response.get("SecurityGroups", []):

        #add securoty groups in list
        security_groups.append({
            "group_id": sg.get("GroupId"),
            "group_name": sg.get("GroupName"),
            "vpc_id": sg.get("VpcId"),
            "ingress_rules": sg.get("IpPermissions", []),
            "egress_rules": sg.get("IpPermissionsEgress", [])
        })

    return security_groups

#cloude state
#fetch complete AWS state
#gets all 3 types of AWS resourses  EC2, Subnet, SG

async def get_aws_state():

    ec2_task = get_ec2_instances()  #EC2 task
    subnet_task = get_subnets()     #subnet task
    sg_task = get_security_groups() #security groups task


    #run them CONCURRENTLY
    #asyncio.gather -> runs multiple asycnhronous operations concurrently
    ec2s, subnets, security_groups = await asyncio.gather(
        ec2_task,
        subnet_task,
        sg_task
    )

    #returns everything together
    #creates on large dictionary
    return {
        "ec2": ec2s,
        "subnets": subnets,
        "security_groups": security_groups
    }

#main asychronous function
async def main():

    state = await get_aws_state()       #fetch all AWS data calls combined functon
    #wait until EC2 data retrieved then subnet and then SG

    #print EC2 data
    print("\nEC2 INSTANCES")
    for instance in state["ec2"]:
        print(instance)

    #print Subnets
    print("\nSUBNETS")
    for subnet in state["subnets"]:
        print(subnet)

    #print Security Groups
    print("\nSECURITY GROUPS")
    for sg in state["security_groups"]:
        print(sg)

#python entry point -> this checks whether this file is being executed directly
        #run this part only when this file is executed directly

if __name__ == "__main__":
    asyncio.run(main())  #start thr async pgm

    #await main()
