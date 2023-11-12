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

    def flood_packet(self, sender_ip, packet_serialized):
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for neighbour in self.ep.neighbours.pop(sender_ip):
            socket_s.sendto(packet_serialized, (neighbour, self.ep.port))
        socket_s.close()

    def handle_join(self, packet, ip):
        # Only requests from neighbors are responded to
        if ip not in self.ep.get_neighbours():
            return

        # If packet don't have origin, insert
        if packet.origin == '':
            packet.origin = ip

        last_hop = packet.last_hop
        packet.last_hop = ip
        packet.number_of_hops += 1

        first_entry = self.ep.table.add_entry(packet.origin, ip, last_hop)

        if self.ep.rendezvous and first_entry:
            # The first packet to arrive is the best option
            # Send response that this is the path
            socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response = Packet(packet.origin, PacketType.TREEUPD, 0, 0, 0)
            socket_s.sendto(response.serialize(), (ip, self.ep.port))
            socket_s.close()
            return

        if not self.ep.rendezvous and first_entry:
            self.flood_packet(ip, packet.serialize())

    def handle_treeupd(self, packet, ip):
        self.ep.table.add_parent(ip)
        next_hop = self.ep.table.get_next_hop(packet.origin)
        if next_hop is not None:
            socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_s.sendto(packet.serialize(), (next_hop, self.ep.port))
            socket_s.close()

    def handle_measure(self, packet, ip):
        packet.type = PacketType.RMEASURE
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.sendto(packet.serialize(), (ip, self.ep.port))
        socket_s.close()

    def handle_rmeasure(self, packet):
        self.ep.table.update_delay(packet.origin, time.time() - packet.delay)
        self.ep.table.update_packets_received(packet.origin)

    def handle_setup(self, request):
        request_neighbours = self.ep.bootstrapper.handle_join_request(request[1][0])
        packet = Packet('', PacketType.RSETUP, calendar.timegm(time.gmtime()), 1, 1, neighbours=request_neighbours)
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.sendto(packet.serialize(), request[1])
        socket_s.close()

    def handle_ack(self, packet):
        pass

    def handle_stream(self, request):
        pass

    def handle_request(self, request):
        packet = Packet.deserialize(request[0])

        if self.ep.debug:
            print(f"DEBUG: Processing response to packet of type {packet.type}")

        # Normal node
        if self.ep.bootstrapper is None:
            if packet.type == PacketType.JOIN:
                self.handle_join(packet, request[1][0])
            elif packet.type == PacketType.TREEUPD:
                self.handle_treeupd(packet, request[1][0])
            elif packet.type == PacketType.MEASURE:
                self.handle_measure(packet, request[1][0])
            elif packet.type == PacketType.RMEASURE:
                self.handle_rmeasure(packet)
            elif packet.type == PacketType.STREAM:
                self.handle_stream(request)
            elif packet.type == PacketType.ACK:
                self.handle_ack(packet)
            else:
                print("IN DEVELOPMENT")
        # Bootstrapper
        else:
            if packet.type == PacketType.SETUP:
                self.handle_setup(request)
            else:
                if self.ep.debug:
                    print(f"ERROR: I'm only the bootstrapper: {packet.type}")
