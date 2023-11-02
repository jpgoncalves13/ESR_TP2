from threading import Thread
from stream_packet import Packet, PacketType
import socket


class ServerWorker:
    def __init__(self, args):
        self.args = args

    def run(self, request):
        Thread(target=lambda: self.handle_request(request)).start()

    def handle_request(self, request: bytearray):
        debug, bootstrapper, is_rendezvous_point, server_files = self.args
        packet = Packet.deserialize(request)
        
        if debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

        match packet.type:
            case PacketType.SETUP:
                if debug:
                    print("DEBUG: Received a request to join the topology")
                if bootstrapper is not None:
                    neighbours = bootstrapper.handle_join_request(packet.origin)
                    packet = Packet(packet.origin, neighbours, PacketType.RSETUP, [], 1, 1, 1)
                    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    socket_s.sendto(packet.serialize(), (packet.origin, 5000))
                else:
                    if debug:
                        print("ERROR: Bootstrapper is not running")
            case PacketType.RSETUP:
                if debug:
                    print('DEBUG: Response received')
                print(Packet.deserialize(request).destinations)

