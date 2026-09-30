#working with graphs/network
import networkx as nx

def build_aws_graph(aws_data):
    graph = nx.DiGraph()


    for vpc in aws_data.get("vpcs", []):
        vpc_id = vpc["VpcId"]

        graph.add_node(
            vpc_id,
            resource_type="VPC",
            name=vpc_id
        )

   