from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
from table.stream_table import StreamTable
import copy
import threading


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str]):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable()
        self.stream_table = StreamTable()
        self.neighbours = neighbours
        self.num_neighbours = len(neighbours) if neighbours is not None else 0
        self.neighbours_lock = threading.Lock()
        self.port = port

    # NEIGHBOURS

    def get_listening_neighbours(self):
        with self.neighbours_lock:
            listening_neighbours = []
            for neighbour, state in self.neighbours.items():
                if state:
                    listening_neighbours.append(neighbour)

            return listening_neighbours

    def get_neighbours(self):
        return list(self.neighbours.keys())

    def get_num_neighbours(self):
        return self.num_neighbours

    def set_state_of_neighbour(self, neighbour, state):
        with self.neighbours_lock:
            self.neighbours[neighbour] = state

    def get_state_of_neighbour(self, neighbour):
        with self.neighbours_lock:
            return self.neighbours[neighbour]

    # BOOTSTRAPPER

    def get_node_info(self, ip):
        return self.bootstrapper.get_node_info(ip)

    # TABLE

    def add_entry(self, leaf, neighbour, next_hop):  # For join
        return self.table.add_entry(leaf, neighbour, next_hop)
    
    def remove_client_from_forwarding_table(self, leaf):
        self.table.remove_client(leaf)

    def get_best_entries(self):
        return self.table.get_best_entries()

    def get_best_entry_rp(self):
        return self.table.get_best_entry_rp()

    def get_neighbour_to_rp(self):
        return self.table.get_neighbour_to_rp()

    def update_metrics_rp(self, leaf, neighbour, next_hop, delay, loss):
        self.table.update_metrics_rp(leaf, neighbour, next_hop, delay, loss)

    def update_metrics(self, leaf, neighbour, next_hop, delay, loss):
        self.table.update_metrics(leaf, neighbour, next_hop, delay, loss)

    def get_table(self):
        return self.table.get_table()

    def get_table_rp(self):
        return self.table.get_table_rp()

    def get_neighbour_to_client(self, client):
        return self.table.get_neighbour_to_client(client)

    # STREAM TABLE

    def add_client_to_stream(self, stream_id, node_id):
        self.stream_table.add_client_to_stream(stream_id, node_id)
        
    def remove_client_from_stream(self, node_id):
        self.stream_table.remove_client_from_stream(node_id)

    def add_server_to_stream(self, stream_id, server_ip):
        self.stream_table.add_server_to_stream(stream_id, server_ip)

    def get_servers(self):
        return self.stream_table.get_servers()

    def its_best_server(self, stream_id, server_ip):
        return self.stream_table.its_best_server(stream_id, server_ip)

    def get_stream_clients(self, stream_id):
        return self.stream_table.get_stream_clients(stream_id)

    def get_stream_table_info(self):
        return self.stream_table.get_clients()

    def update_metrics_server(self, server, delay, loss):
        self.stream_table.update_metrics_server(server, delay, loss)

    def get_stream_table(self):
        return self.stream_table.get_stream_table()
