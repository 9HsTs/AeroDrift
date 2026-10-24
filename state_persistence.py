#ssqlite3 -> used to integrate the SQLite dtabase with python
#JSON -> for storing and exchanging data. translate between JSON data formats and native python data types

import sqlite3
import json
import asyncio
from datetime import datetime, timezone
import networkx as nx

# Import mock AWS data and graph builder
from mock_aws import get_aws_state
from networkX_graph import build_aws_graph

#AERODRIFT STATE PERSISTENCE

#database name
DB_NAME = "aerodrift_history.db"


def get_connection():
    
    #Create a connection to the local SQLite database.
    return sqlite3.connect(DB_NAME)


def initialize_database():
    #Create database tables if they do not already exist.

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                snapshot_id INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                attributes TEXT NOT NULL,
                PRIMARY KEY (snapshot_id, node_id),
                FOREIGN KEY (snapshot_id)
                    REFERENCES snapshots(snapshot_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                snapshot_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                attributes TEXT NOT NULL,
                PRIMARY KEY (snapshot_id, source, target),
                FOREIGN KEY (snapshot_id)
                    REFERENCES snapshots(snapshot_id)
            )
        """)

    print("AeroDrift database initialized.")

#CONVERT MOCK AWS DATA TO GRAPH FORMAT
def convert_aws_data(aws_data):
    
    #Convert mock AWS data into the graph builder's format.

    graph_data = {
        "vpcs": [],
        "subnets": [],
        "instances": [],
        "security_groups": []
    }

    vpc_ids = set()

    # Collect VPCs and subnets
    for subnet in aws_data.get("subnets", []):

        vpc_id = subnet.get("vpc_id")

        if vpc_id and vpc_id not in vpc_ids:

            graph_data["vpcs"].append({
                "VpcId": vpc_id
            })

            vpc_ids.add(vpc_id)

        graph_data["subnets"].append({
            "SubnetId": subnet.get("subnet_id"),
            "VpcId": vpc_id
        })

    # Collect EC2 instances
    for instance in aws_data.get("ec2", []):

        security_groups = [
            {"GroupId": sg_id}
            for sg_id in instance.get("security_groups", [])
        ]

        graph_data["instances"].append({
            "InstanceId": instance.get("instance_id"),
            "SubnetId": instance.get("subnet_id"),
            "SecurityGroups": security_groups
        })

    # Collect security groups
    for sg in aws_data.get("security_groups", []):

        graph_data["security_groups"].append({
            "GroupId": sg.get("group_id"),
            "GroupName": sg.get("group_name")
        })

    return graph_data

#SAVE GRAPH HISTORY
def save_graph(graph):
    #Save a NetworkX graph as a timestamped snapshot.

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:

        cursor = conn.execute(
            "INSERT INTO snapshots (timestamp) VALUES (?)",
            (timestamp,)
        )

        snapshot_id = cursor.lastrowid

        # Save nodes and their attributes
        for node_id, attributes in graph.nodes(data=True):

            conn.execute("""
                INSERT INTO nodes
                (snapshot_id, node_id, attributes)
                VALUES (?, ?, ?)
            """, (
                snapshot_id,
                str(node_id),
                json.dumps(dict(attributes), sort_keys=True)
            ))

        # Save graph relationships
        for source, target, attributes in graph.edges(data=True):

            conn.execute("""
                INSERT INTO edges
                (snapshot_id, source, target, attributes)
                VALUES (?, ?, ?, ?)
            """, (
                snapshot_id,
                str(source),
                str(target),
                json.dumps(dict(attributes), sort_keys=True)
            ))

    print(f"Graph snapshot saved. ID: {snapshot_id}")
    print(f"Timestamp: {timestamp}")

    return snapshot_id

#COLLECT MOCK AWS STATE AND SAVE SNAPSHOT

async def save_mock_aws_snapshot():
    
    #Collect mock AWS data, build the graph,and save it to the SQLite database.
    

    initialize_database()

    print("\nCollecting mock AWS infrastructure state...")

    aws_data = await get_aws_state()

    print("Mock AWS data collected.")

    # Convert the AWS data
    graph_data = convert_aws_data(aws_data)

    # Build the NetworkX graph
    graph = build_aws_graph(graph_data)

    # Save the historical snapshot
    snapshot_id = save_graph(graph)

    print(f"Mock AWS snapshot completed: {snapshot_id}")

    return snapshot_id

#VIEW AVAILABLE SNAPSHOTS

def list_snapshots():
    #Display all saved graph snapshots.

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT snapshot_id, timestamp
            FROM snapshots
            ORDER BY snapshot_id
        """).fetchall()

    if not rows:
        print("No historical snapshots found.")
        return []

    for snapshot_id, timestamp in rows:
        print(f"ID: {snapshot_id} | Timestamp: {timestamp}")

    return rows


#LOAD A SAVED GRAPH

def load_graph(snapshot_id):
    """Reconstruct a saved graph from SQLite."""

    graph = nx.DiGraph()

    with get_connection() as conn:

        snapshot = conn.execute("""
            SELECT snapshot_id
            FROM snapshots
            WHERE snapshot_id = ?
        """, (snapshot_id,)).fetchone()

        if snapshot is None:
            raise ValueError(
                f"Snapshot {snapshot_id} does not exist."
            )

        nodes = conn.execute("""
            SELECT node_id, attributes
            FROM nodes
            WHERE snapshot_id = ?
        """, (snapshot_id,)).fetchall()

        edges = conn.execute("""
            SELECT source, target, attributes
            FROM edges
            WHERE snapshot_id = ?
        """, (snapshot_id,)).fetchall()

    for node_id, attributes in nodes:
        graph.add_node(node_id, **json.loads(attributes))

    for source, target, attributes in edges:
        graph.add_edge(
            source,
            target,
            **json.loads(attributes)
        )

    return graph



#COMPARE TWO HISTORICAL SNAPSHOTS

def diff_graphs(old_snapshot_id, new_snapshot_id):
    """Identify added, removed, and modified graph elements."""

    old_graph = load_graph(old_snapshot_id)
    new_graph = load_graph(new_snapshot_id)

    old_nodes = set(old_graph.nodes)
    new_nodes = set(new_graph.nodes)

    added_nodes = sorted(new_nodes - old_nodes)
    removed_nodes = sorted(old_nodes - new_nodes)

    # Detect modified resource properties
    modified_nodes = {}

    for node_id in sorted(old_nodes & new_nodes):

        old_attributes = dict(old_graph.nodes[node_id])
        new_attributes = dict(new_graph.nodes[node_id])

        if old_attributes != new_attributes:

            modified_nodes[node_id] = {
                "before": old_attributes,
                "after": new_attributes
            }

    # Compare relationships, including their attributes
    def edge_set(graph):
        return {
            (
                source,
                target,
                json.dumps(dict(attributes), sort_keys=True)
            )
            for source, target, attributes
            in graph.edges(data=True)
        }

    old_edges = edge_set(old_graph)
    new_edges = edge_set(new_graph)

    added_edges = sorted(new_edges - old_edges)
    removed_edges = sorted(old_edges - new_edges)

    report = {
        "old_snapshot_id": old_snapshot_id,
        "new_snapshot_id": new_snapshot_id,
        "added_resources": added_nodes,
        "removed_resources": removed_nodes,
        "modified_resources": modified_nodes,
        "added_relationships": [
            {
                "source": source,
                "target": target,
                "attributes": json.loads(attributes)
            }
            for source, target, attributes in added_edges
        ],
        "removed_relationships": [
            {
                "source": source,
                "target": target,
                "attributes": json.loads(attributes)
            }
            for source, target, attributes in removed_edges
        ]
    }

    print("\n========== AERODRIFT TOPOLOGY DIFF ==========")
    print(json.dumps(report, indent=4))

    return report


#STANDALONE TEST

if __name__ == "__main__":

    asyncio.run(save_mock_aws_snapshot())

    print("\nSaved graph history:")

    list_snapshots()