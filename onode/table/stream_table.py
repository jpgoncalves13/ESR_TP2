import sys
import threading
import json
import copy
from table.table_entry import TableEntry


class StreamTable:
    """
    This class is used to store the stream information of a node.
    For each possible stream (identified by a number, store the list of neighbours requesting that stream)
    """
    def __init__(self):
        self.table = {} # Table of servers and neighbours for each stream 
        self.servers_entries = {}
        self.lock = threading.Lock()

    """
    Adds a neighbour to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_neighbour_to_stream(self, stream_id, neighbour):
        with self.lock:
            if stream_id not in self.table:
                self.table[stream_id] = (set(), set())
            self.table[stream_id][1].add(neighbour)
    
    """
    Removes a neighbour from a stream
    """         
    def remove_neighbour_from_stream(self, neighbour):
        with self.lock:
            for stream_id in self.table:
                self.table[stream_id][1].remove(neighbour)
                
    """
    Add a server to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_server_to_stream(self, stream_id, server_ip):
        with self.lock:
            if stream_id not in self.table:
                self.table[stream_id] = (set()), set()
            self.table[stream_id][0].add(server_ip)
            
            # Add the server to the server measure list 
            if server_ip not in self.servers_entries:
                self.servers_entries[server_ip] = TableEntry('0.0.0.0', 0, 0)
                
    """
    Remove a server from a stream
    """
    def remove_server_from_stream(self, stream_id, server_ip):
        with self.lock:
            self.table[stream_id][0].remove(server_ip)
            
    """
    Check if a stream is already in the stream list
    """
    def check_if_stream_exists(self, stream_id):
        with self.lock:
            return stream_id in self.table

    """
    Get all the servers currently streaming
    """
    def get_servers(self):
        with self.lock:
            return list(self.servers_entries.keys())
        
    """
    Get the neighbours for a given stream
    """
    def get_stream_neighbours(self, stream_id):
        with self.lock:
            if stream_id in self.table:
                return self.table[stream_id][1]
            return []

    """
    Update the metrics associated with a given server (server, delay, loss)
    """
    def update_metrics_server(self, server, delay, loss):
        with self.lock:
            self.servers_entries[server] = TableEntry('0.0.0.0', delay, loss)

    # TODO
    def its_best_server(self, stream_id, server_ip):
        with self.lock:
            servers, clients = self.table[stream_id]

            score = sys.maxsize
            best_server = None
            for server in servers:
                entry = self.servers_entries[server]
                if entry.get_metric() < score:
                    score = entry.get_metric()
                    best_server = server

            return best_server == server_ip

    """
    Get all the neighbours
    """
    """
    def get_clients(self):
        with self.lock:
            stream_clients = []
            for stream_id in self.table.keys():
                servers, clients = self.table[stream_id]
                stream_clients.append((stream_id, clients))
            return stream_clients"""

    def get_stream_table(self):
        with self.lock:
            return copy.deepcopy(self.table)

    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        string = "------- Table: -------\n"

        for entry in self.table:
            string += str(entry) + "->>>>>>>>>>>>>\n" + str(self.table[entry]) + "\n"

        return string
