import threading
import json


class StreamTable:
    """
    This class is used to store the stream information of each Node.
    For each possible stream (identified by a number, store the list of clients waiting for that streaming) 
    """
    def __init__(self):
        self.table = {}
        self.servers_entries = {}
        self.lock = threading.Lock()

    def add_client_to_stream(self, stream_id, client):
        with self.lock:
            if stream_id not in self.table:
                self.table[stream_id] = ([], [])
            if client not in self.table[stream_id][1]:
                self.table[stream_id][1].append(client)

    def add_server_to_stream(self, stream_id, server_ip):
        with self.lock:
            if stream_id not in self.table:
                self.table[stream_id] = ([], [])
            if server_ip not in self.table[stream_id][0]:
                self.table[stream_id][0].append(server_ip)

    def its_best_server(self, stream_id, server_ip):
        # We have to update this
        return True

    def get_stream_clients(self, stream_id):
        with self.lock:
            if stream_id in self.table:
                return self.table[stream_id][1]
            return []

    def get_clients(self):
        with self.lock:
            stream_clients = []
            for stream_id in self.table.keys():
                servers, clients = self.table[stream_id]
                stream_clients.append((stream_id, clients))
            return stream_clients

    def remove_client_from_stream(self, stream_id, client):
        with self.lock:
            self.table[stream_id][1].remove(client)

    def remove_server_from_stream(self, stream_id, server_ip):
        with self.lock:
            self.table[stream_id][0].remove(server_ip)

    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        string = "------- Table: -------\n"

        for entry in self.table:
            string += str(entry) + "->>>>>>>>>>>>>\n" + str(self.table[entry]) + "\n"

        return string
