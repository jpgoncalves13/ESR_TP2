import sys
from bootstraper import Bootstrapper
from server import Server
from threading import Thread
import socket
from stream_packet import PacketType, Packet


def request_neighbors(node_ip, bootstrapper_address, timeout=5, max_retries=3):
    retries = 0
    packet_serialized = Packet(node_ip, PacketType.SETUP, [], 0, 0, 0).serialize()
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    response = None

    while retries < max_retries:
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


def main():
    if len(sys.argv) < 2:
        print("onode: try 'onode --help' for more information")
        return

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

    debug = False
    is_rendezvous_point = False
    node = False

    bootstrapper = None
    bootstrapper_address = None

    i = 1
    if sys.argv[i] == '--bootstrapper':
        # Bootstrapper node
        file = sys.argv[i + 1]
        bootstrapper = Bootstrapper(file)
        i += 2
    else:
        # Normal node
        words = sys.argv[i].split(':')
        if len(words) == 2:
            bootstrapper_address = (words[0], words[1])
            node = True
            i += 1
        else:
            print("Wrong bootstrapper configuration")
            return

    while i < len(sys.argv):
        if sys.argv[i] == '--rendezvous':
            is_rendezvous_point = True
        elif sys.argv[i] == '--debug':
            debug = True
        elif sys.argv[i] == '--node':
            node = True
        i += 1

    if bootstrapper is not None and debug:
        bootstrapper.set_debug(debug)

    neighbors = None
    port = 5000

    # Get all the ips
    host_name = socket.gethostname()
    ip_list = socket.gethostbyname_ex(host_name)
    last_ip = ip_list[2].pop()

    # Request the neighbors
    if bootstrapper is None:
        neighbors = request_neighbors(last_ip, bootstrapper_address)

    # Start all threads with the different ips
    args = (bootstrapper, neighbors, is_rendezvous_point, node)
    for ip in ip_list[2]:
        if debug:
            print(f"DEBUG: {ip}")
        server = Server(ip, port, debug=debug)
        Thread(target=lambda: server.run(args)).start()

    server = Server(last_ip, port, debug=debug)
    server.run(args)


if __name__ == '__main__':
    main()
