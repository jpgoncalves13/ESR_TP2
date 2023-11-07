from threading import Thread
from server.stream_packet import Packet, PacketType
import socket


class ServerWorker:
    def __init__(self, args):
        self.args = args

    def run(self, request):
        Thread(target=lambda: self.handle_request(request)).start()

    def handle_request(self, request):
        bootstrapper, bootstrapper_address, neighbours, is_rendezvous_point, debug = self.args
        packet = Packet.deserialize(request[0])
        
        if debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

        if bootstrapper is None:
            if packet.type == PacketType.RSETUP:
                if debug:
                    print('DEBUG: Response received')
                print(Packet.deserialize(request).destinations)
            else:
                print("EM DESENVOLVIMENTO")
        else:
            if packet.type == PacketType.SETUP:
                if debug:
                    print("DEBUG: Received a request to join the topology")
                request_neighbours = bootstrapper.handle_join_request(request[1])
                packet = Packet('', PacketType.RSETUP, 1, 1, 1, neighbours=request_neighbours)
                socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                socket_s.sendto(packet.serialize(), request[1])
            else:
                if debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet.type}")
