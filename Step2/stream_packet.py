
from enum import Enum


class PacketType(Enum):
    SETUP = 1
    RSETUP = 2
    HELLO = 3
    JOIN = 4
    TREEUPD = 5
    MEASURE = 6
    ACK = 7
    STREAMREQ = 8
    STREAM = 9


class Packet:

    def __init__(self, destinations, message_type: int, last_hops, delay: int, loss: int, number_of_hops: int):
        self.type = message_type
        self.destinations = destinations
        self.last_hops = last_hops
        self.delay = delay
        self.loss = loss
        self.number_of_hops = number_of_hops

    def serialize(self):
        byte_array = bytearray()

        # type
        byte_array += self.type.to_bytes(1, byteorder='big')

        # destinations
        byte_array += len(self.destinations).to_bytes(4, byteorder='big')
        for destination in self.destinations:
            byte_array += str(destination).encode('ascii')

        # last hops
        byte_array += len(self.last_hops).to_bytes(4, byteorder='big')
        for hop in self.last_hops:
            byte_array += str(hop).encode('ascii')

        # delay
        byte_array += self.delay.to_bytes(4, byteorder='big')

        # loss
        byte_array += self.loss.to_bytes(1, byteorder='big')

        # number of hops
        byte_array += self.number_of_hops.to_bytes(4, byteorder='big')

        return bytes(byte_array)

    @staticmethod
    def deserialize(byte_array: bytearray):
        offset = 0

        # Read type (1 byte)
        message_type = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
        offset += 1

        # Deserialize destinations (list of strings)
        destinations_count = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4
        destinations = []
        for _ in range(destinations_count):
            str_length = int.from_bytes(byte_array[offset:offset + 2], byteorder='big')
            offset += 2
            destination = byte_array[offset:offset + str_length].decode('ascii')
            offset += str_length
            destinations.append(destination)

        # Deserialize last hops (list of strings)
        last_hops_count = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4
        last_hops = []
        for _ in range(last_hops_count):
            str_length = int.from_bytes(byte_array[offset:offset + 2], byteorder='big')
            offset += 2
            hop = byte_array[offset:offset + str_length].decode('ascii')
            offset += str_length
            last_hops.append(hop)

        # Deserialize delay (4 bytes)
        delay = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4

        # Deserialize loss (1 byte)
        loss = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
        offset += 1

        # Deserialize number of hops (4 bytes)
        number_of_hops = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4

        return Packet(destinations, message_type, last_hops, delay, loss, number_of_hops)
