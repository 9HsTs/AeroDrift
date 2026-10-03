#detect whether a network path now exists from 0.0.0.0/0(internet) --> private database
#if such a path appears, AeroDrift can flag it as network security drift

import networkx as nx

graph = nx.DiGraph()

graph.add_node()