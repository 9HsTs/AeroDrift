#AERODRIFT - COMPLETE MAIN WORKFLOW

#asyncio used to write concurrent code using the  async and await syntax used for asynchronpus prgm 
import asyncio

#import mock AWS data
from mock_aws import get_aws_state, MockEC2Client

#import graph
from networkX_graph import build_aws_graph

#import drift detection
from graph_drift_detection import (
    detect_internet_to_private_db_drift
)

#import CLI interface
from cli_dashboard import (
    console,
    show_topology,
    detect_drift,
    show_resources
)

#import sandbox
from execution_sandbox_mock import execute_sandbox

#import remediation code
from agentic_remediation import generate_remediation

#import state of graph
from state_persistence import (
    initialize_database,
    save_graph,
    list_snapshots,
    diff_graphs
)

#generate pdf
from incident_report import generate_incident_report

#CONVERT AWS DATA TO GRAPH FOUNDATION FORMAT

def convert_aws_data(aws_data):

    graph_data = {
        "vpcs": [],
        "subnets": [],
        "instances": [],
        "security_groups": []
    }

    vpc_ids = set()

    # VPCs
    for subnet in aws_data.get("subnets", []):

        vpc_id = subnet.get("vpc_id")

        if vpc_id and vpc_id not in vpc_ids:

            graph_data["vpcs"].append({
                "VpcId": vpc_id
            })

            vpc_ids.add(vpc_id)

    # Subnets
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

    # Security groups
    for sg in aws_data.get("security_groups", []):

        graph_data["security_groups"].append({
            "GroupId": sg.get("group_id"),
            "GroupName": sg.get("group_name")
        })

    return graph_data

#BUILD COMPLETE NETWORKX GRAPH

def build_complete_graph(aws_data):

    graph_data = convert_aws_data(aws_data)

    graph = build_aws_graph(graph_data)

    return graph

#ADD INTERNET ACCESS RELATIONSHIPS

def add_drift_nodes(graph, aws_data):

    internet_node = "0.0.0.0/0"

    graph.add_node(
        internet_node,
        type="internet",
        name="Internet (0.0.0.0/0)"
    )

    for sg in aws_data.get("security_groups", []):

        sg_id = sg.get("group_id")

        for rule in sg.get("ingress_rules", []):

            for ip_range in rule.get("IpRanges", []):

                cidr = ip_range.get("CidrIp")

                if cidr == "0.0.0.0/0" and sg_id in graph:

                    graph.add_edge(
                        internet_node,
                        sg_id,
                        relationship="allows",
                        port=rule.get("FromPort"),
                        protocol=rule.get("IpProtocol")
                    )

    return graph

#FIND EXPOSED SSH RULE

def find_exposed_ssh_drift(aws_data):

    for sg in aws_data.get("security_groups", []):

        for rule in sg.get("ingress_rules", []):

            protocol = str(rule.get("IpProtocol", "tcp"))

            for ip_range in rule.get("IpRanges", []):

                cidr = ip_range.get("CidrIp")
                port = rule.get("FromPort")
                end_port = rule.get("ToPort", port)

                if (
                    cidr == "0.0.0.0/0"
                    and port is not None
                    and end_port is not None
                    and port <= 22 <= end_port
                    and protocol in ("tcp", "6")
                ):

                    return {
                        "drift_type": "open_sg_port",
                        "security_group_id": sg.get("group_id"),
                        "port": 22,
                        "protocol": "tcp",
                        "cidr": cidr,
                        "description": (
                            "SSH port 22 is exposed to the internet."
                        )
                    }

    return None

#GENERATE PDF INCIDENT REPORT

def create_incident_pdf(
    drift,
    remediation_code="Not generated",
    execution_status=None,
    execution_message="Remediation not executed"
):

    report_path = generate_incident_report(
        drift=drift,
        remediation_code=remediation_code,
        execution_status=execution_status,
        execution_message=execution_message
    )

    console.print(
        "\n[bold green]PDF incident report generated![/bold green]"
    )

    console.print(
        f"[cyan]Report location: {report_path}[/cyan]"
    )

    return report_path

#REMEDIATION + SANDBOX + AUTOMATIC PDF

def run_remediation_sandbox(aws_data):

    console.print(
        "\n[bold yellow]Preparing remediation...[/bold yellow]"
    )

    detected_drift = find_exposed_ssh_drift(aws_data)

    if not detected_drift:

        console.print(
            "[green]No exposed SSH port 22 rule found.[/green]"
        )
        return

    console.print(
        f"[bold red]Detected drift: {detected_drift}[/bold red]"
    )

    generated_code = None

    try:

        # Generate remediation code.
        generated_code = generate_remediation(detected_drift)

        console.print(
            "\n[bold cyan]Generated remediation code:[/bold cyan]"
        )

        console.print(generated_code)

    except Exception as exc:

        console.print(
            f"[bold red]Remediation generation failed: {exc}[/bold red]"
        )

        create_incident_pdf(
            drift=detected_drift,
            remediation_code="Generation failed",
            execution_status=False,
            execution_message=str(exc)
        )

        return

    # Ask permission before executing the sandbox.
    approval = input(
        "\nExecute remediation on mock AWS? (yes/no): "
    ).strip().lower()

    if approval != "yes":

        console.print("[yellow]Remediation cancelled.[/yellow]")

        create_incident_pdf(
            drift=detected_drift,
            remediation_code=generated_code,
            execution_status=None,
            execution_message="Cancelled by user; not executed."
        )

        return

    mock_ec2 = MockEC2Client()

    try:

        result = execute_sandbox(
            generated_code,
            mock_ec2
        )

        console.print(
            f"\n[bold cyan]Sandbox result:[/bold cyan] {result}"
        )

        # A non-boolean result is not automatically treated
        # as proof of successful remediation.
        if isinstance(result, bool):
            execution_status = result
        else:
            execution_status = None

        create_incident_pdf(
            drift=detected_drift,
            remediation_code=generated_code,
            execution_status=execution_status,
            execution_message=str(result)
        )

    except Exception as exc:

        console.print(
            f"[bold red]Sandbox execution failed: {exc}[/bold red]"
        )

        create_incident_pdf(
            drift=detected_drift,
            remediation_code=generated_code,
            execution_status=False,
            execution_message=str(exc)
        )

#REPORT ONLY - DOES NOT EXECUTE REMEDIATION

def generate_report_only(aws_data):

    drift = find_exposed_ssh_drift(aws_data)

    if drift:

        create_incident_pdf(
            drift=drift,
            remediation_code="Not executed in report-only mode",
            execution_status=None,
            execution_message=(
                "Drift detected. This option only generates a report; "
                "no remediation was executed."
            )
        )

    else:

        no_drift = {
            "drift_type": "no_exposed_ssh_rule_detected",
            "resource_id": "N/A",
            "port": "N/A",
            "protocol": "N/A",
            "cidr": "N/A",
            "description": (
                "No internet-exposed SSH port 22 rule was found "
                "by the current detector."
            )
        }

        create_incident_pdf(
            drift=no_drift,
            remediation_code="Not required by this detection result",
            execution_status=None,
            execution_message=(
                "Report-only mode. No remediation was executed."
            )
        )

#VIEW HISTORICAL GRAPH SNAPSHOTS

def view_state_history():

    console.print(
        "\n[bold cyan]Historical Graph Snapshots[/bold cyan]"
    )

    snapshots = list_snapshots()

    if not snapshots:

        console.print(
            "[yellow]No snapshots available.[/yellow]"
        )
        return

    table = __import__("rich.table", fromlist=["Table"]).Table(
        title="Saved Graph Snapshots"
    )

    table.add_column("Snapshot ID", style="cyan")
    table.add_column("Details")

    for snapshot in snapshots:
        table.add_row(str(snapshot[0]), str(snapshot[1:]))

    console.print(table)

#COMPARE HISTORICAL GRAPH STATES

def compare_historical_states():

    console.print(
        "\n[bold cyan]Compare Historical Graph States[/bold cyan]"
    )

    snapshots = list_snapshots()

    if len(snapshots) < 2:

        console.print(
            "[yellow]At least two snapshots are required.[/yellow]"
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
                "[red]Invalid snapshot ID.[/red]"
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

        console.print(str(diff_report))

    except ValueError:

        console.print(
            "[red]Please enter valid numeric snapshot IDs.[/red]"
        )

    except Exception as error:

        console.print(
            f"[red]Could not compare snapshots: {error}[/red]"
        )

#MAIN AERODRIFT WORKFLOW

async def main():

    console.print(
        "\n[bold cyan]Starting AeroDrift...[/bold cyan]\n"
    )

    # 1. Initialize SQLite.
    initialize_database()

    console.print(
        "[green]State Persistence database initialized.[/green]"
    )

    # 2. Collect mock AWS state.
    console.print(
        "[yellow]1. Collecting AWS infrastructure state...[/yellow]"
    )

    aws_data = await get_aws_state()

    console.print(
        "[green]AWS state collected.[/green]\n"
    )

    # 3. Build the NetworkX graph.
    console.print(
        "[yellow]2. Building NetworkX cloud graph...[/yellow]"
    )

    graph = build_complete_graph(aws_data)

    console.print(
        "[green]NetworkX graph created.[/green]\n"
    )

    # 4. Add internet relationships.
    console.print(
        "[yellow]3. Adding network access relationships...[/yellow]"
    )

    graph = add_drift_nodes(graph, aws_data)

    console.print(
        "[green]Network relationships added.[/green]\n"
    )

    # 5. Save a graph snapshot.
    console.print(
        "[yellow]4. Saving graph state to SQLite...[/yellow]"
    )

    snapshot_id = save_graph(graph)

    console.print(
        f"[bold green]Graph snapshot saved. "
        f"Snapshot ID: {snapshot_id}[/bold green]\n"
    )

    # 6. Detect topology drift.
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
            "[green]No Internet → Private Database path detected.[/green]"
        )

    # 7. Interactive CLI.
    while True:

        console.print(
            "\n[bold cyan]AeroDrift CLI Menu[/bold cyan]\n"
        )

        console.print("1. View Cloud Topology")
        console.print("2. Detect Drift and Run Remediation")
        console.print("3. List Cloud Resources")
        console.print("4. View Historical Graph Snapshots")
        console.print("5. Compare Two Historical Snapshots")
        console.print("6. Generate PDF Incident Report")
        console.print("7. Exit")

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

            try:
                generate_report_only(aws_data)

            except Exception as exc:
                console.print(
                    f"[bold red]PDF generation failed: {exc}[/bold red]"
                )

        elif choice == "7":

            console.print(
                "[bold cyan]AeroDrift stopped. Goodbye![/bold cyan]"
            )
            break

        else:

            console.print(
                "[red]Invalid choice. Please select 1-7.[/red]"
            )


if __name__ == "__main__":
    asyncio.run(main())
