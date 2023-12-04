import sys
import socket
from server.server import Server
from server.stream_packet import Packet, PacketType
from bootstrapper.bootstrapper import Bootstrapper
from server.shared_state import EP
from client.ClientLauncher import ClientLauncher
import re


def main():
    if len(sys.argv) < 2:
        print("onode: try 'onode --help' for more information")
        return

    # --help option
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        info = """Usage: onode (--bootstrapper <file>)? <bootstrapper-ip(:bootstrapper-port)?> [node options]

Node Options:
 -r, --rendezvous Rendezvous point.
 -d, --debug      Debug mode.
 --tag            Tag 
"""
        print(info)
        return

    # Standard port
    port = 5000
    # Parse the arguments
    bootstrapper, bootstrapper_address, is_rendezvous_point, debug, tag, client = read_args()

    # Request the neighbors if is a node and not the bootstrapper
    if bootstrapper is None:
        if debug:
            print(f"DEBUG: Requesting the Neighbors")
        neighbours = request_neighbors(bootstrapper_address)
    else:
        neighbours = {}
        neighbours_list = bootstrapper.get_neighbors(bootstrapper_address[0])
        for neighbour in neighbours_list:
            neighbours[neighbour] = False

    if len(neighbours.keys()) == 0:
        print("This is not a overlay node")
        exit(1)

    if debug:
        print(f"DEBUG: Neighbors -> {neighbours.keys()}")

    ep = EP(debug, bootstrapper, is_rendezvous_point, port, neighbours, tag, client)

    if ep.get_num_neighbours() == 1 and client > 0:
        client_launcher = ClientLauncher(ep.get_neighbours()[0], client, ep)
        client_launcher.run()
    elif ep.get_num_neighbours() > 1 and client > 0:
        print("This is not a leaf node to put a client on it")
        print("Starting only the overlay node")

    # Start the server
    server = Server(port)
    server.run(ep)


def request_neighbors(bootstrapper_address, timeout=5, max_retries=3):
    retries = 0
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.settimeout(timeout)
    neighbours = {}

    try:
        while retries < max_retries:
            try:
                packet_serialized = Packet(PacketType.SETUP, '0.0.0.0', 0, '0.0.0.0').serialize()
                udp_socket.sendto(packet_serialized, bootstrapper_address)
                response, _ = udp_socket.recvfrom(4096)
                response_packet = Packet.deserialize(bytearray(response))
                for neighbour in response_packet.payload:
                    neighbours[neighbour] = False
                break
            except socket.timeout:
                retries += 1
    finally:
        udp_socket.close()

    return neighbours


def is_valid_ip(ip):
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    return re.match(pattern, ip) is not None


def get_bootstrapper_address(words):
    if len(words) == 2:
        if not words[1].isdigit():
            print("Error: The bootstrapper port should be an integer")
            exit(1)

        if is_valid_ip(words[0]):
            return words[0], int(words[1])
        else:
            print(f"Error: {words[0]} is not a valid IP address")
            exit(1)
    elif len(words) == 1:
        if is_valid_ip(words[0]):
            return words[0], 5000
        else:
            print(f"Error: {words[0]} is not a valid IP address")
            exit(1)
    else:
        print("Error: Wrong bootstrapper configuration\nTry --help for more information")
        exit(1)


def read_args():
    i = 1
    bootstrapper = None
    debug = False
    tag = None
    is_rendezvous_point = False
    client = 0

    if sys.argv[i] == '--bootstrapper':
        # --bootstrapper <file>
        i += 1
        file = sys.argv[i]
        bootstrapper = Bootstrapper(file)
        i += 1

    # <bootstrapper-ip:bootstrapper-port>
    if ':' in sys.argv[i]:
        words = sys.argv[i].split(':')
    else:
        words = [sys.argv[i]]

    bootstrapper_address = get_bootstrapper_address(words)
    i += 1

    # options
    while i < len(sys.argv):
        if sys.argv[i] == '--rendezvous':
            # for the rendezvous point
            is_rendezvous_point = True
        elif sys.argv[i] == '--debug':
            # for the debug mode
            debug = True
        elif sys.argv[i] == '--tag':
            tag = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == '--client':
            if sys.argv[i + 1].isdigit():
                client = int(sys.argv[i + 1])
            else:
                print(f"Invalid argument: {sys.argv[i + 1]}. I need a stream id")
                exit(1)
            i += 1
        else:
            print(f"Invalid argument: {sys.argv[i]}")
        i += 1

    if bootstrapper is not None and debug:
        bootstrapper.set_debug(debug)

    return bootstrapper, bootstrapper_address, is_rendezvous_point, debug, tag, client


if __name__ == '__main__':
    main()
