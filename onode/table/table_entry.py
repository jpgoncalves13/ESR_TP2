class TableEntry:
    """
    A class used to represent a table entry
    A table entry is composed of a list of next hops, the delay and the loss in the link to the next hop
    """
    def __init__(self, next_hop=None, in_tree=False):
        self.next_hop = next_hop
        self.delay = None
        self.packets_sent = 0
        self.packets_received = 0
        self.in_tree = in_tree

    def update_packets_sent(self):
        self.packets_sent += 1

    def update_packets_received(self):
        self.packets_received += 1

    def update_delay(self, delay):
        self.delay = delay

    def __str__(self) -> str:
        return ("Next Hop: " + str(self.next_hop) + "\nDelay: " + str(self.delay) + "\nLoss: "
                + str(self.packets_received/self.packets_sent)) if self.packets_sent > 0 else "N/A" + str(self.in_tree)
    
    def __repr__(self) -> str:
        return ("Next Hop: " + str(self.next_hop) + "\nDelay: " + str(self.delay) + "\nLoss: "
                + str(self.packets_received/self.packets_sent)) if self.packets_sent > 0 else "N/A" + str(self.in_tree)
