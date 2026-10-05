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
    visited = set()
    
    #finding root nodes
    # Start from nodes that have no incoming edges.
    roots = [
        node for node in graph.nodes
        if graph.in_degree(node) == 0
    ]

    # Handle graphs without a root.
    if not roots and graph.number_of_nodes() > 0:
        roots = [next(iter(graph.nodes))]

    #recursive tree building
    def add_branch(parent, node):

        attrs = graph.nodes[node]
        name = attrs.get("name", str(node))
        resource_type = attrs.get("type", "resource")

        if attrs.get("type") == "internet":     #checks the current node us an internet node
            label = f"[red] {name}[/red]"
        elif attrs.get("type") == "database":   #database node
            label = f"[green] {name}[/green]"
        elif attrs.get("type") == "security_group":     #security group node
            label = f"[yellow] {name}[/yellow]"
        else:
            label = f"[cyan] {name}[/cyan]"

        #add node to rich tree
        branch = parent.add(label)

        # Avoid infinite recursion if the graph has cycles.
        if node in visited:
            branch.add("[dim]Already displayed[/dim]")
            return

        visited.add(node)

        #find child nodes
        for neighbor in graph.successors(node):
            add_branch(branch, neighbor)
    #process all root nodes
    for node in roots:
        add_branch(root, node)

    # Include any disconnected components.
    for node in graph.nodes:
        if node not in visited:
            add_branch(root, node)

    return root

# DISPLAY CLOUD TOPOLOGY
def show_topology(graph):

    console.print()
    console.print(
        Panel(
            build_topology_tree(graph),
            title="[bold cyan]AeroDrift[/bold cyan]",
            subtitle="Cloud Topology Explorer",
            border_style="cyan"
        )
    )




