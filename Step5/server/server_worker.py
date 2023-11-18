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
        print("Recebi mensagem do " + str(request[1]))
        packet = Packet('', PacketType.RSETUP, calendar.timegm(time.gmtime()), 1, 1, neighbours=request_neighbours)
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.sendto(packet.serialize(), request[1])
        socket_s.close()

    def handle_unsubscribe(self, packet, ip):
        stream_id = packet.origin
        self.ep.stream_table.remove_client_from_stream(stream_id, ip)

        if self.ep.stream_table.consult_entry() == None and self.ep.forwarding_table.parents:
            packet = Packet(stream_id, PacketType.UNSUBSCRIBE, 0, 0, 0)
            parent = self.ep.forwarding_table.parents[0]
            socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_s.sendto(packet.serialize(), (parent, self.ep.port))
            socket_s.close()

    def handle_stream(self, packet, ip):
        print("Recebi stream do " + ip)
        payload = packet.payload # Dados da Stream encapsulados em RTP
        stream_id = packet.origin
        stream_servers = self.ep.stream_table.consult_entry_servers(stream_id)
        
        if ip not in stream_servers:
            self.ep.stream_table.add_server_to_stream(stream_id, ip)
            
        stream_servers = self.ep.stream_table.consult_entry_servers(stream_id)

        if ip == stream_servers[0]:
            packet = Packet(packet.origin, PacketType.STREAM, 0, 0, 0, payload=payload) # Estou a considerar o campo origin como o indentificador da STREAM
            
            stream_clients = self.ep.stream_table.consult_entry_clients(packet.origin) # Obter os clientes que estão a pedir a stream
            for client in stream_clients:
                print((client, self.ep.port))
                socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                socket_s.sendto(packet.serialize(), (client, self.ep.port))
                socket_s.close()

    def handle_stream_request(self, packet, ip):
        stream_id = packet.origin # Estou a considerar o campo origin como o indentificador da STREAM
        if self.ep.stream_table.consult_stream(stream_id) == False:
            # Caso a stream não esteja já a ser servida, reencaminha para cima na árvore
            self.ep.stream_table.add_stream_entry(stream_id, [ip])
            packet = Packet(stream_id, PacketType.STREAMREQ, 0, 0, 0)
            parent = self.ep.forwarding_table.parents[0]
            socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_s.sendto(packet.serialize(), (parent, self.ep.port))
            socket_s.close()
        else: 
            # Caso a stream já esteja a ser servida não reencaminha para cima na árvore
            pass # Não faz nada -> espera que o RP envie a stream

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
                self.handle_stream(packet, request[1][0])
            else:
                print("EM DESENVOLVIMENTO")
        else:
            if packet.type == PacketType.SETUP:
                self.handle_setup(request)
            #elif packet.type == PacketType.STREAM:
            #    self.handle_stream(packet)
            #elif packet.type == PacketType.STREAMREQ:
            #    self.handle_stream_request(packet, request[1][0]) # Enviamos também o ip do emissor
            #elif packet.type == PacketType.UNSUBSCRIBE:
            #    self.handle_unsubscribe(packet, request[1][0])
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet.type}")
