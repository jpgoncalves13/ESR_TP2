import sys
import threading
import copy
from table.table_entry import TableEntry


class StreamTable:
    """
    This class is used to store the stream information of a node.
    For each possible stream (identified by a number, store the list of neighbours requesting that stream)
    """
    def __init__(self):
        self.table = {}  # Table of servers and neighbours for each stream, stream_id : (servers, neighbours)
        self.servers_entries = {}
        self.table_lock = threading.Lock()
        self.entries_lock = threading.Lock()

    """
    Adds a neighbour to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_neighbour_to_stream(self, stream_id, neighbour):
        with self.table_lock:
            if stream_id not in self.table:
                self.table[stream_id] = (set(), set())

            self.table[stream_id][1].add(neighbour)
    
    """
    Removes a neighbour from a stream
    Returns if it was the last neighbour from that stream 
    """         
    def remove_neighbour_from_stream(self, stream_id, neighbour_ip):
        with self.table_lock:
            self.table[stream_id][1].discard(neighbour_ip)
            return len(self.table[stream_id][1]) == 0

    def remove_stream(self, stream_id):
        with self.table_lock:
            if stream_id in self.table:
                del self.table[stream_id]

    """
    Add a server to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_server_to_stream(self, stream_id, server_ip):
        with self.table_lock:
            if stream_id not in self.table:
                self.table[stream_id] = (set(), set())
            self.table[stream_id][0].add(server_ip)

        with self.entries_lock:
            # Add the server to the server measure list
            if server_ip not in self.servers_entries:
                self.servers_entries[server_ip] = TableEntry(0, 0)

    """
    Remove a server from a stream
    """
    def remove_server_from_stream(self, server_ip):
        with self.table_lock:
            for stream_id in self.table:
                servers, _ = self.table[stream_id]
                if server_ip in servers:
                    servers.discard(server_ip)
                    break

        with self.entries_lock:
            if server_ip in self.servers_entries:
                del self.servers_entries[server_ip]
            
    """
    Check if a stream is already in the stream list
    """
    def check_if_stream_exists(self, stream_id):
        with self.table_lock:
            return stream_id in self.table

    def check_if_server_exists(self, stream_id):
        with self.table_lock:
            return len(self.table[stream_id][0]) > 0

    """
    Get all the servers currently streaming
    """
    def get_servers(self):
        with self.entries_lock:
            return list(self.servers_entries.keys())
        
    """
    Get the neighbours for a given stream
    """
    def get_stream_neighbours(self, stream_id):
        with self.table_lock:
            if stream_id in self.table:
                return self.table[stream_id][1]
            return []

    """
    Update the metrics associated with a given server (server, delay, loss)
    """
    def update_metrics_server(self, server, delay, loss):
        with self.entries_lock:
            self.servers_entries[server] = TableEntry(delay, loss)

    """
    Return a true if it's the server with the best metric for a specific stream_id
    """
    def its_best_server(self, stream_id, server_ip):
        with self.table_lock:
            servers, clients = self.table[stream_id]

            score = sys.maxsize
            best_server = None
            for server in servers:
                with self.entries_lock:
                    entry = self.servers_entries[server]
                if entry.get_metric() < score:
                    score = entry.get_metric()
                    best_server = server

        return best_server == server_ip

    def get_stream_table(self):
        with self.table_lock:
            return copy.deepcopy(self.table)

    def get_streams(self):
        streams = set()
        with self.table_lock:
            for stream_id in self.table:
                if len(self.table[stream_id][1]) >= 1:
                    streams.add(stream_id)
        return streams
        
    def remove_neighbour_from_stream_table(self, neighbour_ip):
        with self.table_lock:
            for stream_id in self.table:
                self.table[stream_id][1].discard(neighbour_ip)
                