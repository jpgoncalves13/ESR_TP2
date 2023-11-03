import sys
import socket
import netifaces as ni
from server import Server
from stream_packet import Packet, PacketType
from bootstrapper import Bootstrapper


def request_neighbors(node_ip, bootstrapper_address, timeout=5, max_retries=3):
    retries = 0
    packet_serialized = Packet(node_ip, PacketType.SETUP, 0, 0, 0).serialize()
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    response = None

    while response is None and retries < max_retries:
        udp_socket.sendto(packet_serialized, bootstrapper_address)
        udp_socket.settimeout(timeout)
        try:
            response, _ = udp_socket.recvfrom(4096)
        except socket.timeout:
            retries += 1

    udp_socket.close()

    if response is not None:
        response = Packet.deserialize(response)
        return response.neighbors
    return []


def read_args() -> (Bootstrapper, (str, str), bool, bool):
    i = 1
    bootstrapper = None
    debug = False
    bootstrapper_address = None
    node = False
    is_rendezvous_point = False

    if sys.argv[i] == '--bootstrapper':
        # --bootstrapper <file>
        file = sys.argv[i + 1]
        bootstrapper = Bootstrapper(file)
        i += 2
    else:
        # <bootstrapper-ip:bootstrapper-port>
        words = sys.argv[i].split(':')
        if len(words) == 2:
            try:
                bootstrapper_address = (words[0], int(words[1]))
            except ValueError:
                print("Error: The bootstrapper port was to be an integer")
                exit(1)
            node = True
            i += 1
        else:
            print("Error: Wrong bootstrapper configuration\n Try --help for more information")
            exit(1)

    # options
    while i < len(sys.argv):
        if sys.argv[i] == '--rendezvous':
            # for the rendezvous point
            is_rendezvous_point = True
        elif sys.argv[i] == '--debug':
            # for the debug mode
            debug = True
        elif sys.argv[i] == '--node':
            # if is the bootstrapper also functions as a normal node
            node = True
        i += 1

    if bootstrapper is not None and debug:
        bootstrapper.set_debug(debug)

    return bootstrapper, bootstrapper_address, is_rendezvous_point, node, debug


def main():
    if len(sys.argv) < 2:
        print("onode: try 'onode --help' for more information")
        return

    # --help option
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        info = """Usage: onode <bootstrapper-ip:bootstrapper-port> [options]
   or: onode --bootstrapper <file> [options]

Options:
 -r, --rendezvous Rendezvous point.
 -n, --node       Node (This option in already enable in the first command).
 -d, --debug      Debug mode.
"""
        print(info)
        return

    # Standard port
    port = 5000
    # Parse the arguments
    bootstrapper, bootstrapper_address, is_rendezvous_point, node, debug = read_args()

    # The neighbors of this normal node
    neighbours = None

    if node:
        # Get the ip
        my_ip = None
        for interface in ni.interfaces():
            addresses = ni.ifaddresses(interface)
            if ni.AF_INET in addresses:
                for address in addresses[ni.AF_INET]:
                    ip = address['addr']
                    if ip != '127.0.0.1':
                        my_ip = ip
                        break

            if my_ip is not None:
                break

        if node and bootstrapper is None:
            # Request the neighbors if is a node and not the bootstrapper
            neighbours = request_neighbors(my_ip, bootstrapper_address)
        elif node:
            # Get the neighbors if is a node and bootstrapper
            neighbours = bootstrapper.get_neighbors(my_ip)

        if debug:
            print(f"DEBUG: Neighbors -> {neighbours}")

    # Start all threads with the different ips
    args = (bootstrapper, bootstrapper_address, neighbours, is_rendezvous_point, node, debug)
    server = Server('', port)
    server.run(args)


if __name__ == '__main__':
    main()
