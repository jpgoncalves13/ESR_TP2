import read_nodes as rd


class Bootstrapper:
    def __init__(self, nodes_file, debug=None):
        if debug is None:
            debug = False
        self.file = nodes_file
        self.nodes = rd.read_nodes_file(nodes_file)
        self.debug = debug

    def get_neighbors(self, node_id):
        return self.nodes["nodes"][self.nodes["names"][node_id]]

    def set_debug(self, debug):
        self.debug = debug
    
    def handle_join_request(self, node_id):
        if self.debug:
            print(f"DEBUG: Received a request to join the topology from node {node_id}")
        neighbors = self.get_neighbors(node_id)
        if self.debug:
            print(f"DEBUG: Sending neighbors {neighbors} to node {node_id}")
        return neighbors
