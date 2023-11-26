import socket
from server.server_worker import ServerWorker
from server.stream_packet import Packet, PacketType


class Server:
    def __init__(self, port, buffer_size=None):
        if buffer_size is None:
            buffer_size = 20480
        self.port = port
        self.buffer_size = buffer_size

    def run(self, ep):

        # Send message to create the tree if I only have one neighbor
        if ep.bootstrapper is None:
            if ep.debug:
                print("DEBUG: Sending the packet to create the tree")
            #self.start_tree(ep)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', self.port))

        if ep.debug:
            print("DEBUG: Listening on port " + str(self.port) + "...")
        #print('Table: ')
        #print(ep.forwarding_table)
        while True:
            request = server_socket.recvfrom(self.buffer_size)
            if ep.debug:
                print("DEBUG: Request received")
            ServerWorker(ep).run(request)

    def start_tree(self, ep):
        if len(ep.neighbours) == 1:
            packet_serialized = Packet('', PacketType.JOIN, 0, 0, 0, []).serialize()
            udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            udp_socket.sendto(packet_serialized, (ep.neighbours[0], self.port))
