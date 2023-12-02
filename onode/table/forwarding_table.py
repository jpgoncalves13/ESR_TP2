import sys

from table.table_entry import TableEntry
import threading
import copy


class ForwardingTable:
    def __init__(self):
        self.table = {}  # Node_Id -> Neighbour -> Entry
        self.table_lock = threading.Lock()  # Add a lock for thread safety
        self.tree = {}  # Node_Id -> (Neighbour, Entry)
        self.tree_lock = threading.Lock()
        self.rp_table = {}
        self.rp_entry = None  # (rp_IP, Neighbour, entry)

    def add_entry_rp(self, rp_ip, neighbour, next_hop, delay=0, loss=0):
        with self.table_lock:
            entry = TableEntry(next_hop, delay, loss)
            is_first_entry = False

            if len(self.rp_table.keys()) == 0:
                is_first_entry = True
                with self.tree_lock:
                    self.rp_entry = (rp_ip, neighbour, entry)

            if rp_ip not in self.rp_table:
                self.rp_table[rp_ip] = {}

            if neighbour not in self.rp_table[rp_ip]:
                self.rp_table[rp_ip][neighbour] = None

            if self.rp_table[rp_ip][neighbour] is None:
                new_entry_metric = entry.get_metric()
                old_entry_metric = self.table[rp_ip][neighbour].get_metric()
                if new_entry_metric < old_entry_metric:
                    self.table[rp_ip][neighbour] = entry
            else:
                self.table[rp_ip][neighbour] = entry

            return is_first_entry

    def get_neighbour_to_rp(self):
        with self.tree_lock:
            if self.rp_entry is not None:
                return self.rp_entry[1]
            return None

    def add_entry(self, node_id, neighbour, next_hop, delay=0, loss=0):  # For join
        with self.table_lock:
            entry = TableEntry(next_hop, delay, loss)
            is_first_entry = False

            if node_id not in self.table:
                is_first_entry = True
                self.table[node_id] = {}
                with self.tree_lock:
                    self.tree[node_id] = (neighbour, entry)

            if neighbour not in self.table[node_id]:
                self.table[node_id][neighbour] = None

            if self.table[node_id][neighbour] is not None:
                new_entry_metric = entry.get_metric()
                old_entry_metric = self.table[node_id][neighbour].get_metric()
                if new_entry_metric < old_entry_metric:
                    self.table[node_id][neighbour] = entry
            else:
                self.table[node_id][neighbour] = entry

            return is_first_entry
        
    def remove_client(self, node_id):
        with self.table_lock:
            if node_id in self.table:
                del self.table[node_id]

    def get_best_entries(self):
        best_entries = []

        with self.tree_lock:
            for leaf, value in self.tree.items():
                best_entries.append((leaf, value[0], value[1].delay, value[1].loss))

        return best_entries

    def get_best_entry_rp(self):
        with self.tree_lock:
            if self.rp_entry is not None:
                return self.rp_entry[0], self.rp_entry[1], self.rp_entry[2].delay, self.rp_entry[2].loss
            return None

    def get_best_entry(self, node_ip):
        with self.tree_lock:
            if node_ip in self.tree:
                return self.tree[node_ip][1]
        return None
    
    def get_neighbour_to_client(self, node_ip):
        with self.tree_lock:
            if node_ip in self.tree:
                return self.tree[node_ip][0]
        return None

    def get_entry(self, node_id, neighbour, next_hop):
        if node_id in self.table and neighbour in self.table[node_id]:
            for entry in self.table[node_id][neighbour]:
                if entry.next_hop == next_hop:
                    return entry
        return None

    def get_entry_rp(self, rp_ip, neighbour, next_hop):
        if rp_ip in self.rp_table and neighbour in self.rp_table[rp_ip]:
            for entry in self.rp_table[rp_ip][neighbour]:
                if entry.next_hop == next_hop:
                    return entry
        return None

    def update_metrics(self, node_id, neighbour, next_hop, delay, loss):

        is_first_entry = self.add_entry(node_id, neighbour, next_hop, delay, loss)
        if is_first_entry:
            return

        with self.table_lock:
            current_entry = self.get_entry(node_id, neighbour, next_hop)

            best_entry = None
            best_entry_neighbour = None

            # Get the best entry
            with self.tree_lock:
                if node_id in self.tree:
                    best_entry = self.tree[node_id][1]
                    best_entry_neighbour = self.tree[node_id][0]

            # The entry to update is the best entry
            if best_entry_neighbour == neighbour and best_entry.next_hop == next_hop:
                best_entry.delay = delay
                best_entry.loss = loss

                # Obtain the best entry
                best_score = sys.maxsize
                for ng, entry in self.table[node_id].items():
                    entry_score = entry.get_metric()
                    if entry_score < best_score:
                        best_entry = entry
                        best_entry_neighbour = ng

                with self.tree_lock:
                    self.tree[node_id] = (best_entry_neighbour, best_entry)

                return

            current_entry.delay = delay
            current_entry.loss = loss

            if best_entry.get_metric() > current_entry.get_metric():
                best_entry = current_entry

            with self.tree_lock:
                self.tree[node_id] = (neighbour, best_entry)

    def update_metrics_rp(self, rp_ip, neighbour, next_hop, delay, loss):
        is_first_entry = self.add_entry_rp(rp_ip, neighbour, next_hop, delay, loss)
        if is_first_entry:
            return

        with self.table_lock:
            current_entry = self.get_entry_rp(rp_ip, neighbour, next_hop)

            # Find the best entry
            with self.tree_lock:
                if self.rp_entry is not None:
                    best_entry = self.rp_entry[2]
                    best_entry_neighbour = self.rp_entry[1]
                    best_entry_ip = self.rp_entry[0]
                else:
                    self.rp_entry = (rp_ip, neighbour, current_entry)
                    return

            # The entry to update is the best entry
            if best_entry_ip == rp_ip and best_entry_neighbour == neighbour and best_entry.next_hop == next_hop:
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

            current_entry.delay = delay
            current_entry.loss = loss

            if best_entry.get_metric() > current_entry.get_metric():
                best_entry = current_entry
                best_entry_neighbour = neighbour
                best_entry_ip = rp_ip

            with self.tree_lock:
                self.rp_entry = (best_entry_ip, best_entry_neighbour, best_entry)

    def get_table(self):
        with self.table_lock:
            return copy.deepcopy(self.table)

    def get_table_rp(self):
        with self.table_lock:
            return copy.deepcopy(self.rp_table)

    def __str__(self) -> str:
        with self.table_lock:
            st = "------- Table: -------\n"

            for leaf, value in self.table.items():
                st += f"{leaf}:\n"
                for neighbour, entries_list in value.items():
                    st += f"    {neighbour}:\n"
                    for entry in entries_list:
                        st += f"        {entry}\n"

            return st
