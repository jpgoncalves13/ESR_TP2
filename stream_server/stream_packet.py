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
    LEAVE = 12


class Packet:

    def __init__(self, packet_type, leaf, stream_id, last_hop, payload=None):
        self.type = packet_type  # 1
        self.leaf = leaf  # 4
        self.stream_id = stream_id  # 1
        self.last_hop = last_hop  # 4
        self.payload = payload  # RSETUP -> neighbours,
        # RMEASURE -> ([(leaf, nex_hop, delay, loss)], [clients], [stream clients]),
        # STREAM -> bytes

    def serialize(self):
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
            # neighbors
            byte_array += len(self.payload).to_bytes(4, byteorder='big')
            for neighbour in self.payload:
                neighbour_parts = neighbour.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in neighbour_parts])

        elif self.type == PacketType.STREAM:  # Payload in bytes
            clients, stream_data = self.payload
            byte_array += len(clients).to_bytes(1, byteorder='big')
            for client in clients:
                parts = client.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in parts])
            byte_array += len(stream_data).to_bytes(4, byteorder='big')
            byte_array += stream_data

        elif self.type == PacketType.RMEASURE:  # Delay and Loss in a list of tuples

            best_entries, rp_entry = self.payload

            byte_array += len(best_entries).to_bytes(4, byteorder='big')
            for leaf, next_hop, delay, loss in best_entries:
                # leaf
                leaf_parts = leaf.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in leaf_parts])
                # neighbour
                neighbour_parts = next_hop.split('.')
                byte_array += b''.join([int(part).to_bytes(1, 'big') for part in neighbour_parts])
                # delay
                byte_array += delay.to_bytes(4, byteorder='big')
                # loss
                byte_array += loss.to_bytes(4, byteorder='big')

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
                byte_array += rp_entry[3].to_bytes(4, byteorder='big')
            else:
                byte_array += int(0).to_bytes(1, byteorder='big')

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
        # stream_id (1 byte)
        stream_id = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
        offset += 1
        # last_hop
        last_hop_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
        last_hop = '.'.join(map(str, last_hop_ip_parts))
        offset += 4

        clients = []
        payload = None
        if message_type == PacketType.STREAM:
            num_clients = int.from_bytes(byte_array[offset: offset + 1], 'big')
            offset += 1
            for _ in range(num_clients):
                client_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                clients.append('.'.join(map(str, client_ip_parts)))
                offset += 4
            num_bytes = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            data = byte_array[offset:offset + num_bytes]
            payload = (clients, data)

        elif message_type == PacketType.RSETUP:
            num_neighbours = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            payload = []
            for _ in range(num_neighbours):
                neighbour_ip_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                payload.append('.'.join(map(str, neighbour_ip_parts)))
                offset += 4

        elif message_type == PacketType.RMEASURE:
            num_entries = int.from_bytes(byte_array[offset: offset + 4], 'big')
            offset += 4
            best_entries = []
            for _ in range(num_entries):
                # leaf (4 bytes)
                leaf_parts = [int.from_bytes(bytes([byte]), 'big') for byte in byte_array[offset:offset + 4]]
                leaf1 = '.'.join(map(str, leaf_parts))
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
                best_entries.append((leaf1, neighbour1, delay, loss))

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

            payload = (best_entries, rp_entry)

        return Packet(message_type, leaf, stream_id, last_hop, payload)

    def __str__(self):
        return (str(self.type.value) + ";" + str(self.stream_id) + ";" + ";"
                + str(self.last_hop) + ";" + str(self.leaf) + ";" + str(self.payload))
