from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
from table.stream_table import StreamTable
import copy
import threading


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str], node_id: int):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable()
        self.stream_table = StreamTable()
        self.neighbours = neighbours
        self.num_neighbours = len(neighbours) if neighbours is not None else 0
        self.neighbours_lock = threading.Lock()
        self.port = port
        self.node_id = node_id
        self.clients_info = {}  # Node_id -> [Clients]  Stream_id : ([SERVERS], [NODE_IDS])
        self.clients_lock = threading.Lock()

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

    def get_best_entries(self):
        return self.table.get_best_entries()

    def get_neighbour_to_rp(self):
        return self.table.get_neighbour_to_rp()

    def update_metrics(self, leaf, neighbour, next_hop, delay, loss):
        self.table.update_metrics(leaf, neighbour, next_hop, delay, loss)

    def get_table(self):
        return self.table.get_table()

    # CLIENTS

    def add_client(self, node_id, client):
        with self.clients_lock:
            if node_id not in self.clients_info:
                self.clients_info[node_id] = []
            if client not in self.clients_info[node_id]:
                self.clients_info[node_id].append(client)
                return False
            return True

    def im_requesting(self):
        with self.clients_lock:
            if self.node_id in self.clients_info:
                return True
            return False

