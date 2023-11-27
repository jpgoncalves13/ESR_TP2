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
        request_neighbours, node_id = self.ep.get_node_info(address[0])
        packet = Packet(PacketType.RSETUP, '0.0.0.0', node_id if node_id is not None else 0, 0,
                        '0.0.0.0', request_neighbours if request_neighbours is not None else [])
        ServerWorker.send_packet(packet, address)

    def handle_hello(self, address):
        """Neighbour listening"""
        if address[0] in self.ep.get_neighbours():
            self.ep.set_state_of_neighbour(address[0], True)
            packet = Packet(PacketType.ACK, '0.0.0.0', 0, 0, '0.0.0.0')
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

        packet = Packet(PacketType.STREAM, '0.0.0.0', 0, packet.stream_id, '0.0.0.0', packet.payload)
        stream_clients = self.ep.get_stream_clients(packet.stream_id)
        neighbours_to_send = []

        for client in stream_clients:
            if client == self.ep.node_id:
                for c in self.ep.get_clients():
                    if c not in neighbours_to_send:
                        neighbours_to_send.append(c)
            else:
                neighbour = self.ep.get_neighbour_to_client(client)
                if neighbour not in neighbours_to_send:
                    neighbours_to_send.append(neighbour)

        if self.ep.debug:
            print("DEBUG: Packet sent to: " + str(neighbours_to_send))

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours_to_send:
            udp_socket.sendto(packet.serialize(), (neighbour, self.ep.port))
        udp_socket.close()

    def handle_join(self, packet, ip):
        """Handle the join messages to the tree"""

        # Handling logic for border nodes
        if packet.leaf == '0.0.0.0':
            packet.leaf = ip
            packet.node_id = self.ep.node_id

            already_exists = self.ep.add_client(packet.node_id, packet.leaf)
            self.ep.add_client_to_stream(packet.stream_id, packet.node_id)

            if not self.ep.rendezvous and not already_exists:
                neighbour = self.ep.get_neighbour_to_rp()
                if neighbour is not None:
                    ServerWorker.send_packet(packet, (neighbour, self.ep.port))
                else:
                    self.flood_packet(ip, packet.serialize())

        # Handling logic for other nodes
        else:
            self.ep.add_client_to_stream(packet.stream_id, packet.node_id)
            is_first_entry, _ = self.ep.add_entry(packet.node_id, ip, packet.last_hop)
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
            packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, 0, '0.0.0.0', [])
            ServerWorker.send_packet(packet, address)
            return

        best_entries_list = self.ep.get_best_entries()
        best_entries_list = [tup for tup in best_entries_list if tup[1] != address[0]]

        if self.ep.rendezvous:
            # 255 reserved for RP
            best_entries_list.append((255, '0.0.0.0', 0, 0))

        clients = self.ep.get_clients()
        if len(clients) > 0:
            best_entries_list.append((self.ep.node_id, '0.0.0.0', 0, 0))

        packet = Packet(PacketType.RMEASURE, '0.0.0.0', self.ep.node_id, 0, '0.0.0.0',
                        (best_entries_list, clients, self.ep.get_stream_clients()))
        ServerWorker.send_packet(packet, address)

    def handle_request(self, response, address):
        packet = Packet.deserialize(response)

        if self.ep.debug:
            print(f"DEBUG: Processing response to packet: {packet.type}")

        # Normal node
        if self.ep.bootstrapper is None:
            if packet.type == PacketType.HELLO:
                self.handle_hello(address)

            elif packet.type == PacketType.JOIN:
                self.handle_join(packet, address[0])

            elif packet.type == PacketType.MEASURE:
                self.handle_measure(address)

            elif packet.type == PacketType.STREAM:
                self.handle_stream(packet, address[0])

            if self.ep.debug:
                print(self.ep.get_table())
        # Bootstrapper
        else:
            if packet.type == PacketType.SETUP:
                self.handle_setup(address)
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet.type}")
