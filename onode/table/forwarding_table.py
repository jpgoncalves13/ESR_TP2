import sys
import threading
import copy
from table.table_entry import TableEntry


class ForwardingTable:
    """
    This class is used to store the entries to the RP
    Also store the best entry to the RP
    Each node knows the best neighbour to reach the RP
    """
    def __init__(self):
        self.table_lock = threading.Lock()
        self.tree_lock = threading.Lock()
        self.steps_lock = threading.Lock()
        self.next_steps = {}  # Neighbour : Neighbours of neighbour
        self.rp_table = {}    # RP IP : Neighbour : Entry
        self.rp_entry = None  # (RP IP, Neighbour, Entry)

    def add_next_steps(self, neighbour, next_steps):
        with self.steps_lock:
            self.next_steps[neighbour] = next_steps

    def get_next_steps(self, neighbour):
        with self.steps_lock:
            if neighbour in self.next_steps:
                return self.next_steps[neighbour]
            return []

    """
    Adds a new entry to the rp table
    Store the neighbour, the next_hop, the delay and the loss in that path
    """
    def add_entry_rp(self, rp_ip, neighbour, delay=0, loss=0):
        # Create the new entry
        entry = TableEntry(delay, loss)
        is_first_entry = False

        with self.table_lock:
            # First entry to rp is the best entry            
            if len(self.rp_table.keys()) == 0:
                is_first_entry = True
                with self.tree_lock:
                    self.rp_entry = (rp_ip, neighbour, entry)

            # Add the entry
            if rp_ip not in self.rp_table:
                self.rp_table[rp_ip] = {}

            self.rp_table[rp_ip][neighbour] = entry

            return is_first_entry

    """
    Get the neighbour of the best entry to the rp table
    """
    def get_neighbour_to_rp(self):
        with self.tree_lock:
            if self.rp_entry is not None:
                return self.rp_entry[1]
            return None

    """
    Get all the neighbours that can connect to the rp
    """
    def get_neighbours_to_rp(self):      
        with self.steps_lock:
            return self.next_steps.keys()

    """
    Get the best entry to the rp table
    """
    def get_best_entry_rp(self):
        with self.tree_lock:
            if self.rp_entry is not None:
                return self.rp_entry[0], self.rp_entry[0], self.rp_entry[2].delay, self.rp_entry[2].loss
            return None
    
    """
    Get the entry to RP given the rp_ip and the neighbour
    """
    def get_entry_rp(self, rp_ip, neighbour):
        if rp_ip in self.rp_table and neighbour in self.rp_table[rp_ip]:
            return self.rp_table[rp_ip][neighbour]
        return None
    
    """
    Update the metrics of an path entry to the rp
    Based on the the rp_ip and the neighbour, update the next_hop, the delay and the loss
    """
    def update_metrics_rp(self, rp_ip, neighbour, delay, loss):
        is_first_entry = self.add_entry_rp(rp_ip, neighbour, delay, loss)
        if is_first_entry:
            return

        with self.table_lock:
            current_entry = self.get_entry_rp(rp_ip, neighbour)

            # Get the best entry
            with self.tree_lock:
                best_entry_ip = self.rp_entry[0]
                best_entry_neighbour = self.rp_entry[1]
                best_entry = self.rp_entry[2]

            # The entry to update is the best entry
            if best_entry_ip == rp_ip and best_entry_neighbour == neighbour:
                best_entry.delay = delay
                best_entry.loss = loss

                # Obtain the best entry
                best_score = sys.maxsize
                for rp in self.rp_table.keys():
                    for ng, entry in self.rp_table[rp].items():
                        entry_score = entry.get_metric()
                        if entry_score < best_score:
                            best_entry = entry
                            best_entry_neighbour = ng
                            best_entry_ip = rp

                with self.tree_lock:
                    self.rp_entry = (best_entry_ip, best_entry_neighbour, best_entry)

                return

            if best_entry.get_metric() > current_entry.get_metric():
                best_entry_ip = rp_ip
                best_entry_neighbour = neighbour
                best_entry = current_entry

            with self.tree_lock:
                self.rp_entry = (best_entry_ip, best_entry_neighbour, best_entry)

    """
        Update the table when a neighbour dies 
    """
    def update_neighbour_death(self, neighbour):
        with self.table_lock:
            for rp_ip in self.rp_table:
                if neighbour in self.rp_table[rp_ip]:
                    del self.rp_table[rp_ip][neighbour]

            with self.steps_lock:
                if neighbour in self.next_steps:
                    del self.next_steps[neighbour]

            best_score = sys.maxsize
            best_entry = None
            best_entry_neighbour = None
            best_entry_ip = None
            for rp_ip in self.rp_table:
                for ng, entry in self.rp_table[rp_ip].items():
                    entry_score = entry.get_metric()
                    if entry_score < best_score:
                        best_entry = entry
                        best_entry_neighbour = ng
                        best_entry_ip = rp_ip

                with self.tree_lock:
                    self.rp_entry = (best_entry_ip, best_entry_neighbour, best_entry)

    """
        Only for debug
    """
    def get_table_rp(self):
        with self.table_lock:
            return copy.deepcopy(self.rp_table)
