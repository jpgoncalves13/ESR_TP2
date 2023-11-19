import sys
import socket
from server.server import Server
from server.stream_packet import Packet, PacketType
from bootstrapper.bootstrapper import Bootstrapper
from server.shared_state import EP
from server.probe_thread import ProbeThread
from table.stream_table import StreamTable
from table.forwarding_table import ForwardingTable


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
        if response.type == PacketType.RSETUP:
            return response.neighbors
    return []


def read_args() -> (Bootstrapper, (str, str), bool, bool):
    i = 1
    bootstrapper = None
    debug = False
    bootstrapper_address = None
    is_rendezvous_point = False
    f_table = None
    s_table = None

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
        elif len(words) == 1:
            bootstrapper_address = (words[0], 5000)
        else:
            print("Error: Wrong bootstrapper configuration\n Try --help for more information")
            exit(1)

        i += 1
        while i < len(sys.argv):
            if sys.argv[i] == '--rendezvous':
                # for the rendezvous point
                is_rendezvous_point = True
            elif sys.argv[i] == '--debug':
                # for the debug mode
                debug = True
            elif sys.argv[i] == '--f_table':
                print('aqui')
                # To specify forwarding
                filename = sys.argv[i+1]
                f_table = ForwardingTable(filename)
                i += 1
            elif sys.argv[i] == '--s_table':
                print('aqui')
                filename = sys.argv[i+1]
                s_table = StreamTable(filename)
                i += 1
            else:
                print(f"Invalid argument: {sys.argv[i]}")
            i += 1

    if bootstrapper is not None and debug:
        bootstrapper.set_debug(debug)

    return bootstrapper, bootstrapper_address, is_rendezvous_point, debug, f_table, s_table


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
    bootstrapper, bootstrapper_address, is_rendezvous_point, debug, f_table, s_table = read_args()

    # The neighbors of this normal node
    neighbours = None

    if bootstrapper is None:
        # Request the neighbors if is a node and not the bootstrapper
        if debug:
            print(f"DEBUG: Requesting the Neighbors")
        neighbours = request_neighbors(bootstrapper_address)
        if debug:
            print(f"DEBUG: Neighbors -> {neighbours}")

    ep = EP(debug, bootstrapper, is_rendezvous_point, port, neighbours, f_table, s_table)

    if neighbours is not None and len(neighbours) > 1:
        # Default interval for the probe messages
        interval = 5
        # Start the proof messages, only for the nodes not in tree leaves
        probe_thread = ProbeThread(ep, interval, port)
        probe_thread.start()

    # Start the server
    server = Server(port)
    server.run(ep)


if __name__ == '__main__':
    main()
