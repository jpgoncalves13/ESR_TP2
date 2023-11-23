import sys

from table.table_entry import TableEntry
import threading
import copy


class ForwardingTable:
    def __init__(self):
        self.table = {}  # Leaf -> Neighbour -> Entry
        self.lock = threading.Lock()  # Add a lock for thread safety

    def get_neighbours_to_request(self):  # For measure
        with self.lock:
            neighbours = []
            for leaf in self.table.keys():
                for neighbour in self.table[leaf].keys():
                    neighbours.append(neighbour)
            return neighbours

    def add_entry(self, node_id, neighbour, next_hop, delay=0, loss=0):  # For join
        with self.lock:
            entry = TableEntry(next_hop, False, delay, loss)
            is_first_entry = False

            if node_id not in self.table:
                is_first_entry = True
                self.table[node_id] = {}
                entry.in_tree = True

            if neighbour not in self.table[node_id]:
                self.table[node_id][neighbour] = []

            already_exists = any(en.next_hop == next_hop for en in self.table[node_id][neighbour])

            if not already_exists:
                self.table[node_id][neighbour].append(entry)

            return is_first_entry, already_exists

    def get_neighbour_to_rp(self):
        with self.lock:
            if 255 in self.table:
                for neighbour, entries in self.table[255]:
                    for entry in entries:
                        if entry.in_tree:
                            return neighbour
            return None

    def get_best_entries(self):
        best_entries = []

        with self.lock:
            for leaf in self.table.keys():
                best_entry_found = False

                for neighbour, entries in self.table[leaf].items():
                    for entry in entries:
                        if entry.in_tree:
                            best_entries.append((leaf, neighbour, entry.delay, entry.loss))
                            best_entry_found = True
                            break
                    if best_entry_found:
                        break

        return best_entries

    def get_best_entry(self, node_id):
        with self.lock:
            if node_id in self.table:
                for entries in self.table[node_id].values():
                    for entry in entries:
                        if entry.in_tree:
                            return entry
        return None

    def get_entry(self, leaf, neighbour, next_hop):
        if leaf in self.table and neighbour in self.table[leaf]:
            for entry in self.table[leaf][neighbour]:
                if entry.next_hop == next_hop:
                    return entry
        return None

    def update_metrics(self, leaf, neighbour, next_hop, delay, loss):

        is_first_entry, _ = self.add_entry(leaf, neighbour, next_hop, delay, loss)

        with self.lock:
            current_entry = self.get_entry(leaf, neighbour, next_hop)

            if is_first_entry:
                current_entry.in_tree = True
                return

            best_entry = None
            best_entry_neighbour = None

            # Find the best entry
            for entry_neighbour, entry_list in self.table[leaf].items():
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

            if best_entry is None:
                current_entry.in_tree = True
                return

            if best_entry.get_metric() > current_entry.get_metric():
                best_entry.in_tree = False
                current_entry.in_tree = True

    def get_table(self):
        with self.lock:
            return copy.deepcopy(self.table)

    def __str__(self) -> str:
        with self.lock:
            st = "------- Table: -------\n"

            for leaf, value in self.table.items():
                st += f"{leaf}:\n"
                for neighbour, entries_list in value.items():
                    st += f"    {neighbour}:\n"
                    for entry in entries_list:
                        st += f"        {entry}\n"

            return st
