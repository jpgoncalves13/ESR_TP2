from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str]):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable(neighbours)
        self.neighbours = neighbours
        self.port = port

    def get_neighbours(self):
        return self.neighbours

    def get_entries(self):
        return self.table.get_entries()
