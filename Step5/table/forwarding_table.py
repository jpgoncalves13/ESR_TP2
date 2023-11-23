from table.table_entry import TableEntry
import threading
import json


class ForwardingTable:
    """
    This class is used to store the forwarding table of the Node.
    For each destination node reachable from the tree, we store the next hops
    The list of next hops may be variable 
    """
    def __init__(self, filename=None):
        if filename is not None:
            self.table = read_forwarding_table(filename)
            self.parents = []  # We may also store the parents of this node in the tree
            self.lock = threading.Lock()
        else:
            self.table = {}
            self.parents = []  # We may also store the parents of this node in the tree
            self.lock = threading.Lock()

    def add_entry(self, destination):
        with self.lock:
            entry = TableEntry()
            self.table[destination] = entry

    def remove_entry(self, destination):
        with self.lock:
            del self.table[destination]

    def consult_entry(self, destination):
        return self.table[destination]

    def update_packets_sent(self, destination):
        self.table[destination].update_packets_sent()

    def update_delay(self, destination, delay):
        self.table[destination].update_delay(delay)

    def update_packets_received(self, destination):
        self.table[destination].update_packets_received()

    def __str__(self) -> str:
        return repr(self)
    
    def __repr__(self) -> str:
        st = "------- Table: -------\n"

        for entry in self.table:
            st += entry + "->>>>>>>>>>>>>\n" + str(self.table[entry]) + "\n"

        return st
    

def read_forwarding_table(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    print(data)
    return data
