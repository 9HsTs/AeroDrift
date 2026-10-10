import asyncio

from mock_aws import get_aws_state
from networkX_graph import build_aws_graph

from graph_drift_detection import detect_internet_to_private_db_drift

from cli_dashboard import (
    console,
    show_topology,
    detect_drift,
    show_resources
)

import networkx as nx


# ============================================================
# ADAPTER
# Convert AWS ingestion output to Graph Foundation format
# ============================================================

def convert_aws_data(aws_data):

    graph_data = {
        "vpcs": [],
        "subnets": [],
        "instances": [],
        "security_groups": []
    }

    # --------------------------------------------------------
    # VPC
    # --------------------------------------------------------

    vpc_ids = set()

    for subnet in aws_data.get("subnets", []):

        vpc_id = subnet.get("vpc_id")

        if vpc_id and vpc_id not in vpc_ids:

            graph_data["vpcs"].append({
                "VpcId": vpc_id
            })

            vpc_ids.add(vpc_id)

    # --------------------------------------------------------
    # SUBNETS
    # --------------------------------------------------------

    for subnet in aws_data.get("subnets", []):

        graph_data["subnets"].append({
            "SubnetId": subnet.get("subnet_id"),
            "VpcId": subnet.get("vpc_id")
        })

    # --------------------------------------------------------
    # EC2 INSTANCES
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SECURITY GROUPS
    # --------------------------------------------------------

    for sg in aws_data.get("security_groups", []):

        graph_data["security_groups"].append({
            "GroupId": sg.get("group_id"),
            "GroupName": sg.get("group_name")
        })

    return graph_data


# ============================================================
# BUILD COMPLETE GRAPH
# ============================================================

def build_complete_graph(aws_data):

    graph_data = convert_aws_data(aws_data)

    graph = build_aws_graph(graph_data)

    return graph


# ============================================================
# ADD INTERNET / DATABASE INFORMATION
# ============================================================

def add_drift_nodes(graph, aws_data):

    # --------------------------------------------------------
    # INTERNET NODE
    # --------------------------------------------------------

    graph.add_node(
        "0.0.0.0/0",
        type="internet",
        name="Internet (0.0.0.0/0)"
    )

    # --------------------------------------------------------
    # CONNECT INTERNET TO SECURITY GROUPS
    # BASED ON INGRESS RULES
    # --------------------------------------------------------

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


# ============================================================
# RUN COMPLETE AERODRIFT SYSTEM
# ============================================================

async def main():

    console.print(
        "\n[bold cyan]Starting AeroDrift...[/bold cyan]\n"
    )

    # --------------------------------------------------------
    # STEP 1: AWS INGESTION
    # --------------------------------------------------------

    console.print(
        "[yellow]1. Collecting AWS infrastructure state...[/yellow]"
    )

    aws_data = await get_aws_state()

    console.print(
        "[green]✓ AWS state collected[/green]\n"
    )

    # --------------------------------------------------------
    # STEP 2: GRAPH FOUNDATION
    # --------------------------------------------------------

    console.print(
        "[yellow]2. Building NetworkX cloud graph...[/yellow]"
    )

    graph = build_complete_graph(aws_data)

    console.print(
        "[green]✓ NetworkX graph created[/green]\n"
    )

    # --------------------------------------------------------
    # STEP 3: ADD NETWORK ACCESS INFORMATION
    # --------------------------------------------------------

    console.print(
        "[yellow]3. Adding network access relationships...[/yellow]"
    )

    graph = add_drift_nodes(
        graph,
        aws_data
    )

    console.print(
        "[green]✓ Network relationships added[/green]\n"
    )

    # --------------------------------------------------------
    # STEP 4: GRAPH DRIFT DETECTION
    # --------------------------------------------------------

    console.print(
        "[yellow]4. Running graph drift detection...[/yellow]"
    )

    drift_paths = detect_internet_to_private_db_drift(
        graph
    )

    if drift_paths:

        console.print(
            "\n[bold red]⚠ SECURITY DRIFT DETECTED![/bold red]\n"
        )

        for path in drift_paths:

            console.print(
                "[yellow]Internet → Private Database:[/yellow]"
            )

            console.print(
                " → ".join(path)
            )

    else:

        console.print(
            "[green]✓ No Internet → Private Database "
            "drift detected[/green]\n"
        )

    # --------------------------------------------------------
    # STEP 5: RICH DASHBOARD
    # --------------------------------------------------------

    console.print(
        "\n[bold cyan]AeroDrift Dashboard Ready[/bold cyan]\n"
    )

    while True:

        console.print(
            "\n[bold cyan]AeroDrift CLI Menu[/bold cyan]\n"
        )

        console.print("[1] View Cloud Topology")
        console.print("[2] Detect Drift")
        console.print("[3] List Cloud Resources")
        console.print("[4] Exit")

        choice = input("\nSelect an option: ")

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

        else:

            console.print(
                "[red]Invalid choice.[/red]"
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())