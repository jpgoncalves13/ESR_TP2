from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable


class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, node: bool, table: ForwardingTable):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.node = node
        self.table = table
