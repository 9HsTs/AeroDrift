#detect whether a network path now exists from 0.0.0.0/0(internet) --> private database
#if such a path appears, AeroDrift can flag it as network security drift

import networkx as nx

graph = nx.DiGraph()

#internet
graph.add_node(
    "0.0.0.0/0",
    type="internet"
)

graph.add_node(
    "igw-001",
    type="internet_gateway"
)

graph.add_node(
    "subnet-public",
    type="public_subnet"
)

graph.add_node(
    "ec2-001",
    type="ec2"
)

graph.add_node(
    "subnet-private",
    type="private_subnet"
)

graph.add_node(
    "db-001",
    type="database",
    private = True
)

#network path
graph.add_edge("0.0.0.0/0", "igw-001")

graph.add_edge("igw-001","subnet-public")

graph.add_edge("subnet-public", "ec2-001")

graph.add_edge("ec2-001", "subnet-private")

graph.add_edge("subnet-private", "db-001")

#drift detection
