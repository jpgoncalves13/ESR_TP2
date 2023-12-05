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
            self.state.update_metrics_rp(rp_ip, neighbour, rp_entry[1] + delay, max(rp_entry[2], loss))
            self.state.add_next_steps(neighbour, neighbours)

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

    def handle_neighbour_death(self, neighbour):
        # Send join to the neighbours of the neighbour if I do not have other option
        neighbour_to_rp = self.state.get_neighbour_to_rp()
        if neighbour_to_rp is None:
            # Add to neighbours the next steps of the neighbour (which is dead)
            self.state.delete_neighbour(neighbour)
            next_steps = self.state.get_next_steps(neighbour)
            self.state.add_neighbours(next_steps)

            time.sleep(12)
            packet = Packet(PacketType.JOIN, '0.0.0.0', self.state.client_stream_id, '0.0.0.0').serialize()
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(5)
            ProbeThread.send_packet_with_confirmation(udp_socket, packet,
                                                      (self.state.get_neighbour_to_rp(), self.state.port))
            udp_socket.close()

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
                    self.handle_neighbour_death(neighbour)

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
