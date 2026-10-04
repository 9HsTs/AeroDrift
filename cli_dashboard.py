#RICH provides styled terminal output and tree rendering, while NetworkX stores and analyzes cloud topology
#rich -> a py library used to make terminal output more attractive and readable
#networkX is used to create and work with graphs

import networkx as nx

from rich.console import Console   #console class used to show op on terminal
from rich.tree import Tree         #tree class i.e. hierarchical data
from rich.panel import Panel        #create box
from rich.table import Table        #create table format
from rich.prompt import Prompt      #takes user input
from rich.text import Text          #text manipulation

#console object
console = Console()

# SAMPLE CLOUD TOPOLOGY
# Replace this function's graph with your AWS graph.
#sample cloud graph topology
def create_sample_graph():

    graph = nx.DiGraph()

    #creating nodes
    graph.add_node(
        "internet",
        name="Internet (0.0.0.0/0)",
        type="internet"
    )

    graph.add_node(
        "vpc-001",
        name="VPC: vpc-001",
        type="vpc"
    )

    graph.add_node(
        "sg-web",
        name="Security Group: sg-web",
        type="security_group",
        port=22,
        cidr="0.0.0.0/0"
    )

    graph.add_node(
        "ec2-web",
        name="EC2: web-server",
        type="ec2"
    )

    graph.add_node(
        "db-001",
        name="Private Database: db-001",
        type="database",
        private=True
    )

    #creating edges and connect the resources
    graph.add_edges_from([
        ("internet", "vpc-001"),
        ("vpc-001", "sg-web"),
        ("sg-web", "ec2-web"),
        ("ec2-web", "db-001")
    ])

    return graph

#building the rich tree
def build_topology_tree(graph):
    root = Tree(
        "[bold cyan]AWS Cloud Topology[/bold cyan]"
    )



