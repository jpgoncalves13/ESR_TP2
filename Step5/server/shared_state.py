from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
from table.stream_table import StreamTable

class EP:

    def __init__(self, debug: bool, bootstrapper: Bootstrapper, rendezvous: bool, port, neighbours: [str], forwarding_table: ForwardingTable, stream_table: StreamTable):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        if forwarding_table is None:
            self.forwarding_table = ForwardingTable()
        else:
            self.forwarding_table = forwarding_table
        
        if stream_table is None:
            self.stream_table = StreamTable()
        else:
            self.stream_table = stream_table
        self.neighbours = neighbours
        self.port = port
        if neighbours is not None:
            for neighbour in neighbours:
                self.forwarding_table.add_entry(neighbour)
                
        self.count = 0 # Conta o número de mensagens recebidas

    def get_neighbours(self):
        return self.neighbours
