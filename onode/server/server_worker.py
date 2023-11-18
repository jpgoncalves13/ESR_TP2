from threading import Thread
from server.stream_packet import Packet, PacketType
from server.shared_state import EP
from probe_thread import ProbeThread
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
            packet = Packet(PacketType.ACK, '0.0.0.0', '', 0, '0.0.0.0')
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
            packet = Packet(PacketType.JOIN, '0.0.0.0', '', 0, '0.0.0.0')
            ServerWorker.send_packet(packet, (self.ep.neighbours[0], self.ep.port))
        # This will be updated

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
            best_entries_list += ("RP", "RP", 0, 0)
        packet = Packet(PacketType.RMEASURE, '0.0.0.0', '', '0.0.0.0', best_entries_list)
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
                if len(self.ep.get_neighbours()) > 1:
                    # Start the proof thread only for the nodes not in tree leaves
                    # The messages only start when the table has entries, because we can have
                    # neighbours not listening
                    probe_thread = ProbeThread(self.ep, 20, 5, 10, self.ep.port)
                    probe_thread.start()

            elif packet.type == PacketType.MEASURE:
                self.handle_measure(address)
        # Bootstrapper
        else:
            if packet.type == PacketType.SETUP:
                self.handle_setup(address)
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet}")




