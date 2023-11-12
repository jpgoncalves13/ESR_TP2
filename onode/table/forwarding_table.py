from table.table_entry import TableEntry


class ForwardingTable:
    """
    This class is used to store the forwarding table of the Node.
    For each destination node reachable from the tree, we store the next hops
    The list of next hops may be variable 
    """
    def __init__(self):
        self.table = {}  # Leaf -> Neighbour -> Entry
        self.parents = []  # We may also store the parents of this node in the tree

    # To get the correct path for a client, we have to search for all entries and return the neighbour to connect

    def add_parent(self, parent):
        self.parents.append(parent)

    def add_entry(self, leaf, neighbour, next_hop):
        entry = TableEntry(next_hop)
        first_entry = False

        if leaf not in self.table:
            first_entry = True
            self.table[leaf] = {}
            entry.in_tree = True

        if neighbour not in self.table[leaf]:
            self.table[leaf][neighbour] = []

        already_exists = any(en.next_hop == next_hop for en in self.table[leaf][neighbour])

        if not already_exists:
            self.table[leaf][neighbour].append(entry)

        return first_entry

    def get_next_hop(self, leaf):
        if leaf in self.table:
            for neighbour, entries in self.table[leaf].items():
                for entry in entries:
                    if entry.in_tree:
                        return entry.next_hop
        # Return a default value or handle the case when the leaf is not found
        return None

    def remove_leaf(self, leaf):
        del self.table[leaf]

    def __str__(self) -> str:
        return repr(self)
    
    def __repr__(self) -> str:
        st = "------- Table: -------\n"

        for entry in self.table:
            st += entry + "->>>>>>>>>>>>>\n" + str(self.table[entry]) + "\n"

        return st
