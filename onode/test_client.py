from server.stream_packet import Packet, PacketType
import socket

packet = Packet(PacketType.STREAMREQ, '0.0.0.0', 0, 0, '0.0.0.0')
upd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ip = input()
upd.sendto(packet.serialize(), (ip, 5000))
upd.close()


