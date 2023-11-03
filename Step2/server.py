from threading import Thread
import socket
from server_worker import ServerWorker
from stream_packet import Packet, PacketType


class Server:
    def __init__(self, ip, port, buffer_size=None):
        if buffer_size is None:
            buffer_size = 4096
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size

    def run(self, args):
        bootstrapper, neighbors, rendezvous, node = args

        # Send message to create the tree if I only have one neighbor
        if node:
            self.start_tree(neighbors)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip, self.port))
        print("DEBUG: Listening on port " + str(self.port) + "...")

        while True:
            request = server_socket.recvfrom(self.buffer_size)
            if self.debug:
                print("DEBUG: Request received")
            ServerWorker(args).run(request[0])

    def start_tree(self, neighbors):
        if len(neighbors) == 1:
            if self.debug:
                print("DEBUG: Sending the packet to create the tree")

            packet_serialized = Packet(self.ip, PacketType.SETUP, [], 0, 0, 0).serialize()
            udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            udp_socket.sendto(packet_serialized, neighbors[0])
            