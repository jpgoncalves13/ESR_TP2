class TableEntry:
    """
    A class used to represent a table entry
    A table entry is composed of a list of next hops, the delay and the loss in the link to the next hop
    """
    def __init__(self, next_hops=None, delay=None, packages_sent=0, packets_received=0):
        if next_hops is None:
            next_hops = []

        self.next_hops = next_hops
        self.delay = delay
        self.packets_sent = packages_sent
        self.packets_received = packets_received

    def update_packets_sent(self):
        self.packets_sent += 1

    def update_packets_received(self):
        self.packets_received += 1

    def update_delay(self, delay):
        self.delay = delay

    def __str__(self) -> str:
        return ("Next Hops: " + str(self.next_hops) + "\nDelay: " + str(self.delay) + "\nLoss: "
                + str(self.packets_received/self.packets_sent)) if self.packets_sent > 0 else "N/A"
    
    def __repr__(self) -> str:
        return ("Next Hops: " + str(self.next_hops) + "\nDelay: " + str(self.delay) + "\nLoss: "
                + str(self.packets_received/self.packets_sent)) if self.packets_sent > 0 else "N/A"
