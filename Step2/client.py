from stream_packet import Packet
import socket
from threading import Thread

class Client:
    def __init__(self):
        pass

    def run(self):
        Thread(target=self.request).start()
    
    def request(self):
        print("Insere a video a visualizar:")
        video_name = input()

        packet = Packet("127.0.0.1", [], 1, [], 1, 1, 1)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(packet.serialize(), ("127.0.0.1", 5001))
        


