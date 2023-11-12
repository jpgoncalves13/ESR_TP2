import time
import calendar
import socket
from server.stream_packet import Packet, PacketType
import threading


class ProbeThread(threading.Thread):

    def __init__(self, ep, interval, port):
        super().__init__()
        self.ep = ep
        self.interval = interval
        self.running = False
        self.port = port

    def run(self):
        self.running = True
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        while self.running:
            if self.ep.debug:
                print("DEBUG: Sending the probe message to neighbours")
            #for neighbour in self.ep.get_neighbours():
                # Update this in the future to do not ask off nodes
            #    self.send_probe_message(neighbour, udp_socket)
            time.sleep(self.interval)

        udp_socket.close()

    def stop(self):
        self.running = False

    def send_probe_message(self, neighbour_ip, udp_socket):
        packet_serialized = Packet(neighbour_ip, PacketType.MEASURE, calendar.timegm(time.gmtime()), 0, 0).serialize()
        udp_socket.sendto(packet_serialized, (neighbour_ip, self.port))
        # Table update
        self.ep.table.update_packets_sent(neighbour_ip)
