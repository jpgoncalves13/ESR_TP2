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

    def run(self):
        self.running = True
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.settimeout(self.timeout)

        try:
            while self.running:
                if self.ep.debug:
                    print("DEBUG: Sending the probe message to neighbours")

                neighbours = self.ep.get_neighbours_to_request()
                for neighbour in neighbours:

                    packets_sent = 0
                    packets_received = 0
                    total_delay = 0
                    packet_serialized = Packet(PacketType.MEASURE, '0.0.0.0', '', 0, '0.0.0.0')
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

                    loss_measured = 100 * (packets_sent - packets_received) / packets_sent if packets_sent > 0 else 0
                    delay_measured = total_delay / packets_received if packets_received > 0 else 0

                    if packets_received > 0:
                        last_packet = list_packets_received[-1]
                        if last_packet.type == PacketType.RMEASURE:
                            list_metrics = last_packet.payload
                            for leaf, next_hop, delay, loss in list_metrics:
                                self.ep.update_metrics(leaf, neighbour, next_hop,
                                                       delay + delay_measured, (loss + loss_measured)/2)

                time.sleep(self.interval)
        finally:
            udp_socket.close()

    def stop(self):
        self.running = False

