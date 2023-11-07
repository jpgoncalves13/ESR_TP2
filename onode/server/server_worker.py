from threading import Thread
from server.stream_packet import Packet, PacketType
from server.shared_state import EP
import socket


class ServerWorker:
    def __init__(self, ep: EP):
        self.ep = ep

    def run(self, request):
        Thread(target=lambda: self.handle_request(request)).start()

    def handle_request(self, request):
        packet = Packet.deserialize(request[0])
        
        if self.ep.debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

        if self.ep.bootstrapper is None:
            if packet.type == PacketType.RSETUP:
                if self.ep.debug:
                    print('DEBUG: Response received')
                print(Packet.deserialize(request).destinations)
            else:
                print("EM DESENVOLVIMENTO")
        else:
            if packet.type == PacketType.SETUP:
                if self.ep.debug:
                    print("DEBUG: Received a request to join the topology")
                request_neighbours = self.ep.bootstrapper.handle_join_request(request[1][0])
                packet = Packet('', PacketType.RSETUP, 1, 1, 1, neighbours=request_neighbours)
                socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                socket_s.sendto(packet.serialize(), request[1])
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet.type}")
