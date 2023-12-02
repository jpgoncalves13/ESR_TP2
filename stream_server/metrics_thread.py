import socket
from stream_packet import Packet, PacketType
import threading


class MetricsThread(threading.Thread):

    def __init__(self, port, buffer_size):
        super().__init__()
        self.port = port
        self.buffer_size = buffer_size

    @staticmethod
    def handle_measure(address):
        packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0',
                        ([('0.0.0.0', '0.0.0.0', 0, 0)], None, []))
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(packet.serialize(), address)
        udp_socket.close()

    def run(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.port))

        try:
            while True:
                response, address = udp_socket.recvfrom(self.buffer_size)
                packet = Packet.deserialize(response)
                if packet.type == PacketType.MEASURE:
                    MetricsThread.handle_measure(address)
        finally:
            udp_socket.close()





