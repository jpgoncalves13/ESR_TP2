import json


# Read the file with the nodes of the overlay topology
def read_nodes_file(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)
    return data
