from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
import copy
import threading


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str], node_id: int):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable()
        self.neighbours = copy.deepcopy(neighbours)
        self.neighbours_lock = threading.Lock()
        self.port = port
        self.node_id = node_id

    def get_listening_neighbours(self):
        with self.neighbours_lock:
            listening_neighbours = []
            for neighbour, state in self.neighbours.items():
                if state:
                    listening_neighbours.append(neighbour)

            return listening_neighbours

    def get_neighbours(self):
        with self.neighbours_lock:
            return copy.copy(self.neighbours.keys())

    def set_state_of_neighbour(self, neighbour, state):
        with self.neighbours_lock:
            self.neighbours[neighbour] = state

    def get_state_of_neighbour(self, neighbour):
        with self.neighbours_lock:
            return self.neighbours[neighbour]

    def get_parents(self):
        return self.table.get_parents()

    def get_neighbours_to_request(self):  # For measure
        return self.table.get_neighbours_to_request()

    def add_parent(self, parent):  # For tree update
        self.table.add_parent(parent)

    def get_neighbour_to_request(self, leaf):  # For tree update, to send to the next child in the tree
        return self.table.get_neighbour_to_request(leaf)

    def update_tree_entry(self, leaf, next_hop):
        return self.table.update_tree_entry(leaf, next_hop)

    def add_entry(self, leaf, neighbour, next_hop):  # For join
        return self.table.add_entry(leaf, neighbour, next_hop)

    def handle_join_request(self, ip):
        return self.bootstrapper.handle_join_request(ip)

    def get_best_entries(self):
        return self.table.get_best_entries()

    def get_neighbour_to_rp(self):
        return self.table.get_neighbour_to_rp()

    def update_metrics(self, leaf, neighbour, next_hop, delay, loss):
        self.table.update_metrics(leaf, neighbour, next_hop, delay, loss)
