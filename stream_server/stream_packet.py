from enum import Enum


class PacketType(Enum):
    SETUP = 1
    RSETUP = 2
    JOIN = 4
    MEASURE = 5
    RMEASURE = 6
    ACK = 7
    STREAM = 8
    LEAVE = 10


class Packet:

    def __init__(self, packet_type, leaf, stream_id, last_hop, payload=None):
        self.type = packet_type  # 1
        self.leaf = leaf  # 4
        self.stream_id = stream_id  # 1
        self.last_hop = last_hop  # 4
        self.payload = payload  # Variable

    def serialize(self):
        """
        Method to serialize the packet
        """
        byte_array = bytearray()
        # type
        byte_array += self.type.value.to_bytes(1, byteorder='big')
        # leaf
        leaf_ip_parts = self.leaf.split('.')
        byte_array += b''.join([int(part).to_bytes(1, 'big') for part in leaf_ip_parts])
        # stream_id
        byte_array += self.stream_id.to_bytes(1, byteorder='big')
        # last hop
        last_hop_ip_parts = self.last_hop.split('.')
        byte_array += b''.join([int(part).to_bytes(1, 'big') for part in last_hop_ip_parts])

        if self.type == PacketType.RSETUP:  # List of neighbours
            byte_array += len(self.payload).to_bytes(4, byteorder='big')
            for neighbour in self.payload:
                neighbour_parts = neighbour.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in neighbour_parts])

        elif self.type == PacketType.STREAM:  # Data of the stream in bytes
            byte_array += len(self.payload).to_bytes(4, byteorder='big')
            byte_array += self.payload

        elif self.type == PacketType.RMEASURE:
            # Get the best entry to rp for eah neighbour
            # and the neighbours with connection to rp of that neighbour
            rp_entry, neighbours = self.payload

            if rp_entry is not None:
                byte_array += int(1).to_bytes(1, byteorder='big')
                # rp_ip
                leaf_parts = rp_entry[0].split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in leaf_parts])
                # neighbour
                neighbour_parts = rp_entry[1].split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in neighbour_parts])
                # delay
                byte_array += rp_entry[2].to_bytes(4, byteorder='big')
                # loss
                byte_array += rp_entry[3].to_bytes(1, byteorder='big')
            else:
                byte_array += int(0).to_bytes(1, byteorder='big')

            byte_array += len(neighbours).to_bytes(1, byteorder='big')
            for neighbour_of_neighbour in neighbours:
                neighbour_parts = neighbour_of_neighbour.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in neighbour_parts])

        return byte_array

    @staticmethod
    def deserialize(byte_array):
        """
        Function to deserialize the packet
        """
        offset = 0
        # type (1 byte)
        message_type = PacketType(int.from_bytes(byte_array[offset:offset + 1], byteorder='big'))
        offset += 1
        # leaf (4 bytes)
        leaf_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset: offset + 4]]
        leaf = '.'.join(map(str, leaf_ip_parts))
        offset += 4
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
            data = byte_array[offset:offset + num_bytes]
            payload = data

        elif message_type == PacketType.RSETUP:
            num_neighbours = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            payload = []
            for _ in range(num_neighbours):
                neighbour_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                payload.append('.'.join(map(str, neighbour_ip_parts)))
                offset += 4

        elif message_type == PacketType.RMEASURE:

            rp_entry_exists = int.from_bytes(byte_array[offset: offset + 1], 'big')
            offset += 1
            if rp_entry_exists == 1:
                # rp_ip (4 bytes)
                rp_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                rp_ip = '.'.join(map(str, rp_ip_parts))
                offset += 4
                # neighbour (4 bytes)
                neighbour_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                neighbour1 = '.'.join(map(str, neighbour_parts))
                offset += 4
                # delay (4 bytes)
                delay = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
                offset += 4
                # loss (4 bytes)
                loss = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
                offset += 4
                rp_entry = (rp_ip, neighbour1, delay, loss)
            else:
                rp_entry = None

            neighbours = []
            num_neighbours = int.from_bytes(byte_array[offset: offset + 4], 'big')
            for _ in range(num_neighbours):
                neighbour_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                neighbour = '.'.join(map(str, neighbour_parts))
                offset += 4
                neighbours.append(neighbour)

            payload = (rp_entry, neighbours)

        return Packet(message_type, leaf, stream_id, last_hop, payload)

    def __str__(self):
        return (str(self.type.value) + ";" + str(self.stream_id) + ";" + ";"
                + str(self.last_hop) + ";" + str(self.leaf) + ";" + str(self.payload))
