from threading import Thread
import socket
from server_worker import ServerWorker
from stream_packet import Packet, PacketType


class Server:
    def __init__(self, ip, port, buffer_size=None, debug: bool = None):
        if buffer_size is None:
            buffer_size = 4096
        if debug is None:
            debug = False
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.debug = debug

    def run(self, args):
        bootstrapper, neighbors, rendezvous, node = args

        # Send message to create the tree if I only have one neighbor

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip, self.port))
        print("DEBUG: Listening on port " + str(self.port) + "...")

        while True:
            request = server_socket.recvfrom(self.buffer_size)
            if self.debug:
                print("DEBUG: Request received")
            ServerWorker(args).run(request[0])



        

