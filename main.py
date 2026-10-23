#asyncio -> py library for asynchoronous programming
import asyncio

#import functions from python codes
from mock_aws import get_aws_state          #mock data ingestion
from networkX_graph import build_aws_graph      #graph module
from graph_drift_detection import detect_internet_to_private_db_drift       #drift detection

#dashboard function defined in cli dashoard
from cli_dashboard import (
    console,
    show_topology,
    detect_drift,
    show_resources
)

import networkx as nx

#import execute rollback function from sandbox mock
from execution_sandbox_mock import execute_sandbox
from agentic_remediation import generate_remediation
from mock_aws import MockEC2Client

from state_persistence import (
    initialize_database,
    save_graph,
    list_snapshots,
    diff_graphs
)

# Convert AWS ingestion output to Graph Foundation format
#adapter function
def convert_aws_data(aws_data):

    #empty dictionary
    graph_data = {
        "vpcs": [],
        "subnets": [],
        "instances": [],
        "security_groups": []
    }

    #vpc empty set
    vpc_ids = set()

    for subnet in aws_data.get("subnets", []):

        vpc_id = subnet.get("vpc_id")

        if vpc_id and vpc_id not in vpc_ids:

            graph_data["vpcs"].append({
                "VpcId": vpc_id
            })

            vpc_ids.add(vpc_id)

    #subnets
    for subnet in aws_data.get("subnets", []):

        graph_data["subnets"].append({
            "SubnetId": subnet.get("subnet_id"),
            "VpcId": subnet.get("vpc_id")
        })
# EC2 instances
    for instance in aws_data.get("ec2", []):

        security_groups = []

        for sg_id in instance.get("security_groups", []):

            security_groups.append({
                "GroupId": sg_id
            })

        graph_data["instances"].append({
            "InstanceId": instance.get("instance_id"),
            "SubnetId": instance.get("subnet_id"),
            "SecurityGroups": security_groups
        })
    #security groups
    for sg in aws_data.get("security_groups", []):

        graph_data["security_groups"].append({
            "GroupId": sg.get("group_id"),
            "GroupName": sg.get("group_name")
        })

    return graph_data

# BUILD COMPLETE GRAPH
def build_complete_graph(aws_data):

    graph_data = convert_aws_data(aws_data)

    graph = build_aws_graph(graph_data)

    return graph

# ADD INTERNET / DATABASE INFORMATION
def add_drift_nodes(graph, aws_data):
    # INTERNET NODE
    graph.add_node(
        "0.0.0.0/0",
        type="internet",
        name="Internet (0.0.0.0/0)"
    )

    # CONNECT INTERNET TO SECURITY GROUPS
    # BASED ON INGRESS RULES
    for sg in aws_data.get("security_groups", []):

        sg_id = sg.get("group_id")

        for rule in sg.get("ingress_rules", []):

            for ip_range in rule.get("IpRanges", []):

                cidr = ip_range.get("CidrIp")

                if cidr == "0.0.0.0/0":

                    if sg_id in graph:

                        graph.add_edge(
                            "0.0.0.0/0",
                            sg_id,
                            relationship="allows"
                        )

    return graph

def run_remediation_sandbox(aws_data):

    console.print(
        "\n[bold yellow]Preparing remediation...[/bold yellow]"
    )

    mock_ec2 = MockEC2Client()

    # Find an exposed SSH rule in mock AWS data.
    detected_drift = None

    for sg in aws_data.get("security_groups", []):

        for rule in sg.get("ingress_rules", []):

            protocol = str(rule.get("IpProtocol", "tcp"))

            for ip_range in rule.get("IpRanges", []):

                cidr = ip_range.get("CidrIp")
                port = rule.get("FromPort")

                if cidr == "0.0.0.0/0" and port == 22:

                    detected_drift = {
                        "drift_type": "open_sg_port",
                        "security_group_id": sg.get("group_id"),
                        "port": 22,
                        "protocol": protocol,
                        "cidr": cidr
                    }
                    break

            if detected_drift:
                break

        if detected_drift:
            break

    if not detected_drift:
        console.print(
            "[green]No exposed SSH rule found for remediation.[/green]"
        )
        return

    console.print(
        f"[red]Exposed SSH rule detected: "
        f"{detected_drift}[/red]"
    )

    generated_code = generate_remediation(detected_drift)

    console.print("\n[bold cyan]Generated remediation code:[/bold cyan]")
    console.print(generated_code)

    approval = input(
        "\nExecute remediation on mock AWS? (yes/no): "
    ).strip().lower()

    if approval != "yes":
        console.print("[yellow]Remediation cancelled.[/yellow]")
        return

    result = execute_sandbox(
        generated_code,
        mock_ec2
        #approved=True
    )

    console.print(f"\n[bold green]{result}[/bold green]")

def view_state_history():
    console.print("\n[bold cyan]Historical Graph Snapshots[/bold cyan]")

    snapshots = list_snapshots()

    if not snapshots:
        console.print("[yellow]No Snapshots Available.[/yellow]")
        return
    
def compare_historical_states():

    console.print(
        "\n[bold cyan]Compare Historical Graph States[/bold cyan]"
    )

    snapshots = list_snapshots()

    if len(snapshots) < 2:

        console.print(
            "[yellow]At least two snapshots are required. "
            "Run AeroDrift again to save another snapshot.[/yellow]"
        )
        return

    try:

        old_id = int(input("Enter older snapshot ID: ").strip())
        new_id = int(input("Enter newer snapshot ID: ").strip())

        available_ids = {
            snapshot[0] for snapshot in snapshots
        }

        if old_id not in available_ids or new_id not in available_ids:

            console.print(
                "[red]Invalid snapshot ID. Select IDs from the list.[/red]"
            )
            return

        if old_id == new_id:

            console.print(
                "[yellow]Select two different snapshot IDs.[/yellow]"
            )
            return

        diff_report = diff_graphs(old_id, new_id)

        console.print(
            "\n[bold green]Topology comparison completed.[/bold green]"
        )

        return diff_report

    except ValueError:

        console.print(
            "[red]Please enter valid numeric snapshot IDs.[/red]"
        )

    except Exception as error:

        console.print(
            f"[red]Could not compare snapshots: {error}[/red]"
        )


#RUN COMPLETE AERODRIFT SYSTEM
        
async def main():

    console.print(
        "\n[bold cyan]Starting AeroDrift...[/bold cyan]\n"
    )

    # Initialize local SQLite database
    initialize_database()

    console.print(
        "[green]State Persistence database initialized.[/green]"
    )

    console.print(
        "[yellow]1. Collecting AWS infrastructure state...[/yellow]"
    )

    aws_data = await get_aws_state()

    console.print(
        "[green]AWS state collected.[/green]\n"
    )

    console.print(
        "[yellow]2. Building NetworkX cloud graph...[/yellow]"
    )

    graph = build_complete_graph(aws_data)

    console.print(
        "[green]NetworkX graph created.[/green]\n"
    )

    console.print(
        "[yellow]3. Adding network access relationships...[/yellow]"
    )

    graph = add_drift_nodes(graph, aws_data)

    console.print(
        "[green]Network relationships added.[/green]\n"
    )

    console.print(
        "[yellow]4. Saving graph state to SQLite...[/yellow]"
    )

    snapshot_id = save_graph(graph)

    console.print(
        f"[bold green]Graph snapshot saved successfully. "
        f"Snapshot ID: {snapshot_id}[/bold green]\n"
    )

    

    console.print(
        "[yellow]5. Running graph drift detection...[/yellow]"
    )

    drift_paths = detect_internet_to_private_db_drift(graph)

    if drift_paths:

        console.print(
            "\n[bold red]SECURITY DRIFT DETECTED![/bold red]\n"
        )

        for path in drift_paths:

            console.print(
                "[yellow]Internet → Private Database:[/yellow]"
            )

            console.print(" → ".join(path))

    else:

        console.print(
            "[green]No Internet → Private Database "
            "drift detected.[/green]\n"
        )

    console.print(
        "\n[bold cyan]AeroDrift Dashboard Ready[/bold cyan]\n"
    )

    #CLI MENU
    

    while True:

        console.print(
            "\n[bold cyan]AeroDrift CLI Menu[/bold cyan]\n"
        )

        console.print("[1] View Cloud Topology")
        console.print("[2] Detect Drift and Run Remediation")
        console.print("[3] List Cloud Resources")
        console.print("[4] View Historical Graph Snapshots")
        console.print("[5] Compare Two Historical Snapshots")
        console.print("[6] Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":

            show_topology(graph)

        elif choice == "2":

            detect_drift(graph)
            run_remediation_sandbox(aws_data)

        elif choice == "3":

            show_resources(graph)

        elif choice == "4":

            view_state_history()

        elif choice == "5":

            compare_historical_states()

        elif choice == "6":

            console.print(
                "[bold cyan]AeroDrift stopped. Goodbye![/bold cyan]"
            )

            break

        else:

            console.print(
                "[red]Invalid choice.[/red]"
            )


if __name__ == "__main__":

    asyncio.run(main())