import sys
import socket
import netifaces as ni
from server.server import Server
from server.stream_packet import Packet, PacketType
from bootstrapper.bootstrapper import Bootstrapper
from server.shared_state import EP


def request_neighbors(bootstrapper_address, timeout=5, max_retries=3):
    retries = 0
    packet_serialized = Packet('', PacketType.SETUP, 0, 0, 0).serialize()
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
        response = Packet.deserialize(bytearray(response))
        return response.neighbors
    return []


def read_args() -> (Bootstrapper, (str, str), bool, bool):
    i = 1
    bootstrapper = None
    debug = False
    bootstrapper_address = None
    is_rendezvous_point = False

    if sys.argv[i] == '--bootstrapper':
        # --bootstrapper <file> [opt]
        file = sys.argv[i + 1]
        i += 2
        bootstrapper = Bootstrapper(file)

        while i < len(sys.argv):
            if sys.argv[i] == '--debug':
                # for the debug mode
                debug = True
            else:
                print(f"Invalid argument: {sys.argv[i]}")
            i += 1
    else:
        # <bootstrapper-ip:bootstrapper-port> [opt]
        if ':' in sys.argv[i]:
            words = sys.argv[i].split(':')
        else:
            words = [sys.argv[i]]
        if len(words) == 2:
            try:
                bootstrapper_address = (words[0], int(words[1]))
            except ValueError:
                print("Error: The bootstrapper port was to be an integer")
                exit(1)
            i += 1
        elif len(words) == 1:
            bootstrapper_address = (words[0], 5000)
        else:
            print("Error: Wrong bootstrapper configuration\n Try --help for more information")
            exit(1)

        while i < len(sys.argv):
            if sys.argv[i] == '--rendezvous':
                # for the rendezvous point
                is_rendezvous_point = True
            elif sys.argv[i] == '--debug':
                # for the debug mode
                debug = True
            else:
                print(f"Invalid argument: {sys.argv[i]}")
            i += 1

    if bootstrapper is not None and debug:
        bootstrapper.set_debug(debug)

    return bootstrapper, bootstrapper_address, is_rendezvous_point, debug


def main():
    if len(sys.argv) < 2:
        print("onode: try 'onode --help' for more information")
        return

    # --help option
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        info = """Usage: onode <bootstrapper-ip(:bootstrapper-port)?> [node options]
   or: onode --bootstrapper <file> [bootstrapper options]

Node Options:
 -r, --rendezvous Rendezvous point.
 -d, --debug      Debug mode.

Bootstrapper Options:
 -d, --debug      Debug mode.
"""
        print(info)
        return

    # Standard port
    port = 5000
    # Parse the arguments
    bootstrapper, bootstrapper_address, is_rendezvous_point, debug = read_args()

    # The neighbors of this normal node
    neighbours = None

    if bootstrapper is None:
        # Request the neighbors if is a node and not the bootstrapper
        neighbours = request_neighbors(bootstrapper_address)
        if debug:
            print(f"DEBUG: Neighbors -> {neighbours}")

    # Start the server
    args = (bootstrapper, bootstrapper_address, neighbours, is_rendezvous_point, debug)
    server = Server(port)
    server.run(args)


if __name__ == '__main__':
    main()
