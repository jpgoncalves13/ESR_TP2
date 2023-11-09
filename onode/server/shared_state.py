from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str]):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable()
        self.neighbours = neighbours
        self.port = port
        if neighbours is not None:
            for neighbour in neighbours:
                self.table.add_entry(neighbour)

    def get_neighbours(self):
        return self.neighbours
