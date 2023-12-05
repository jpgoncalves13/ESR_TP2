from threading import Thread
from server.stream_packet import Packet, PacketType
from server.shared_state import EP
import socket


class ServerWorker:
    def __init__(self, ep: EP):
        self.ep = ep

    def run(self, request, address):
        Thread(target=lambda: self.handle_request(request, address)).start()

    @staticmethod
    def send_packet(packet, address):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp_socket.sendto(packet.serialize(), address)
        except (socket.error, OSError) as e:
            print(f"Error sending the data: {e}")
        finally:
            udp_socket.close()

    @staticmethod
    def send_packet_with_confirmation(udp_socket, packet_serialized, address):
        response = False
        retries = 0
        num_retries = 4
        while not response and retries < num_retries:
            udp_socket.sendto(packet_serialized, address)
            try:
                resp, _ = udp_socket.recvfrom(4096)
                resp_packet = Packet.deserialize(resp)
                if resp_packet.type == PacketType.ACK:
                    response = True
            except socket.timeout:
                retries += 1

    def handle_setup(self, address):
        """Bootstrapper response"""
        request_neighbours = self.ep.get_node_info(address[0])
        packet = Packet(PacketType.RSETUP, '0.0.0.0', 0, '0.0.0.0',
                        request_neighbours if request_neighbours is not None else [])
        ServerWorker.send_packet(packet, address)
    """
    def flood_packet(self, sender_ip, packet_serialized):
        neighbours = self.ep.get_listening_neighbours()
        if sender_ip in neighbours:
            neighbours.remove(sender_ip)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours:
            udp_socket.sendto(packet_serialized, (neighbour, self.ep.port))
        udp_socket.close()
    """

    def handle_stream(self, packet, ip):
        if self.ep.rendezvous:
            self.ep.add_server_to_stream(packet.stream_id, ip)
        if self.ep.rendezvous and not self.ep.its_best_server(packet.stream_id, ip):
            return

        neighbours = self.ep.get_stream_neighbours(packet.stream_id)

        if self.ep.debug:
            print(f"DEBUG: Stream packet sent to: {neighbours}")

        if self.ep.client_on:
            # Update the client video
            pass

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours:
            udp_socket.sendto(packet.serialize(), (neighbour, self.ep.port))
        udp_socket.close()

    def handle_join(self, packet, ip):
        """Handle the join messages to the tree"""

        # Handling logic for leaf neighbours nodes
        if packet.leaf == '0.0.0.0':
            packet.leaf = ip

        if self.ep.rendezvous:
            self.ep.add_client_to_stream(packet.stream_id, packet.leaf)
        is_first_entry = self.ep.add_entry(packet.leaf, ip, packet.last_hop)
        packet.last_hop = ip

        if not self.ep.rendezvous and is_first_entry:
            neighbour = self.ep.get_neighbour_to_rp()
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(5)

            if neighbour is not None:
                ServerWorker.send_packet_with_confirmation(udp_socket, packet.serialize(), (neighbour, self.ep.port))
            else:
                neighbours = self.ep.get_listening_neighbours()
                if ip in neighbours:
                    neighbours.remove(ip)
                for neighbour in neighbours:
                    ServerWorker.send_packet_with_confirmation(udp_socket, packet.serialize(),
                                                               (neighbour, self.ep.port))
            udp_socket.close()

    def handle_leave(self, packet, ip):
        """Handle the client leave message to the tree"""
        
        # Handling logic for leaf neighbours nodes
        if packet.leaf == '0.0.0.0':
            packet.leaf = ip
            
        if not self.ep.rendezvous:
            neighbour = self.ep.get_neighbour_to_rp()
            ServerWorker.send_packet(packet, (neighbour, self.ep.port))

        if self.ep.rendezvous:
            self.ep.remove_client_from_stream(packet.leaf)

        self.ep.remove_client_from_forwarding_table(packet.leaf)

    def handle_measure(self, address):
        """Handle the packets requesting the metrics"""

        if self.ep.rendezvous:
            neighbours = []
            rp_entry = ('0.0.0.0', '0.0.0.0', 0, 0)
        else:
            rp_entry = self.ep.get_best_entry_rp()
            # UPDATE THIS
            neighbours = []
            if rp_entry is not None and rp_entry[1] == address[0]:
                rp_entry = None

        packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0',
                        (rp_entry, neighbours))
        ServerWorker.send_packet(packet, address)

    def handle_request(self, response, address):
        packet = Packet.deserialize(response)

        if self.ep.debug:
            print(f"DEBUG: Processing response to packet: {packet.type}")
            if packet.type is not PacketType.STREAM:
                print(f"DEBUG: Packet: {packet}")
            else:
                print(f"DEBUG: Packet: {packet.payload[0]}")

        # Normal node
        if packet.type == PacketType.JOIN:
            ServerWorker.send_packet(Packet(PacketType.ACK, '0.0.0.0', 0, '0.0.0.0'), address)
            self.handle_join(packet, address[0])

        elif packet.type == PacketType.MEASURE:
            self.handle_measure(address)

        elif packet.type == PacketType.STREAM:
            self.handle_stream(packet, address[0])

        elif packet.type == PacketType.LEAVE:
            ServerWorker.send_packet(Packet(PacketType.ACK, '0.0.0.0', 0, '0.0.0.0'), address)
            self.handle_leave(packet, address[0])

        # Bootstrapper
        elif packet.type == PacketType.SETUP and self.ep.bootstrapper is not None:
            self.handle_setup(address)

        if self.ep.debug:
            print((self.ep.tag if self.ep.tag is not None else "") + " CLIENTS_TABLE" + str(self.ep.get_table()) + "\n")
            print("RP_TABLE" + str(self.ep.get_table_rp()) + "\n")
            print("STREAM_TABLE" + str(self.ep.get_stream_table()) + "\n")
