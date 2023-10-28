from threading import Thread
from stream_packet import Packet


class ServerWorker:

    def __init__(self, args):
        self.args = args

    def run(self, request):
        Thread(target=self.handle_request(request)).start()

    def handle_request(self, request: bytearray):
        debug, bootstrapper, is_rendezvous_point = self.args
        packet = Packet.deserialize(request)

        if debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

