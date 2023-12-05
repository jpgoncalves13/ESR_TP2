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

        stream_clients, data = packet.payload
        
        if self.ep.rendezvous:
            stream_clients = self.ep.get_stream_clients(packet.stream_id)
        # stream_clients = self.ep.get_stream_clients(packet.stream_id)
        # neighbours_to_send = []
        neighbours_to_send = {}
        clients_to_send = []

        for client in stream_clients:
            entry = self.ep.get_best_entry(client)
            neighbour = self.ep.get_neighbour_to_client(client)
            if neighbour is not None:
                if client == neighbour:
                    if entry.loss == 100:
                        # Send leave  because client is dead
                        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        leave_packet = Packet(PacketType.LEAVE, client, 0, '0.0.0.0')
                        self.ep.remove_client_from_forwarding_table(client)
                        ServerWorker.send_packet_with_confirmation(udp_socket, leave_packet.serialize(),
                                                                   (self.ep.get_neighbour_to_rp(), self.ep.port))
                    elif client not in clients_to_send:
                        clients_to_send.append(client)

                else:
                    if entry.loss == 100:
                        neighbour = entry.next_hop
                    if neighbour not in neighbours_to_send:
                        # neighbours_to_send.append(neighbour)
                        neighbours_to_send[neighbour] = [client]
                    else:
                        neighbours_to_send[neighbour].append(client)

        if self.ep.debug:
            print("DEBUG: Packet sent to: " + str(neighbours_to_send))
        if self.ep.debug:
            print("DEBUG: Packet sent to: " + str(clients_to_send))

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours_to_send:
            packet.payload = (neighbours_to_send[neighbour], data)
            udp_socket.sendto(packet.serialize(), (neighbour, self.ep.port))
        udp_socket.close()

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for client in clients_to_send:
            packet.payload = ([], data)
            udp_socket.sendto(packet.serialize(), (client, 5001))
        udp_socket.close()

    """
    Handle a join message
    Receives the join packet, and the ip of the sender (a neighbour)
    """
    def handle_join(self, packet, ip):
        """# Handling logic for leaf neighbours nodes
        if packet.leaf = '0.0.0.0':
            packet.leaf = ip"""
        """
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
            udp_socket.close()"""
        
        stream_id = packet.stream_id
        
        if self.ep.check_if_stream_exists(stream_id):
            pass
        else:
            # Add the stream and the neighbour to the state
            self.ep.add_neighbour_to_stream(stream_id, ip)
            
            # Update the information to the top of the tree
            rp_neighbour = self.ep.get_neighbour_to_rp()
            

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
        if self.ep.get_num_neighbours() == 1 and not self.ep.rendezvous:
            packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0',
                            ([('0.0.0.0', '0.0.0.0', 0, 0)] if self.ep.get_client_state() else [], None))
            ServerWorker.send_packet(packet, address)
            return

        if self.ep.rendezvous:
            best_entries_list = []
            rp_entry = ('0.0.0.0', '0.0.0.0', 0, 0)
        else:
            best_entries_list = self.ep.get_best_entries()
            best_entries_list = [tup for tup in best_entries_list if tup[1] != address[0]]
            rp_entry = self.ep.get_best_entry_rp()
            if rp_entry is not None and rp_entry[1] == address[0]:
                rp_entry = None

        packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0',
                        (best_entries_list, rp_entry))
        ServerWorker.send_packet(packet, address)

    """
    Handles the processing of a request
    A request can be of types:
    - Measure;
    - Join;
    - Leave;
    - Stream;
    """
    def handle_request(self, response, address):
        # Deserialize the packet
        packet = Packet.deserialize(response)

        # Debug information
        if self.ep.debug:
            print(f"DEBUG: Processing response to packet: {packet.type}")
            if packet.type is not PacketType.STREAM:
                print(f"DEBUG: Packet: {packet}")
            else:
                print(f"DEBUG: Packet: {packet.payload[0]}")

        # Normal node TODO
        if packet.type == PacketType.HELLO:
            self.handle_hello(address)

        # Join Message (directly from a client or a node)
        elif packet.type == PacketType.JOIN:
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
            print("TREE" + str(self.ep.get_tree()) + "\n")
            if self.ep.rendezvous:
                print("STREAM_TABLE" + str(self.ep.get_stream_table()) + "\n")
