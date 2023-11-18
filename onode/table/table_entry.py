class TableEntry:
    """
    A class used to represent a table entry
    A table entry is composed of a list of next hops, the delay and the loss in the link to the next hop
    """
    def __init__(self, next_hop=None, in_tree=False, delay=None, loss=None):
        self.next_hop = next_hop
        self.delay = delay
        self.loss = loss
        self.in_tree = in_tree

    def set_delay(self, delay):
        self.delay = delay

    def get_metric(self):
        return 0.7 * self.delay / 1000 + 0.3 * self.loss

    def __str__(self) -> str:
        return ("Next Hop: " + str(self.next_hop) + "; Delay: " + str(self.delay) + "; Loss: "
                + str(self.loss) + "; In tree:" + str(self.in_tree))
