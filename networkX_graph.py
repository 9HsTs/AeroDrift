#networkx -> py library for creating, analyzing and working with graphs/network
#graph containing nodes and edges
#nodes -> AWS resources
#edges -> relationship bet resources

import networkx as nx

#graph building function
#convert the ingested data into a graph
def build_aws_graph(aws_data):
    graph = nx.DiGraph()  #DiGraph -> Directed Graph

    #loop through all vpc in aws
    #.get()-> get the vpc data. if not exits then return empty list
    for vpc in aws_data.get("vpcs", []):
        vpc_id = vpc["VpcId"]

        #add vpc as node in graph
        graph.add_node(
            vpc_id,
            resource_type="VPC",
            name=vpc_id
        )

#add subnet nodes
        #loops throungh all available subnets
    for subnet in aws_data.get("subnets", []):
        subnet_id = subnet["SubnetId"]  #get the subnet id
        vpc_id = subnet["VpcId"]        #get the vpc id

    #add the subnet as a node
    #this creates a networkX node
    graph.add_node(
            subnet_id,
            resource_type="Subnet",
            name=subnet_id
        )

    #check whether the VPC exists
    #if exists, then create a realtion betweeen vpc and subnet
    if vpc_id in graph:
                #creates an edge
                graph.add_edge(
                vpc_id,
                subnet_id,
                relationship="contains"
            )
    
    #process EC2 instances from AWS data
    for instance in aws_data.get("instances", []):
        instance_id = instance["InstanceId"]  #get EC2 instance ID
        
        #add EC2 as a node this creates an node
        graph.add_node(
            instance_id,
            resource_type="EC2",
            name=instance_id
        )
        #subnet id , which subnet conatains the EC2 instance
        subnet_id = instance.get("SubnetId")

         # EC2 is connected to its subnet
        #checks that the subnet is already present as a node
        #checks that a subnet ID actually exists

        if subnet_id and subnet_id in graph:
            graph.add_edge(
                subnet_id,
                instance_id,
                relationship="contains"
            )
    #process security groups
    for sg in aws_data.get("security_groups", []):
        sg_id = sg["GroupId"]   #get security group id

        #add security group as node
        graph.add_node(
            sg_id,
            resource_type="SecurityGroup",
            name=sg.get("GroupName", sg_id) #if group name exist use it, otherwise use gropu id
        )

    #process EC2 security gropu relationship
    #to find which SG are attached to which EC2 instance
    for instance in aws_data.get("instances", []):
        instance_id = instance["InstanceId"]        #get ec2 id

        for sg in instance.get("SecurityGroups", []):
            sg_id = sg["GroupId"]       #get security group id 

            #check both nodes
            if sg_id in graph and instance_id in graph:

                #ec2 security group realtionship
                graph.add_edge(
                    instance_id,
                    sg_id,
                    relationship="protected_by"
                )

    return graph        

#print graph function
#display the graph information
#not build but prints the it
def print_graph(graph):

    print("\n========== AWS GRAPH ==========\n")

    print("NODES:")
    #loops through all graph nodes
    #data = true -> nodes attribute
    for node, attributes in graph.nodes(data=True):
        print(
            node,
            "->",
            attributes
        )

    print("\nEDGES:")
    for source, target, attributes in graph.edges(data=True):
        print(
            source,
            "-->",
            target,
            attributes
        )

    print("\n================================")
    print("Total Nodes :", graph.number_of_nodes())
    print("Total Edges :", graph.number_of_edges())

#mock aws data
aws_data = {

    "vpcs": [
        {
            "VpcId": "vpc-001"
        }
    ],

    "subnets": [
        {
            "SubnetId": "subnet-001",
            "VpcId": "vpc-001"
        }
    ],

    "instances": [
        {
            "InstanceId": "i-001",
            "SubnetId": "subnet-001",

            "SecurityGroups": [
                {
                    "GroupId": "sg-001"
                }
            ]
        }
    ],

    "security_groups": [
        {
            "GroupId": "sg-001",
            "GroupName": "web-server-sg"
        }
    ]
}

#build graph   
aws_graph = build_aws_graph(aws_data)

print_graph(aws_graph)
