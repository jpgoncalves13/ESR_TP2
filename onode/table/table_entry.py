class TableEntry:
    """
    A class used to represent a table entry
    A table entry is composed of a list of next hops, the delay and the loss in the link to the next hop
    """
    def __init__(self, delay, loss):
        self.delay = delay
        self.loss = loss

    def set_delay(self, delay):
        self.delay = delay

    def get_metric(self):
        return 2 * self.delay / 10000 + self.loss

    def __str__(self) -> str:
        return ("Delay: " + str(self.delay) + "; Loss: "
                + str(self.loss))

    def __repr__(self):
        return str(self)
