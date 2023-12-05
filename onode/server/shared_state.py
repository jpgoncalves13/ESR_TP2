from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
from table.stream_table import StreamTable
import copy
import threading
import queue


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str], tag, stream_id):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable()
        self.stream_table = StreamTable()
        self.neighbours = neighbours
        self.num_neighbours = len(neighbours) if neighbours is not None else 0
        self.neighbours_lock = threading.Lock()
        self.port = port
        self.tag = tag
        self.client = stream_id  # When the client is together with the node
        self.client_lock = threading.Lock()
        self.client_on = False
        self.buffer = queue.Queue(maxsize=10) if self.client > 0 else None

    def add_packet_to_buffer(self, rtp_packet):
        if self.client > 0:
            self.buffer.put(rtp_packet)

    def get_packet_from_buffer(self):
        data = self.buffer.get()
        self.buffer.task_done()
        return data

    # TODO
    def update_client_state(self, state):
        with self.client_lock:
            self.client_on = state

    # TODO
    def get_client_state(self):
        with self.client_lock:
            return self.client_on

    """
    def get_listening_neighbours(self):
        with self.neighbours_lock:
            listening_neighbours = []
            for neighbour, state in self.neighbours.items():
                if state:
                    listening_neighbours.append(neighbour)

            return listening_neighbours
    """
    """
    Get all the neighbours
    """
    def get_neighbours(self):
        return list(self.neighbours.keys())

    """
    Get the number of neighbours
    """
    def get_num_neighbours(self):
        return self.num_neighbours

    """
    def set_state_of_neighbour(self, neighbour, state):
        with self.neighbours_lock:
            self.neighbours[neighbour] = state
    """
    """
    def get_state_of_neighbour(self, neighbour):
        with self.neighbours_lock:
            return self.neighbours[neighbour]
    """

    # BOOTSTRAPPER
    """
    Get the info of a node, based on its ip (bootstrapper)
    """
    def get_node_info(self, ip):
        return self.bootstrapper.get_node_info(ip)

    # TABLE
    """def add_entry(self, leaf, neighbour, next_hop):  # For join
        return self.table.add_entry(leaf, neighbour, next_hop)"""
    
    """def remove_client_from_forwarding_table(self, leaf):
        self.table.remove_client(leaf)"""

    """def get_best_entries(self):
        return self.table.get_best_entries()"""

    """
    Get the best entry to the rp table
    """
    def get_best_entry_rp(self):
        return self.table.get_best_entry_rp()

    """
    Get the neighbour of the best entry to the rp table
    """
    def get_neighbour_to_rp(self):
        return self.table.get_neighbour_to_rp()

    """
    Update the metrics of an path entry to the rp
    Based on the the rp_ip and the neighbour, update the next_hop, the delay and the loss
    """
    def update_metrics_rp(self, leaf, neighbour, next_hop, delay, loss):
        self.table.update_metrics_rp(leaf, neighbour, next_hop, delay, loss)
        
    # TODO
    def update_neighbour_death(self, neighbour):
        return self.table.update_neighbour_death(neighbour)

    """def update_metrics(self, leaf, neighbour, next_hop, delay, loss):
        self.table.update_metrics(leaf, neighbour, next_hop, delay, loss)"""

    """def get_table(self):
        return self.table.get_table()"""

    """def get_tree(self):
        return self.table.get_tree()"""

    """def get_table_rp(self):
        return self.table.get_table_rp()"""

    """def get_neighbour_to_client(self, client):
        return self.table.get_neighbour_to_client(client)"""

    """def get_best_entry(self, client):
        return self.table.get_best_entry(client)"""

    # STREAM TABLE
    
    """
    Adds a neighbour to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_neighbour_to_stream(self, stream_id, node_id):
        self.stream_table.add_neighbour_to_stream(stream_id, node_id)
        
    """
    Removes a neighbour from a stream
    """    
    def remove_neighbour_from_stream(self, node_id):
        self.stream_table.remove_client_from_stream(node_id)
        
    """
    Check if a stream is already in the stream list
    """
    def check_if_stream_exists(self, stream_id):
        self.stream_table.check_if_stream_exists(stream_id)

    """
    Add a server to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_server_to_stream(self, stream_id, server_ip):
        self.stream_table.add_server_to_stream(stream_id, server_ip)

    """
    Get all the servers currently streaming
    """
    def get_servers(self):
        return self.stream_table.get_servers()

    # TODO
    def its_best_server(self, stream_id, server_ip):
        return self.stream_table.its_best_server(stream_id, server_ip)

    """
    Get the neighbours for a given stream
    """
    def get_stream_neighbours(self, stream_id):
        return self.stream_table.get_stream_neighbours(stream_id)

    """def get_stream_table_info(self):
        return self.stream_table.get_clients()"""

    """
    Update the metrics associated with a given server (server, delay, loss)
    """
    def update_metrics_server(self, server, delay, loss):
        self.stream_table.update_metrics_server(server, delay, loss)

    def get_stream_table(self):
        return self.stream_table.get_stream_table()

    """def remove_clients_neighbour_from_forwarding_table(self, leafs, neighbour):
        self.table.remove_clients_neighbour_from_forwarding_table(leafs, neighbour)"""
