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
            return copy.deepcopy(self.parents)

    def get_neighbours_to_request(self):  # For measure
        with self.lock:
            neighbours = []
            for value in self.table.values():
                for key in value.keys():
                    neighbours.append(key)
            return neighbours

    def add_parent(self, parent):  # For tree update
        with self.lock:
            self.parents.append(parent)

    def get_neighbour_to_request(self, leaf):  # For tree update, to send to the next child in the tree
        with self.lock:
            if leaf in self.table:
                for item in self.table[leaf].items():
                    for entry in item[1]:
                        if entry.in_tree:
                            return item[0]
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

    def add_entry(self, leaf, neighbour, next_hop, is_rendezvous_point):  # For join
        with self.lock:
            entry = TableEntry(next_hop)
            is_first_entry = False

            if leaf not in self.table:
                is_first_entry = True
                self.table[leaf] = {}
                if is_rendezvous_point:
                    entry.in_tree = True

            if neighbour not in self.table[leaf]:
                self.table[leaf][neighbour] = []

            already_exists = any(en.next_hop == next_hop for en in self.table[leaf][neighbour])

            if not already_exists:
                self.table[leaf][neighbour].append(entry)

            return is_first_entry

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
