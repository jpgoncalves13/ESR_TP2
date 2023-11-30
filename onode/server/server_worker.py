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
        request_neighbours = self.ep.get_node_info(address[0])
        packet = Packet(PacketType.RSETUP, '0.0.0.0', 0, '0.0.0.0',
                        request_neighbours if request_neighbours is not None else [])
        ServerWorker.send_packet(packet, address)

    def handle_hello(self, address):
        """Neighbour listening"""
        if address[0] in self.ep.get_neighbours():
            self.ep.set_state_of_neighbour(address[0], True)
            packet = Packet(PacketType.ACK, '0.0.0.0', 0, '0.0.0.0')
            ServerWorker.send_packet(packet, address)

    def flood_packet(self, sender_ip, packet_serialized):
        """Send a packet to all listening neighbours, except the one that sent the packet"""
        neighbours = self.ep.get_listening_neighbours()
        if sender_ip in neighbours:
            neighbours.remove(sender_ip)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours:
            udp_socket.sendto(packet_serialized, (neighbour, self.ep.port))
        udp_socket.close()

    def handle_stream(self, packet, ip):
        if self.ep.rendezvous:
            self.ep.add_server_to_stream(packet.stream_id, ip)
        if self.ep.rendezvous and not self.ep.its_best_server(packet.stream_id, ip):
            return

        packet = Packet(PacketType.STREAM, '0.0.0.0', packet.stream_id, '0.0.0.0', packet.payload)
        stream_clients = self.ep.get_stream_clients(packet.stream_id)
        neighbours_to_send = []
        clients_to_send = []

        for client in stream_clients:
            neighbour = self.ep.get_neighbour_to_client(client)
            if client == neighbour:
                if client not in clients_to_send:
                    clients_to_send.append(client)
            else:
                if neighbour not in neighbours_to_send:
                    neighbours_to_send.append(neighbour)

        if self.ep.debug:
            print("DEBUG: Packet sent to: " + str(neighbours_to_send))
        if self.ep.debug:
            print("DEBUG: Packet sent to: " + str(clients_to_send))

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours_to_send:
            udp_socket.sendto(packet.serialize(), (neighbour, self.ep.port))
        udp_socket.close()

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for client in clients_to_send:
            udp_socket.sendto(packet.serialize(), (client, 5001))
        udp_socket.close()

    def handle_join(self, packet, ip):
        """Handle the join messages to the tree"""

        # Handling logic for leaf neighbours nodes
        if packet.leaf == '0.0.0.0':
            packet.leaf = ip

        self.ep.add_client_to_stream(packet.stream_id, packet.leaf)
        is_first_entry, _ = self.ep.add_entry(packet.leaf, ip, packet.last_hop)
        packet.last_hop = ip

        if not self.ep.rendezvous and is_first_entry:
            neighbour = self.ep.get_neighbour_to_rp()
            if neighbour is not None:
                ServerWorker.send_packet(packet, (neighbour, self.ep.port))
            else:
                self.flood_packet(ip, packet.serialize())

    def handle_measure(self, address):
        """Handle the packets requesting the metrics"""
        if self.ep.get_num_neighbours() == 1 and not self.ep.rendezvous:
            packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0', ([], []))
            ServerWorker.send_packet(packet, address)
            return

        best_entries_list = self.ep.get_best_entries()
        best_entries_list = [tup for tup in best_entries_list if tup[1] != address[0]]

        if self.ep.rendezvous:
            # 255 reserved for RP
            best_entries_list.append((255, '0.0.0.0', 0, 0))

        packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0',
                        (best_entries_list, self.ep.get_stream_table_info()))
        ServerWorker.send_packet(packet, address)

    def handle_stream_request(self):
        if self.ep.get_num_neighbours() == 1:
            packet = Packet(PacketType.JOIN, '0.0.0.0', 0, '0.0.0.0')
            ServerWorker.send_packet(packet, (self.ep.get_neighbours()[0], self.ep.port))

    def handle_request(self, response, address):
        packet = Packet.deserialize(response)

        if self.ep.debug:
            print(f"DEBUG: Processing response to packet: {packet.type}")

        # Normal node
        if packet.type == PacketType.HELLO:
            self.handle_hello(address)

        elif packet.type == PacketType.JOIN:
            self.handle_join(packet, address[0])

        elif packet.type == PacketType.MEASURE:
            self.handle_measure(address)

        elif packet.type == PacketType.STREAM:
            self.handle_stream(packet, address[0])

        elif packet.type == PacketType.STREAMREQ:
            self.handle_stream_request()

        # Bootstrapper
        elif packet.type == PacketType.SETUP and self.ep.bootstrapper is not None:
            self.handle_setup(address)

        if self.ep.debug:
            print(self.ep.get_table())
