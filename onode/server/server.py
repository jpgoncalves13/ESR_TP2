import socket
from server.server_worker import ServerWorker
from server.stream_packet import Packet, PacketType


class Server:
    def __init__(self, port, buffer_size=None):
        if buffer_size is None:
            buffer_size = 4096
        self.port = port
        self.buffer_size = buffer_size

    def run(self, ep):

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', self.port))

        # Send message to create the tree if I only have one neighbor
        if ep.bootstrapper is None and not ep.rendezvous and len(ep.neighbours) == 1:
            if ep.debug:
                print("DEBUG: Sending the packet to create the tree")
            packet_serialized = Packet(PacketType.JOIN, '0.0.0.0', 0, '0.0.0.0').serialize()
            server_socket.sendto(packet_serialized, (ep.neighbours[0], self.port))

        if ep.debug:
            print("DEBUG: Listening on port " + str(self.port) + "...")

        while True:
            request = server_socket.recvfrom(self.buffer_size)
            ServerWorker(ep).run(request)
