#detect whether a network path now exists from 0.0.0.0/0(internet) --> private database
#if such a path appears, AeroDrift can flag it as network security drift

#netwprkX -> used to create and work with graphs
import networkx as nx

#create the directed graph
graph = nx.DiGraph()

#add the internet node
graph.add_node(
    "0.0.0.0/0",        #any ip address
    type="internet"     #node metadata
)

#add the internet gateway
graph.add_node(
    "igw-001",              #node id
    type="internet_gateway" #node metadata
)

#add public subnet
graph.add_node(
    "subnet-public",
    type="public_subnet"
)

#add EC2
graph.add_node(
    "ec2-001",
    type="ec2"
)

#add privet subnet
graph.add_node(
    "subnet-private",
    type="private_subnet"
)

#add database
graph.add_node(
    "db-001",
    type="database",
    private = True             #flag -> detection logic means databse is private
)

#network path
#internet -> IGW connection -> public subnet ->EC2 -> private subnet -> database
graph.add_edge("0.0.0.0/0", "igw-001")

graph.add_edge("igw-001","subnet-public")

graph.add_edge("subnet-public", "ec2-001")

graph.add_edge("ec2-001", "subnet-private")

graph.add_edge("subnet-private", "db-001")

#drift detection
#purpose find the internet can reach any private databse
#graph parameter --> pass networkX graph
def detect_internet_to_private_db_drift(graph):
    internet_node = "0.0.0.0/0"

    #find private database
    #find all nodes that are databases and are marked private...this works as a filter
    private_database = [
        node
        for node, data in graph.nodes(data=True)  #loops through all nodes along with metadata
        if data.get("type") == "database"           #check whether its a database
        and data.get("private") is True             #check data is private

        #if both conditions are true thrn node added in private databse


    ]

    #empty list for detected path
    drift_path = []

    #loop through private databse
    for database in private_database:
        if nx.has_path(graph, internet_node, database):         #check path exists core graph query

            #find the actual shortest path
            path = nx.shortest_path(
                graph,
                source=internet_node,
                target=database
            )

            #append the detected path
            drift_path.append(path)

    return drift_path

#run detection
#call the function
drift_path = detect_internet_to_private_db_drift(graph)

#result

#empty list --> false
#non empty list --> true

if drift_path:
    print("SECURITY DRIFT DETECTED")

    #loop through detected path
    for path in drift_path:
        print("Internet --> Private database path found : ")
        print(" --> ".join(path))
else:

    print("No Internet --> Private Database path detected.")