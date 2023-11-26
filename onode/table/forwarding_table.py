import sys

from table.table_entry import TableEntry
import threading
import copy


class ForwardingTable:
    def __init__(self):
        self.table = {}  # Node_Id -> Neighbour -> Entry
        self.table_lock = threading.Lock()  # Add a lock for thread safety
        self.tree = {}  # Node_Id -> Neighbour
        self.tree_lock = threading.Lock()

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
                self.table[node_id][neighbour] = []

            already_exists = any(en.next_hop == next_hop for en in self.table[node_id][neighbour])

            if not already_exists:
                self.table[node_id][neighbour].append(entry)

            return is_first_entry, already_exists

    def get_neighbour_to_rp(self):
        with self.tree_lock:
            if 255 in self.tree:
                return self.tree[255][0]
            return None

    def get_best_entries(self):
        best_entries = []

        with self.tree_lock:
            for node_id, value in self.tree.items():
                best_entries.append((node_id, value[0], value[1].delay, value[1].loss))

        return best_entries

    def get_best_entry(self, node_id):
        with self.tree_lock:
            if node_id in self.tree:
                return self.tree[node_id][1]
        return None

    def get_entry(self, node_id, neighbour, next_hop):
        if node_id in self.table and neighbour in self.table[node_id]:
            for entry in self.table[node_id][neighbour]:
                if entry.next_hop == next_hop:
                    return entry
        return None

    def update_metrics(self, node_id, neighbour, next_hop, delay, loss):

        is_first_entry, _ = self.add_entry(node_id, neighbour, next_hop, delay, loss)
        if is_first_entry:
            return

        with self.table_lock:
            current_entry = self.get_entry(node_id, neighbour, next_hop)

            best_entry = None
            best_entry_neighbour = None

            # Find the best entry
            for entry_neighbour, entry_list in self.table[node_id].items():
                for entry in entry_list:
                    if entry.in_tree:
                        best_entry = entry
                        best_entry_neighbour = entry_neighbour
                        break
                if best_entry is not None:
                    break

            # The entry to update is the best entry
            if best_entry_neighbour == neighbour and best_entry.next_hop == next_hop:
                best_entry.delay = delay
                best_entry.loss = loss
                best_entry.in_tree = False

                # Obtain the best entry
                best_score = sys.maxsize
                for leaf in self.table.keys():
                    for entries in self.table[leaf].values():
                        for entry in entries:
                            entry_score = entry.get_metric()
                            if entry_score < best_score:
                                best_entry = entry

                best_entry.in_tree = True
                return

            current_entry.delay = delay
            current_entry.loss = loss

            if best_entry.get_metric() > current_entry.get_metric():
                best_entry.in_tree = False
                current_entry.in_tree = True
                best_entry = current_entry

            with self.tree_lock:
                self.tree[node_id] = (neighbour, best_entry)

    def get_table(self):
        with self.table_lock:
            return copy.deepcopy(self.table)

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
