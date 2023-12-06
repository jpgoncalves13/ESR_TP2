from bootstrapper.bootstrapper import Bootstrapper
from table.forwarding_table import ForwardingTable
from table.stream_table import StreamTable
import copy
import threading
import queue


class EP:

    def __init__(self, debug, bootstrapper: Bootstrapper, rendezvous, port, neighbours, tag, stream_id):
        self.debug = debug
        self.bootstrapper = bootstrapper
        self.rendezvous = rendezvous
        self.port = port
        self.tag = tag
        self.table = ForwardingTable()
        self.stream_table = StreamTable()

        self.neighbours_lock = threading.Lock()
        self.neighbours = neighbours
        self.num_neighbours = len(neighbours) if neighbours is not None else 0

        self.client_stream_id = stream_id  # When the client is together with the node
        self.client_lock = threading.Lock()
        self.client_on = False
        self.buffer = queue.Queue(maxsize=100) if self.client_stream_id > 0 else None

    def add_packet_to_buffer(self, rtp_packet):
        if self.client_stream_id > 0:
            self.buffer.put(rtp_packet)

    def get_packet_from_buffer(self):
        data = self.buffer.get()
        self.buffer.task_done()
        return data

    def get_neighbours_to_rp(self):
        return self.table.get_neighbours_to_rp()

    def update_client_state(self, state):
        with self.client_lock:
            self.client_on = state

    def get_client_state(self):
        with self.client_lock:
            return self.client_on

    """
    Get all the neighbours
    """
    def get_neighbours(self):
        with self.neighbours_lock:
            return list(self.neighbours)

    """
    Get the number of neighbours
    """
    def get_num_neighbours(self):
        with self.neighbours_lock:
            return self.num_neighbours

    """
    Add a neighbour 
    """
    def add_neighbour(self, neighbour):
        with self.neighbours_lock:
            if neighbour not in self.neighbours:
                self.neighbours.append(neighbour)
                self.num_neighbours += 1

    """
    Add a list of neighbour 
    """
    def add_neighbours(self, neighbours):
        with self.neighbours_lock:
            for neighbour in neighbours:
                if neighbour not in self.neighbours:
                    self.neighbours.append(neighbour)
                    self.num_neighbours += 1

    """
    Remove a neighbour 
    """
    def delete_neighbour(self, neighbour):
        with self.neighbours_lock:
            if neighbour in self.neighbours:
                self.neighbours.remove(neighbour)
                self.num_neighbours -= 1

    # BOOTSTRAPPER
    """
    Get the info of a node, based on its ip (bootstrapper)
    """
    def get_node_info(self, ip):
        return self.bootstrapper.get_node_info(ip)

    """
    Get the best entry to the rp table
    """
    def get_best_entry_rp(self):
        return self.table.get_best_entry_rp()

    """
    Get the neighbour of the best entry to the rp table
    """
    def get_neighbour_to_rp(self):
        return self.table.get_neighbour_to_rp()

    """
    Update the metrics of an path entry to the rp
    Based on the the rp_ip and the neighbour, update the next_hop, the delay and the loss
    """
    def update_metrics_rp(self, neighbour, delay, loss):
        self.table.update_metrics_rp(neighbour, delay, loss)

    def add_next_steps(self, neighbour, next_steps):
        self.table.add_next_steps(neighbour, next_steps)

    def get_next_steps(self, neighbour):
        return self.table.get_next_steps(neighbour)

    def update_neighbour_death(self, neighbour):
        return self.table.update_neighbour_death(neighbour)

    def get_table_rp(self):
        return self.table.get_table_rp()

    # STREAM TABLE
    
    """
    Adds a neighbour to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_neighbour_to_stream(self, stream_id, node_id):
        self.stream_table.add_neighbour_to_stream(stream_id, node_id)
        
    """
    Removes a neighbour from a stream
    Returns if it was the last neighbour from that stream 
    """      
    def remove_neighbour_from_stream(self, stream_id, neighbour_ip):
        return self.stream_table.remove_neighbour_from_stream(stream_id, neighbour_ip)

    def remove_stream(self, stream_id):
        return self.stream_table.remove_stream(stream_id)

    """
    Check if a stream is already in the stream list
    """
    def check_if_stream_exists(self, stream_id):
        return self.stream_table.check_if_stream_exists(stream_id)

    def check_if_server_exists(self, stream_id):
        return self.stream_table.check_if_server_exists(stream_id)

    """
    Add a server to a stream
    If the stream does not exist, add a new entry in the map with a new neighbour
    """
    def add_server_to_stream(self, stream_id, server_ip):
        self.stream_table.add_server_to_stream(stream_id, server_ip)

    """
    Get all the servers currently streaming
    """
    def get_servers(self):
        return self.stream_table.get_servers()

    def its_best_server(self, stream_id, server_ip):
        return self.stream_table.its_best_server(stream_id, server_ip)

    def remove_server_from_stream(self, server):
        self.stream_table.remove_server_from_stream(server)

    """
    Get the neighbours for a given stream
    """
    def get_stream_neighbours(self, stream_id):
        return self.stream_table.get_stream_neighbours(stream_id)

    """
    Update the metrics associated with a given server (server, delay, loss)
    """
    def update_metrics_server(self, server, delay, loss):
        self.stream_table.update_metrics_server(server, delay, loss)

    def get_stream_table(self):
        return self.stream_table.get_stream_table()
    
    def get_streams(self):
        return self.stream_table.get_streams()
