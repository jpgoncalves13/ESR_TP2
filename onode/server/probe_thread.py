import time
import calendar
import socket
from server.stream_packet import Packet, PacketType
import threading


class ProbeThread(threading.Thread):

    def __init__(self, state, interval, timeout, block, port):
        super().__init__()
        self.state = state
        self.interval = interval
        self.running = False
        self.port = port
        self.block = block
        self.timeout = timeout

    def handle_neighbour_response(self, neighbour, packet, delay, loss):
        rp_entry, neighbours = packet.payload

        if rp_entry is not None and not self.state.rendezvous:
            rp_ip = rp_entry[0]
            if rp_ip == '0.0.0.0':
                rp_ip = neighbour

            # Change function because this is rp only
            print("RP_ENTRY: ", rp_entry)
            print("LOSS: ", loss)
            self.state.update_metrics_rp(rp_ip, neighbour, rp_entry[1] + delay, max(rp_entry[2], loss))
            self.state.add_next_steps(neighbour, neighbours)

    def handle_neighbour_death(self, neighbour):
        self.state.update_neighbour_death(neighbour)

    def handle_servers(self, server, packet, delay, loss):
        _, list_metrics = packet.payload
        for _ in list_metrics:
            self.state.update_metrics_server(server, delay, loss)

    def measure(self, neighbour):
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.settimeout(self.timeout)

        packets_sent = 0
        packets_received = 0
        total_delay = 0
        packet_serialized = Packet(PacketType.MEASURE, '0.0.0.0', 0, '0.0.0.0').serialize()
        list_packets_received = []

        for _ in range(self.block):
            start_time = time.time()
            print("Sent")
            udp_socket.sendto(packet_serialized, (neighbour, self.port))
            packets_sent += 1

            try:
                response, _ = udp_socket.recvfrom(4096)
                print("received")
                end_time = time.time()
                packets_received += 1
                list_packets_received.append(Packet.deserialize(response))
                total_delay += (end_time - start_time) * 1000  # ms

            except socket.timeout:
                print("timeout")

        udp_socket.close()

        loss_measured = int(100 * (packets_sent - packets_received) / packets_sent) if packets_sent > 0 else 0
        delay_measured = int(total_delay / packets_received) if packets_received > 0 else 0

        last_packet = list_packets_received[-1] if len(list_packets_received) > 0 else None

        return loss_measured, delay_measured, last_packet

    def run(self):
        self.running = True

        while self.running:
            neighbours = self.state.get_neighbours()

            if self.state.debug:
                print(f"DEBUG: Sending the probe message to: {neighbours}")

            for neighbour in neighbours:
                loss_measured, delay_measured, last_packet = self.measure(neighbour)
                if last_packet is not None and last_packet.type == PacketType.RMEASURE:
                    self.handle_neighbour_response(neighbour, last_packet, delay_measured, loss_measured)
                else:
                    pass
                    # Send join to the neighbours of the neighbour if i do not have other option
                    #self.handle_neighbour_death(neighbour)

            if self.state.rendezvous:
                servers = self.state.get_servers()
                if self.state.debug:
                    print(f"DEBUG: Sending the probe message to servers {servers}")

                for server in servers:
                    loss_measured, delay_measured, last_packet = self.measure(server)
                    if last_packet is not None and last_packet.type == PacketType.RMEASURE:
                        self.handle_servers(server, last_packet, delay_measured, loss_measured)
                    else:
                        self.state.remove_server_from_stream(server)

            time.sleep(self.interval)

    def stop(self):
        self.running = False
