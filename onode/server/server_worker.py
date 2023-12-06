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

    """
        Handle a setup message
        Receives the setup packet, and the ip of the sender (a overlay node)
        Returns the neighbours of this overlay node
    """
    def handle_setup(self, address):
        """Bootstrapper response"""
        request_neighbours = self.ep.get_node_info(address[0])
        packet = Packet(PacketType.RSETUP, '0.0.0.0', 0, '0.0.0.0',
                        request_neighbours if request_neighbours is not None else [])
        ServerWorker.send_packet(packet, address)

    """
        Handle a stream message
        Receives the stream packet, and the ip of the sender (a neighbour)
        Redirects to all the neighbours requesting that stream_id
    """
    def handle_stream(self, packet, ip):
        if self.ep.rendezvous:
            self.ep.add_server_to_stream(packet.stream_id, ip)
        if self.ep.rendezvous and not self.ep.its_best_server(packet.stream_id, ip):
            return

        neighbours = self.ep.get_stream_neighbours(packet.stream_id)

        if self.ep.debug:
            print(f"DEBUG: Stream packet sent to: {neighbours}")

        if self.ep.get_client_state() and packet.stream_id == self.ep.client_stream_id:
            self.ep.add_packet_to_buffer(packet.payload)

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in neighbours:
            udp_socket.sendto(packet.serialize(), (neighbour, self.ep.port))
        udp_socket.close()

    """
    Handle a join message
    Receives the join packet, and the ip of the sender (a neighbour) 
    """
    def handle_join(self, packet, ip):
        stream_id = packet.stream_id

        if self.ep.rendezvous:
            self.ep.add_neighbour_to_stream(stream_id, ip)
            return

        if not self.ep.check_if_stream_exists(stream_id):
            # Add the stream and the neighbour to the state
            self.ep.add_neighbour_to_stream(stream_id, ip)

            # Update the information to the top of the tree
            neighbour_to_rp = self.ep.get_neighbour_to_rp()

            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(5)

            if neighbour_to_rp is not None:
                ServerWorker.send_packet_with_confirmation(udp_socket, packet.serialize(),
                                                           (neighbour_to_rp, self.ep.port))

            udp_socket.close()
        else:
            # Add the stream and the neighbour to the state
            self.ep.add_neighbour_to_stream(stream_id, ip)

    """
    Handle a leave message
    Receives the leave packet, and the ip of the sender (a neighbour)
    """
    def handle_leave(self, packet, ip):
        stream_id = packet.stream_id

        if self.ep.check_if_stream_exists(stream_id) and self.ep.rendezvous:
            is_last_neighbour_from_stream = self.ep.remove_neighbour_from_stream(stream_id, ip)
            if is_last_neighbour_from_stream and not self.ep.check_if_server_exists(stream_id):
                self.ep.remove_stream(stream_id)
            return

        if self.ep.check_if_stream_exists(stream_id):
            # Remove the neighbour from the set of neighbours of that stream
            is_last_neighbour_from_stream = self.ep.remove_neighbour_from_stream(stream_id, ip)

            if is_last_neighbour_from_stream:
                self.ep.remove_stream(stream_id)
                # Update the information to the top of the tree
                neighbour_to_rp = self.ep.get_neighbour_to_rp()
                
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp_socket.settimeout(5)

                if neighbour_to_rp is not None:
                    ServerWorker.send_packet_with_confirmation(udp_socket, packet.serialize(),
                                                               (neighbour_to_rp, self.ep.port))

                udp_socket.close()

    """
        Handle a measure message
    """
    def handle_measure(self, address):
        """Handle the packets requesting the metrics"""

        # self.ep.add_neighbour(address[0])

        if self.ep.rendezvous:
            neighbours = []
            rp_entry = (0, 0)
        else:
            rp_entry = self.ep.get_best_entry_rp()
            neighbours = self.ep.get_neighbours_to_rp()
            neighbours = [neighbour for neighbour in neighbours if neighbour != address[0]]
            if rp_entry is not None and rp_entry[0] == address[0]:
                rp_entry = self.ep.get_best_entry_neighbour_rp(address[0])
            elif rp_entry is not None:
                rp_entry = (rp_entry[1], rp_entry[2])

        packet = Packet(PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0',
                        (rp_entry, neighbours))
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
            print("## " + (str(self.ep.tag)) + " ## " + f" DEBUG: Processing response to packet: {packet.type} from {str(address)}")

        # Join Message (directly from a client or a node)
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
            print("STREAM_TABLE" + str(self.ep.get_stream_table()))
            print("RP_TABLE" + str(self.ep.get_table_rp()))
            print("ROUTE TO RP: " + str(self.ep.get_neighbour_to_rp()))

