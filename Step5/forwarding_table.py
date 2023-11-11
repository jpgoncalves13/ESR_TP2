from table_entry import TableEntry
import threading

class ForwardingTable:
    """
    This class is used to store the forwarding table of the Node.
    For each destination node reachable from the tree, we store the next hops
    The list of next hops may be variable 
    """
    def __init__(self):
        self.table = {}
        self.parents = [] # We may also store the parents of this node in the tree
        self.lock = threading.Lock()
    
    def add_entry(self, destination, next_hops, delay, loss):
        with self.lock:
            entry = TableEntry(next_hops, delay, loss)
            self.table[destination] = entry

    def remove_entry(self, destination):
        with self.lock:
            del self.table[destination]

    def consult_entry(self, destination):
        return self.table[destination]
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        str = "------- Table: -------\n"

        for entry in self.table:
            str += entry + "->>>>>>>>>>>>>\n" + self.table[entry].__str__() + "\n"

        return str