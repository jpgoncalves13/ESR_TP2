from threading import Thread
from server.stream_packet import Packet, PacketType
from server.shared_state import EP
from server.probe_thread import ProbeThread
import socket


class ServerWorker:
    def __init__(self, ep: EP):
        self.ep = ep

    def run(self, request, address):
        Thread(target=lambda: self.handle_request(request, address)).start()

    @staticmethod
    def send_packet(packet, address):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(packet.serialize(), address)
        udp_socket.close()

    def handle_setup(self, address):
        """Bootstrapper response"""
        request_neighbours, node_id = self.ep.handle_join_request(address[0])
        packet = Packet(PacketType.RSETUP, '0.0.0.0', node_id, 0, '0.0.0.0', request_neighbours)
        ServerWorker.send_packet(packet, address)

    def handle_hello(self, address):
        """Neighbour listening"""
        if address[0] in self.ep.get_neighbours():
            self.ep.set_state_of_neighbour(address[0], True)
            packet = Packet(PacketType.ACK, '0.0.0.0', 0, 0, '0.0.0.0')
            ServerWorker.send_packet(packet, address)

    def flood_packet(self, sender_ip, packet_serialized):
        """Send a packet to all listening neighbours, except the one that sent the packet"""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        neighbours = self.ep.get_listening_neighbours()
        neighbours.remove(sender_ip)
        for neighbour in neighbours:
            udp_socket.sendto(packet_serialized, (neighbour, self.ep.port))
        udp_socket.close()

    def handle_stream_request(self, packet):
        """Send message to create the tree if I only have one neighbor"""
        if self.ep.bootstrapper is None and not self.ep.rendezvous and len(self.ep.get_neighbours()) == 1:
            if self.ep.debug:
                print("DEBUG: Sending the packet to create the tree")
            packet = Packet(PacketType.JOIN, '0.0.0.0', 0, 0, '0.0.0.0')
            ServerWorker.send_packet(packet, (self.ep.get_neighbours()[0], self.ep.port))
        # This will be updated
    
    def handle_stream(self, packet, ip):
        payload = packet.payload # Dados da Stream encapsulados em RTP
        stream_id = packet.stream_id
        stream_servers = self.ep.stream_table.consult_entry_servers(stream_id)
        
        
        if ip not in stream_servers:
            self.ep.stream_table.add_server_to_stream(stream_id, ip)
            
        stream_servers = self.ep.stream_table.consult_entry_servers(stream_id)
        
        if ip == stream_servers[0]:
            packet = Packet(PacketType.STREAM, 0, 0, stream_id, 0, payload=payload) # Estou a considerar o campo origin como o indentificador da STREAM
            
            stream_clients = self.ep.stream_table.consult_entry_clients(stream_id) # Obter os clientes que estão a pedir a stream
            next_hops = []
            for client in stream_clients:
                next_hop = self.ep.forwarding_table.get_best_entry(client)
                if next_hop not in next_hops:
                    next_hops.append(next_hop)
            
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for next_hop in next_hops:    
                udp_socket.sendto(packet.serialize(), (next_hop, self.ep.port))
            
            udp_socket.close()

    def handle_join(self, packet, ip):
        if packet.leaf == '0.0.0.0':
            packet.leaf = ip
            packet.last_hop = ip
            packet.node_id = self.ep.node_id

        next_hop = packet.last_hop
        packet.last_hop = ip

        is_first_entry, already_exists = self.ep.add_entry(packet.node_id, ip, next_hop)

        if self.ep.rendezvous:
            if is_first_entry:
                # Start the stream transmission
                pass
            return

        if is_first_entry:
            neighbour = self.ep.get_neighbour_to_rp()
            if neighbour is not None:
                ServerWorker.send_packet(packet, (neighbour, self.ep.port))
            else:
                self.flood_packet(ip, packet.serialize())

    def handle_measure(self, address):
        best_entries_list = self.ep.get_best_entries()
        if self.ep.rendezvous:
            # 255 reserved for RP
            best_entries_list.append((255, "0.0.0.0", 0, 0))
        if len(self.ep.get_neighbours()) == 1 and not self.ep.rendezvous:
            best_entries_list = []

        if self.ep.debug:
            print("DEBUG: " + str(best_entries_list))

        packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, 0, '0.0.0.0', best_entries_list)
        ServerWorker.send_packet(packet, address)

    def handle_request(self, response, address):
        packet = Packet.deserialize(response)

        if self.ep.debug:
            print(f"DEBUG: Processing response to packet: {packet}")

        # Normal node
        if self.ep.bootstrapper is None:
            if packet.type == PacketType.HELLO:
                self.handle_hello(address)

            elif packet.type == PacketType.STREAMREQ:
                self.handle_stream_request(packet)

            elif packet.type == PacketType.JOIN:
                self.handle_join(packet, address[0])

            elif packet.type == PacketType.MEASURE:
                self.handle_measure(address)

            if self.ep.debug:
                print("DEBUG:")
                print(self.ep.get_table())
        # Bootstrapper
        else:
            if packet.type == PacketType.SETUP:
                self.handle_setup(address)
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet}")




