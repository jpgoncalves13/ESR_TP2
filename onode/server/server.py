import socket
from server.server_worker import ServerWorker
from threading import Thread
from server.stream_packet import Packet, PacketType
from server.probe_thread import ProbeThread


class Server:
    def __init__(self, port, buffer_size=None):
        if buffer_size is None:
            buffer_size = 20480
        self.port = port
        self.buffer_size = buffer_size

    def run(self, ep):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', self.port))

        if ep.debug:
            print("DEBUG: Listening on port " + str(self.port) + "...")

        # Start the proof thread
        probe_thread = ProbeThread(ep, 5, 2, 2, ep.port)
        probe_thread.start()

        while True:
            response, address = server_socket.recvfrom(self.buffer_size)
            ServerWorker(ep).run(response, address)
