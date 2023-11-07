from table.table_entry import TableEntry


class ForwardingTable:
    """
    This class is used to store the forwarding table of the Node.
    For each destination node reachable from the tree, we store the next hops
    The list of next hops may be variable 
    """
    def __init__(self):
        self.table = {}
        self.parents = []  # We may also store the parents of this node in the tree

    def add_entry(self, destination, next_hops, delay, loss):
        entry = TableEntry(next_hops, delay, loss)
        self.table[destination] = entry

    def remove_entry(self, destination):
        del self.table[destination]

    def consult_entry(self, destination):
        return self.table[destination]
    
    def __str__(self) -> str:
        return repr(self)
    
    def __repr__(self) -> str:
        st = "------- Table: -------\n"

        for entry in self.table:
            st += entry + "->>>>>>>>>>>>>\n" + str(self.table[entry]) + "\n"

        return st
