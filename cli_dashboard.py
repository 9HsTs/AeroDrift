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

# DETECT INTERNET-TO-PRIVATE-DATABASE PATHS
#search for a ptemtially dangerous path   - internet ---> private database
def detect_drift(graph):

    #find internet node and returns node and attribute
    internet_nodes = [
        node for node, attrs in graph.nodes(data=True)
        if (
            attrs.get("type") == "internet"
            or attrs.get("cidr") == "0.0.0.0/0"
            or attrs.get("name") == "Internet (0.0.0.0/0)"
        )
    ]

    #find private database
    #returns evry node and attributes
    database_nodes = [
        node for node, attrs in graph.nodes(data=True)
        if (
            attrs.get("type") == "database"
            and attrs.get("private", False)
        )
    ]

    #create result table
    table = Table(title="Drift Detection Results")
    table.add_column("Internet Source", style="cyan")
    table.add_column("Private Database", style="green")
    table.add_column("Result", style="bold")

    #track drift
    found = False

    for source in internet_nodes:       #loop in internet node
        for database in database_nodes: #lopp in private database

            #if suspicious path exists
            if nx.has_path(graph, source, database):

                found = True

                #get the acutal path
                path = nx.shortest_path(
                    graph, source, database
                )

                #add results on table
                table.add_row(
                    str(source),
                    str(database),
                    "[bold red]PATH EXISTS[/bold red]"
                )

                console.print(
                    "[yellow]Potential exposure path:[/yellow]"
                )

                for index, node in enumerate(path):     #enumerate --> gives index and node
                    console.print(
                        f" {index + 1}. "
                        f"{graph.nodes[node].get('name', node)}"
                    )

    #if drift is not found
    if not found:
        console.print(
            "[green]No Internet-to-private-database "
            "path found in this graph.[/green]"
        )
    else:
        console.print(
            "[bold red]Review security rules and "
            "network controls immediately.[/bold red]"
        )

    if found:
        console.print(table)

#SHOW RESOURCE INVENTORY
#display all cloud resources
def show_resources(graph):

    #create table
    table = Table(title="Cloud Resource Inventory")

    #add coloumns in table
    table.add_column("Resource ID", style="cyan")
    table.add_column("Resource Name")
    table.add_column("Type", style="yellow")

    #loop in resources
    for node, attrs in graph.nodes(data=True):
        table.add_row(
            str(node),
            str(attrs.get("name", node)),
            str(attrs.get("type", "resource"))
        )

    console.print(table)

#INTERACTIVE CLI MENU
#main user interface
def main():

    graph = create_sample_graph()

    while True:

        console.print()
        console.print(
            Panel(
                "[1] View Cloud Topology\n"
                "[2] Detect Drift\n"
                "[3] List Cloud Resources\n"
                "[4] Exit",
                title="AeroDrift CLI Menu",
                border_style="blue"
            )
        )

        choice = Prompt.ask(
            "Select an option",
            choices=["1", "2", "3", "4"]
        )

        if choice == "1":
            show_topology(graph)

        elif choice == "2":
            detect_drift(graph)

        elif choice == "3":
            show_resources(graph)

        elif choice == "4":
            console.print(
                "[bold cyan]AeroDrift stopped. Goodbye![/bold cyan]"
            )
            break


if __name__ == "__main__":
    main()