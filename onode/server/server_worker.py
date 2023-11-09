from threading import Thread
from server.stream_packet import Packet, PacketType
from server.shared_state import EP
import socket
import time
import calendar


class ServerWorker:
    def __init__(self, ep: EP):
        self.ep = ep

    def run(self, request):
        Thread(target=lambda: self.handle_request(request)).start()

    def handle_join(self, packet):
        pass

    def handle_measure(self, packet, ip):
        packet.type = PacketType.RMEASURE
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.sendto(packet.serialize(), (ip, self.ep.port))

    def handle_rmeasure(self, packet):
        self.ep.table.update_delay(packet.origin, time.time() - packet.delay)
        self.ep.table.update_packets_received(packet.origin)

    def handle_setup(self, request):
        request_neighbours = self.ep.bootstrapper.handle_join_request(request[1][0])
        packet = Packet('', PacketType.RSETUP, calendar.timegm(time.gmtime()), 1, 1, neighbours=request_neighbours)
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.sendto(packet.serialize(), request[1])
        socket_s.close()

    def handle_stream(self, request):
        pass

    def handle_request(self, request):
        packet = Packet.deserialize(request[0])

        if self.ep.debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

        if self.ep.bootstrapper is None:
            if packet.type == PacketType.JOIN:
                self.handle_join(packet)
            elif packet.type == PacketType.MEASURE:
                self.handle_measure(packet, request[1][0])
            elif packet.type == PacketType.RMEASURE:
                self.handle_rmeasure(packet)
            elif packet.type == PacketType.STREAM:
                self.handle_stream(request)
            else:
                print("EM DESENVOLVIMENTO")
        else:
            if packet.type == PacketType.SETUP:
                self.handle_setup(request)
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet.type}")
