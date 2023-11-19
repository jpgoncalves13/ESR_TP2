from enum import Enum


class PacketType(Enum):
    SETUP = 1
    RSETUP = 2
    JOIN = 4
    TREEUPD = 5
    MEASURE = 6
    RMEASURE = 7
    ACK = 8
    STREAMREQ = 9
    STREAM = 10
    HELLO = 11


class Packet:

    def __init__(self, packet_type, leaf, node_id, stream_id, last_hop, payload=None):
        self.type = packet_type  # 1
        self.leaf = leaf  # 4
        self.stream_id = stream_id  # 1
        self.last_hop = last_hop  # 4
        self.node_id = node_id  # 1
        self.payload = payload  # RSETUP -> neighbours, RMEASURE -> [(leaf, nex_hop, delay, loss)], STREAM -> bytes

    def serialize(self):
        byte_array = bytearray()
        # type
        byte_array += self.type.value.to_bytes(1, byteorder='big')
        # leaf
        leaf_ip_parts = self.leaf.split('.')
        byte_array += b''.join([int(part).to_bytes(1, 'big') for part in leaf_ip_parts])
        # node identifier
        byte_array += self.node_id.to_bytes(1, byteorder='big')
        # stream_id
        byte_array += self.stream_id.to_bytes(1, byteorder='big')
        # last hop
        last_hop_ip_parts = self.last_hop.split('.')
        byte_array += b''.join([int(part).to_bytes(1, 'big') for part in last_hop_ip_parts])

        if self.type == PacketType.RSETUP:  # List of neighbours
            # neighbors
            byte_array += len(self.payload).to_bytes(4, byteorder='big')
            for neighbour in self.payload:
                neighbour_parts = neighbour.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in neighbour_parts])

        elif self.type == PacketType.STREAM:  # Payload in bytes
            byte_array += len(self.payload).to_bytes(4, byteorder='big')
            byte_array += self.payload

        elif self.type == PacketType.RMEASURE:  # Delay and Loss in a list of tuples
            byte_array += len(self.payload).to_bytes(4, byteorder='big')
            for leaf, next_hop, delay, loss in self.payload:
                # leaf
                byte_array += leaf.to_bytes(1, byte_order='big')
                # next hop
                next_hop_parts = next_hop.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in next_hop_parts])
                # delay
                byte_array += delay.to_bytes(4, byteorder='big')
                # loss
                byte_array += loss.to_bytes(4, byteorder='big')

        return byte_array

    @staticmethod
    def deserialize(byte_array):
        offset = 0
        # Read type (1 byte)
        message_type = PacketType(int.from_bytes(byte_array[offset:offset + 1], byteorder='big'))
        offset += 1
        # leaf (4 bytes)
        leaf_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset: offset + 4]]
        leaf = '.'.join(map(str, leaf_ip_parts))
        offset += 4
        # node identifier (3 byte)
        node_id = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
        offset += 1
        # stream_id (1 byte)
        stream_id = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
        offset += 1
        # last_hop
        last_hop_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
        last_hop = '.'.join(map(str, last_hop_ip_parts))
        offset += 4

        payload = None
        if message_type == PacketType.STREAM:
            num_bytes = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            payload = byte_array[offset:offset + num_bytes]

        elif message_type == PacketType.RSETUP:
            num_neighbours = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            payload = []
            for _ in range(num_neighbours):
                neighbour_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                payload.append('.'.join(map(str, neighbour_ip_parts)))
                offset += 4

        elif message_type == PacketType.RMEASURE:
            num_measures = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            payload = []
            for _ in range(num_measures):
                # leaf (1 bytes)
                leaf1 = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
                offset += 1
                # next hop (4 bytes)
                next_hop_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                next_hop = '.'.join(map(str, next_hop_ip_parts))
                offset += 4
                # delay (4 bytes)
                delay = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
                offset += 4
                # loss (4 bytes)
                loss = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
                offset += 4
                payload.append((leaf1, next_hop, delay, loss))

        return Packet(message_type, leaf, node_id, stream_id, last_hop, payload)

    def __str__(self):
        return (str(self.type.value) + ";" + str(self.stream_id) + ";" + str(self.node_id) + ";"
                + str(self.last_hop) + ";" + str(self.leaf) + ";" + str(self.payload))
