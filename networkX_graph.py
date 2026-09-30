# networkx -> py library for creating, analyzing and working with graphs/network
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

   