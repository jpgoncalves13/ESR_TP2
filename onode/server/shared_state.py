from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
import copy


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str]):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.table = ForwardingTable()
        self.neighbours = copy.deepcopy(neighbours)
        self.port = port

    def get_neighbours(self):
        return self.neighbours

