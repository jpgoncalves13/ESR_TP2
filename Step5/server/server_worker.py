from threading import Thread
from server.stream_packet import Packet, PacketType
import socket


class ServerWorker:
    def __init__(self, args):
        self.args = args

    def run(self, request):
        Thread(target=lambda: self.handle_request(request)).start()

    def handle_request(self, request):
        bootstrapper, bootstrapper_address, neighbours, is_rendezvous_point, node, debug = self.args
        packet = Packet.deserialize(request[0])
        
        if debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

        if packet.type == PacketType.SETUP:
            if debug:
                print("DEBUG: Received a request to join the topology")
            if bootstrapper is not None:
                request_neighbours = bootstrapper.handle_join_request(packet.origin)
                packet = Packet(packet.origin, PacketType.RSETUP, 1, 1, 1, neighbours=request_neighbours)
                socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                socket_s.sendto(packet.serialize(), request[1])
            else:
                if debug:
                    print("ERROR: Bootstrapper is not running")
        elif packet.type == PacketType.RSETUP:
            if debug:
                print('DEBUG: Response received')
            print(Packet.deserialize(request).destinations)
        elif packet.type == PacketType.STREAM:
            if debug:
                print("DEBUG: Received a stream packet")
            
            # Aceder ao estado partilhado e verificar quais os servidores que estão a pedir a stream enviada
            # Enviar a stream para o(s) próximo(s) nó(s) da árvore
            #     Caso o próximo nó é cliente -> enviar diretamente para o cliente
            #     Caso o próximo nó é servidor -> minimizar número de pacotes enviados 
            #          (dois clientes acessíveis pelo mesmo link -> enviar apenas um pacote)
