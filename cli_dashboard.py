import networkx as nx

from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text

console = Console()


# --------------------------------------------------
# SAMPLE CLOUD TOPOLOGY
# Replace this function's graph with your AWS graph.
# --------------------------------------------------

def create_sample_graph():

    graph = nx.DiGraph()

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

    graph.add_edges_from([
        ("internet", "vpc-001"),
        ("vpc-001", "sg-web"),
        ("sg-web", "ec2-web"),
        ("ec2-web", "db-001")
    ])

    return graph

# --------------------------------------------------
# BUILD RICH TREE FROM NETWORKX GRAPH
# --------------------------------------------------

def build_topology_tree(graph):

    root = Tree(
        "[bold cyan]AWS Cloud Topology[/bold cyan]"
    )

    visited = set()

    # Start from nodes that have no incoming edges.
    roots = [
        node for node in graph.nodes
        if graph.in_degree(node) == 0
    ]

    # Handle graphs without a root.
    if not roots and graph.number_of_nodes() > 0:
        roots = [next(iter(graph.nodes))]

    def add_branch(parent, node):

        attrs = graph.nodes[node]
        name = attrs.get("name", str(node))
        resource_type = attrs.get("type", "resource")

        if attrs.get("type") == "internet":
            label = f"[red]🌐 {name}[/red]"
        elif attrs.get("type") == "database":
            label = f"[green]🗄 {name}[/green]"
        elif attrs.get("type") == "security_group":
            label = f"[yellow]🔐 {name}[/yellow]"
        else:
            label = f"[cyan]☁ {name}[/cyan]"

        branch = parent.add(label)

        # Avoid infinite recursion if the graph has cycles.
        if node in visited:
            branch.add("[dim]Already displayed[/dim]")
            return

        visited.add(node)

        for neighbor in graph.successors(node):
            add_branch(branch, neighbor)

    for node in roots:
        add_branch(root, node)

    # Include any disconnected components.
    for node in graph.nodes:
        if node not in visited:
            add_branch(root, node)

    return root


# --------------------------------------------------
# DISPLAY CLOUD TOPOLOGY
# --------------------------------------------------

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


# --------------------------------------------------
# DETECT INTERNET-TO-PRIVATE-DATABASE PATHS
# --------------------------------------------------

def detect_drift(graph):

    internet_nodes = [
        node for node, attrs in graph.nodes(data=True)
        if (
            attrs.get("type") == "internet"
            or attrs.get("cidr") == "0.0.0.0/0"
            or attrs.get("name") == "Internet (0.0.0.0/0)"
        )
    ]

    database_nodes = [
        node for node, attrs in graph.nodes(data=True)
        if (
            attrs.get("type") == "database"
            and attrs.get("private", False)
        )
    ]

    table = Table(title="Drift Detection Results")
    table.add_column("Internet Source", style="cyan")
    table.add_column("Private Database", style="green")
    table.add_column("Result", style="bold")

    found = False

    for source in internet_nodes:
        for database in database_nodes:

            if nx.has_path(graph, source, database):

                found = True

                path = nx.shortest_path(
                    graph, source, database
                )

                table.add_row(
                    str(source),
                    str(database),
                    "[bold red]PATH EXISTS[/bold red]"
                )

                console.print(
                    "[yellow]Potential exposure path:[/yellow]"
                )

                for index, node in enumerate(path):
                    console.print(
                        f" {index + 1}. "
                        f"{graph.nodes[node].get('name', node)}"
                    )

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


# --------------------------------------------------
# SHOW RESOURCE INVENTORY
# --------------------------------------------------

def show_resources(graph):

    table = Table(title="Cloud Resource Inventory")

    table.add_column("Resource ID", style="cyan")
    table.add_column("Resource Name")
    table.add_column("Type", style="yellow")

    for node, attrs in graph.nodes(data=True):
        table.add_row(
            str(node),
            str(attrs.get("name", node)),
            str(attrs.get("type", "resource"))
        )

    console.print(table)


# --------------------------------------------------
# INTERACTIVE CLI MENU
# --------------------------------------------------

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


