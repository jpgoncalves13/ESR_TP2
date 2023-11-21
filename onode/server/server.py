import socket
from server.server_worker import ServerWorker
from threading import Thread
from server.stream_packet import Packet, PacketType
from server.probe_thread import ProbeThread


class Server:
    def __init__(self, port, buffer_size=None):
        if buffer_size is None:
            buffer_size = 4096
        self.port = port
        self.buffer_size = buffer_size

    def send_hello(self, ep, timeout):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(timeout)
        try:
            packet = Packet(PacketType.HELLO, '0.0.0.0', 0, 0, '0.0.0.0').serialize()
            for neighbour in ep.get_neighbours():
                udp_socket.sendto(packet, (neighbour, self.port))
                try:
                    response, address = udp_socket.recvfrom(self.buffer_size)
                    response_packet = Packet.deserialize(bytearray(response))
                    if response_packet.type == PacketType.ACK and address[0] == neighbour:
                        ep.set_state_of_neighbour(neighbour, True)
                except socket.timeout:
                    pass
        finally:
            udp_socket.close()

    def run(self, ep):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', self.port))

        if ep.debug:
            print("DEBUG: Listening on port " + str(self.port) + "...")

        if ep.bootstrapper is None:
            if ep.debug:
                print("DEBUG: Sending hello to neighbours")
            Thread(target=lambda: self.send_hello(ep, 5)).start()

        if ep.bootstrapper is None and len(ep.get_neighbours()) > 1:
            # Start the proof thread only for the nodes not in tree leaves
            # The messages only start when the table has entries, because we can have
            # neighbours not listening
            probe_thread = ProbeThread(ep, 5, 2, 2, ep.port)
            probe_thread.start()

        while True:
            response, address = server_socket.recvfrom(self.buffer_size)
            ServerWorker(ep).run(response, address)
