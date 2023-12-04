import time
import calendar
import socket
from server.stream_packet import Packet, PacketType
import threading


class ProbeThread(threading.Thread):

    def __init__(self, ep, interval, timeout, block, port):
        super().__init__()
        self.ep = ep
        self.interval = interval
        self.running = False
        self.port = port
        self.block = block
        self.timeout = timeout

    def handle_neighbours(self, neighbour, last_packet, delay_measured, loss_measured):
        list_metrics, rp_entry = last_packet.payload
        print("LOSS: " + str(loss_measured))
        for leaf, next_hop, delay, loss in list_metrics:
            self.ep.update_metrics(neighbour if leaf == "0.0.0.0" else leaf, neighbour, next_hop,
                                   delay + delay_measured, max(loss, loss_measured))

        if rp_entry is not None and not self.ep.rendezvous:
            rp_ip = rp_entry[0]
            if rp_ip == "0.0.0.0":
                rp_ip = neighbour

            self.ep.update_metrics_rp(rp_ip, neighbour, rp_entry[1], rp_entry[2]
                                      + delay_measured, max(rp_entry[3], loss_measured))

    def handle_neighbours_total_loss(self, neighbour):
        print(str(neighbour) + " is dead")
        self.ep.update_neighbour_death(neighbour)

    def handle_servers(self, server, last_packet, delay_measured, loss_measured):
        list_metrics, rp_entry = last_packet.payload
        for _ in list_metrics:
            self.ep.update_metrics_server(server, delay_measured, int(loss_measured / 2))

    def measure(self, udp_socket, neighbour):
        packets_sent = 0
        packets_received = 0
        total_delay = 0
        packet_serialized = Packet(PacketType.MEASURE, '0.0.0.0', 0, '0.0.0.0').serialize()
        list_packets_received = []

        for _ in range(self.block):
            start_time = time.time()
            udp_socket.sendto(packet_serialized, (neighbour, self.port))
            packets_sent += 1

            try:
                response, _ = udp_socket.recvfrom(4096)
                end_time = time.time()
                packets_received += 1
                list_packets_received.append(Packet.deserialize(response))
                total_delay += (end_time - start_time) * 1000  # ms

            except socket.timeout:
                pass

        loss_measured = int(100 * (packets_sent - packets_received) / packets_sent) if packets_sent > 0 else 0
        delay_measured = int(total_delay / packets_received) if packets_received > 0 else 0

        last_packet = list_packets_received[-1] if len(list_packets_received) > 0 else None

        return loss_measured, delay_measured, last_packet

    def run(self):
        self.running = True
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.settimeout(self.timeout)

        try:
            while self.running:
                neighbours = self.ep.get_listening_neighbours()

                for neighbour in neighbours:
                    loss_measured, delay_measured, last_packet = self.measure(udp_socket, neighbour)
                    if last_packet is not None and last_packet.type == PacketType.RMEASURE:
                        self.handle_neighbours(neighbour, last_packet, delay_measured, loss_measured)
                    else:
                        self.handle_neighbours_total_loss(neighbour)

                if self.ep.rendezvous:
                    servers = self.ep.get_servers()
                    if self.ep.debug:
                        print(f"DEBUG: Sending the probe message to servers {servers}")

                    for server in servers:
                        loss_measured, delay_measured, last_packet = self.measure(udp_socket, server)
                        if last_packet is not None and last_packet.type == PacketType.RMEASURE:
                            self.handle_servers(server, last_packet, delay_measured, loss_measured)

                time.sleep(self.interval)
        finally:
            udp_socket.close()

    def stop(self):
        self.running = False

