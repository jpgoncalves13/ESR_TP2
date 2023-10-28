import read_nodes as rd


class Bootstrapper:
    def __init__(self, nodes_file):
        self.file = nodes_file
        self.nodes = rd.read_nodes_file(nodes_file)

    def get_neighbors(self, node_id):
        return self.nodes[node_id]


