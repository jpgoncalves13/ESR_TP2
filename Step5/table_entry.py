class TableEntry:
    """
    A class used to represent a table entry
    A table entry is composed of a list of next hops, the delay and the loss in the link to the next hop
    """
    def __init__(self, next_hops, delay, loss):
        self.next_hops = next_hops
        self.delay = delay
        self.loss = loss

    def __str__(self) -> str:
        return "Next Hops: " + str(self.next_hops) + "\nDelay: " + str(self.delay) + "\nLoss: " + str(self.loss)
    
    def __repr__(self) -> str:
        return "Next Hops: " + str(self.next_hops) + "\nDelay: " + str(self.delay) + "\nLoss: " + str(self.loss)
