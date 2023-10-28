from threading import Thread
import socket
from server_worker import ServerWorker


class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.buffer_size = 4096

    def run(self, args):
        # Request bootstrapper neighbors

        # Send message to create the tree if I only have one neighbor

        debug, _, _ = args
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip, self.port))
        print("DEBUG: Listening")

        while True:
            request = server_socket.recvfrom(self.buffer_size)
            if debug:
                print("DEBUG: Request received")
            ServerWorker(args).run(request[0])
