from bootstrapper import read_nodes as rd


class Bootstrapper:
    def __init__(self, nodes_file, debug=None):
        if debug is None:
            debug = False
        self.file = nodes_file
        self.nodes = rd.read_nodes_file(nodes_file)
        self.debug = debug

    def get_neighbors(self, node_ip):
        if node_ip in self.nodes["names"]:
            return self.nodes["nodes"][self.nodes["names"][node_ip]]
        return None

    def set_debug(self, debug):
        self.debug = debug
    
    def get_node_info(self, node_ip):
        if self.debug:
            print(f"DEBUG: Received a request to join the topology from node {node_ip}")
        neighbors = self.get_neighbors(node_ip)
        if self.debug:
            print(f"DEBUG: Sending neighbors {neighbors} to node {node_ip}")
        return neighbors
