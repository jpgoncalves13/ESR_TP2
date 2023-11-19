import threading
import json

class StreamTable:
    """
    This class is used to store the stream information of each Node.
    For each possible stream (identified by a number, store the list of clients waiting for that streaming) 
    """
    def __init__(self, filename=None):
        if filename is not None:
            self.table = read_stream_table(filename)
            self.lock = threading.Lock()
        else:
            self.table = {}
            self.lock = threading.Lock()

    def add_stream_entry(self, stream_id, servers, clients):
        with self.lock:
            if clients is None:
                self.table[stream_id] = ([],[]) # server, clients
            else:
                self.table[stream_id][1] = clients

    def add_client_to_stream(self, stream_id, client):
        with self.lock:
            if stream_id not in self.table:
                self.table[stream_id] = ([], [client])
            self.table[stream_id][1].append(client)

    def remove_client_from_stream(self, stream_id, client):
        with self.lock:
            self.table[stream_id][1].remove(client)
            
    def add_server_to_stream(self, stream_id, server_ip):
        print(stream_id)
        print(server_ip)
        with self.lock:
            if stream_id not in self.table:
                self.table[stream_id] = ([server_ip], ['10.0.11.1'])
            self.table[stream_id][0].append(server_ip)
            
    def remove_server_from_stream(self, stream_id, server_ip):
        with self.lock:
            self.table[stream_id][0].remove(server_ip)

    def remove_entry(self, stream_id):
        with self.lock:
            del self.table[stream_id]

    def consult_entry_clients(self, stream_id):
        return self.table[stream_id][1]
    
    def consult_entry_servers(self, stream_id):
        if stream_id in self.table:
            return self.table[stream_id][0]
        else:
            return []
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        str = "------- Table: -------\n"

        for entry in self.table:
            str += entry + "->>>>>>>>>>>>>\n" + self.table[entry].__str__() + "\n"

        return str
    
def read_stream_table(filename):
    with open(filename, 'r') as file:
        data = json.load(file)

    for key in data:
        data[key] = ([], data[key])
        
    print(data)
    return data