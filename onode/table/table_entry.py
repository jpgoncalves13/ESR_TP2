class TableEntry:
    """
    A class used to represent a table entry
    A table entry is composed of a list of next hops, the delay and the loss in the link to the next hop
    """
    def __init__(self, next_hop=None, in_tree=False):
        self.next_hop = next_hop
        self.delay = None
        self.loss = None
        self.in_tree = in_tree

    def set_delay(self, delay):
        self.delay = delay

    def __str__(self) -> str:
        return ("Next Hop: " + str(self.next_hop) + "\nDelay: " + str(self.delay) + "\nLoss: "
                + str(self.loss) + str(self.in_tree))
    
    def __repr__(self) -> str:
        return ("Next Hop: " + str(self.next_hop) + "\nDelay: " + str(self.delay) + "\nLoss: "
                + str(self.loss) + str(self.in_tree))
