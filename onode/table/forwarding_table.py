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
        self.rp_table = {}    # Neighbour : Entry
        self.rp_entry = None  # (Neighbour, Entry)
        self.threshold = 10

    def add_next_steps(self, neighbour, next_steps):
        with self.steps_lock:
            self.next_steps[neighbour] = next_steps

    def get_next_steps(self, neighbour):
        with self.steps_lock:
            if neighbour in self.next_steps:
                return self.next_steps[neighbour]
            return []

    """
    Get the neighbour of the best entry to the rp table
    """
    def get_neighbour_to_rp(self):
        with self.tree_lock:
            if self.rp_entry is not None:
                return self.rp_entry[0]
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
                return self.rp_entry[0], self.rp_entry[1].delay, self.rp_entry[1].loss
            return None

    def add_best_entry(self, entry):
        with self.tree_lock:
            self.rp_entry = entry

    def get_best_entry(self):
        with self.tree_lock:
            return self.rp_entry

    """
    Update the metrics of an path entry to the rp
    Based on the the rp_ip and the neighbour, update the next_hop, the delay and the loss
    """
    def update_metrics_rp(self, neighbour, delay, loss):
        entry = TableEntry(delay, loss)

        with self.table_lock:
            # first entry in table -> is the best entry
            if len(self.rp_table.keys()) == 0:
                # Add the entry
                self.rp_table[neighbour] = entry
                self.add_best_entry((neighbour, entry))
                return

            # Add the entry
            self.rp_table[neighbour] = entry

            # Get the best entry
            best_entry_neighbour, best_entry = self.get_best_entry()

            # The entry to update is the best entry
            if best_entry_neighbour == neighbour:

                if best_entry.get_metric() < entry.get_metric() + self.threshold:
                    self.add_best_entry((best_entry_neighbour, best_entry))
                    return

                # Obtain the best entry
                best_score = sys.maxsize
                for ng, entry in self.rp_table.items():
                    entry_score = entry.get_metric()
                    if entry_score < best_score:
                        best_entry = entry
                        best_entry_neighbour = ng

                self.add_best_entry((best_entry_neighbour, best_entry))
                return

            if best_entry.get_metric() > entry.get_metric() + self.threshold:
                best_entry_neighbour = neighbour
                best_entry = entry

            self.add_best_entry((best_entry_neighbour, best_entry))

    def remove_next_steps(self, neighbour):
        with self.steps_lock:
            if neighbour in self.next_steps:
                del self.next_steps[neighbour]

    """
        Update the table when a neighbour dies 
    """
    def update_neighbour_death(self, neighbour):
        with self.table_lock:
            # Remove the entry to rp with this neighbour
            if neighbour in self.rp_table:
                del self.rp_table[neighbour]

            # Delete the neighbour in next steps
            self.remove_next_steps(neighbour)

            # Get the best entry
            best_entry = self.get_best_entry()
            if best_entry is None:
                return

            if best_entry[0] != neighbour:
                return

            best_score = sys.maxsize
            best_entry = None
            best_entry_neighbour = None
            for ng, entry in self.rp_table.items():
                entry_score = entry.get_metric()
                if entry_score < best_score:
                    best_entry = entry
                    best_entry_neighbour = ng

            best_entry = (best_entry_neighbour, best_entry) if best_entry is not None else None
            self.add_best_entry(best_entry)

    """
        Only for debug
    """
    def get_table_rp(self):
        with self.table_lock:
            return copy.deepcopy(self.rp_table)
