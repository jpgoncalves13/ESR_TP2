import sys

from table.table_entry import TableEntry
import threading
import copy


class ForwardingTable:
    def __init__(self):
        self.table = {}  # Leaf -> Neighbour -> Entry
        self.parents = []  # We may also store the parents of this node in the tree
        self.lock = threading.Lock()  # Add a lock for thread safety

    def get_parents(self):
        with self.lock:
            return copy.copy(self.parents)

    def get_neighbours_to_request(self):  # For measure
        with self.lock:
            neighbours = []
            for leaf in self.table.keys():
                for neighbour in self.table[leaf].keys():
                    neighbours.append(neighbour)
            return neighbours

    def add_parent(self, parent):  # For tree update
        with self.lock:
            self.parents.append(parent)

    def get_neighbour_to_request(self, leaf):  # For tree update, to send to the next child in the tree
        with self.lock:
            if leaf in self.table:
                for neighbour, value in self.table[leaf].items():
                    for entry in value:
                        if entry.in_tree:
                            return neighbour
            return None

    def update_tree_entry(self, leaf, next_hop):
        with self.lock:
            if leaf in self.table and next_hop in self.table[leaf]:
                entries = self.table[leaf][next_hop]

                for neighbour, value in self.table[leaf].items():
                    for entry in value:
                        entry.in_tree = False

                if len(entries) == 1:
                    entries[0].in_tree = True
                    return entries[0].next_hop
                elif len(entries) > 1:
                    best_entry = entries[0]
                    metric = best_entry.get_metric()
                    for entry in entries:
                        metric_i = entry.get_metric()
                        if metric_i < metric:
                            best_entry = entry
                            metric = metric_i

                    best_entry.in_tree = True
                    return best_entry.next_hop
                return None

    def add_entry(self, node_id, neighbour, next_hop, delay=None, loss=None):  # For join
        with self.lock:
            entry = TableEntry(next_hop, delay, loss)
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
            if "RP" in self.table:
                for neighbour, entries in self.table["RP"]:
                    for entry in entries:
                        if entry.in_tree:
                            return neighbour
            return None

    def get_best_entries(self):
        best_entries = []

        with self.lock:
            for leaf in self.table.keys():
                best_entry_found = False

                for neighbour, entries in self.table[leaf]:
                    for entry in entries:
                        if entry.in_tree:
                            best_entries.append((leaf, neighbour, entry.delay, entry.loss))
                            best_entry_found = True
                            break
                    if best_entry_found:
                        break

        return best_entries

    def get_entry(self, leaf, neighbour, next_hop):
        if leaf in self.table and neighbour in self.table[leaf]:
            for entry in self.table[leaf][neighbour]:
                if entry.next_hop == next_hop:
                    return entry
        return None

    def update_metrics(self, leaf, neighbour, next_hop, delay, loss):

        with self.lock:
            current_entry = self.get_entry(leaf, neighbour, next_hop)
            if current_entry is None:
                self.add_entry(leaf, neighbour, next_hop, delay, loss)

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

            if best_entry.get_metric() > current_entry.get_metric():
                best_entry.in_tree = False
                current_entry.in_tree = True

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
