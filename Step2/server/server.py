import socket
from server.server_worker import ServerWorker
from server.stream_packet import Packet, PacketType


class Server:
    def __init__(self, ip, port, buffer_size=None):
        if buffer_size is None:
            buffer_size = 4096
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size

    def run(self, args):
        bootstrapper, bootstrapper_address, neighbors, is_rendezvous_point, node, debug = args

        # Send message to create the tree if I only have one neighbor
        if node:
            if debug:
                print("DEBUG: Sending the packet to create the tree")
            self.start_tree(neighbors)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip, self.port))

        if debug:
            print("DEBUG: Listening on port " + str(self.port) + "...")

        while True:
            request = server_socket.recvfrom(self.buffer_size)
            if debug:
                print("DEBUG: Request received")
            ServerWorker(args).run(request)

    def start_tree(self, neighbors):
        if len(neighbors) == 1:
            packet_serialized = Packet(self.ip, PacketType.SETUP, 0, 0, 0, []).serialize()
            udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            udp_socket.sendto(packet_serialized, neighbors[0])
            