class StreamTable:
    """
    This class is used to store the stream information of each Node.
    For each possible stream (identified by a number, store the list of clients waiting for that streaming) 
    """
    def __init__(self):
        self.table = {}

    def add_stream_entry(self, stream_id, clients):
        if clients is None:
            self.table[stream_id] = []
        else:
            self.table[stream_id] = clients

    def add_client_to_stream(self, stream_id, client):
        self.table[stream_id].append(client)

    def remove_client_from_stream(self, stream_id, client):
        self.table[stream_id].remove(client)

    def remove_entry(self, stream_id):
        del self.table[stream_id]

    def consult_entry(self, stream_id):
        return self.table[stream_id]
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        str = "------- Table: -------\n"

        for entry in self.table:
            str += entry + "->>>>>>>>>>>>>\n" + self.table[entry].__str__() + "\n"

        return str