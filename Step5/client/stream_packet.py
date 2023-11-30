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
    UNSUBSCRIBE = 11

class Packet:

    def __init__(self, origin: str, message_type: PacketType, delay: int, loss: int, number_of_hops: int,
                 last_hops: [str] = None, neighbours: [str] = None, payload: bytes = None):
        if neighbours is None:
            neighbours = []
        if payload is None:
            payload = bytes()
        if last_hops is None:
            last_hops = []

        self.origin = origin
        self.type = message_type
        self.delay = delay
        self.loss = loss
        self.number_of_hops = number_of_hops
        self.last_hops = last_hops
        self.neighbors = neighbours
        self.payload = payload

    def serialize(self) -> bytearray:
        byte_array = bytearray()

        # type
        byte_array += self.type.value.to_bytes(1, byteorder='big')

        # origin
        byte_array += len(self.origin).to_bytes(2, byteorder='big')
        byte_array += self.origin.encode('ascii')

        # delay
        byte_array += self.delay.to_bytes(4, byteorder='big')

        # loss
        byte_array += self.loss.to_bytes(1, byteorder='big')

        # number of hops
        byte_array += self.number_of_hops.to_bytes(4, byteorder='big')

        # last hops
        byte_array += len(self.last_hops).to_bytes(4, byteorder='big')
        for hop in self.last_hops:
            byte_array += len(hop).to_bytes(2, byteorder='big')
            byte_array += hop.encode('ascii')

        # neighbors
        byte_array += len(self.neighbors).to_bytes(4, byteorder='big')
        for neighbour in self.neighbors:
            byte_array += len(neighbour).to_bytes(2, byteorder='big')
            byte_array += neighbour.encode('ascii')

        # payload
        byte_array += len(self.payload).to_bytes(4, byteorder='big')
        if len(self.payload) > 0:
            byte_array += self.payload

        return byte_array

    @staticmethod
    def deserialize(byte_array: bytearray):
        offset = 0

        # Read type (1 byte)
        message_type = PacketType(int.from_bytes(byte_array[offset:offset + 1], byteorder='big'))
        offset += 1

        # origin
        length_origin = int.from_bytes(byte_array[offset:offset + 2], byteorder='big')
        offset += 2
        origin = byte_array[offset:offset + length_origin].decode('ascii')
        offset += length_origin

        # Deserialize delay (4 bytes)
        delay = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4

        # Deserialize loss (1 byte)
        loss = int.from_bytes(byte_array[offset:offset + 1], byteorder='big')
        offset += 1

        # Deserialize number of hops (4 bytes)
        number_of_hops = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4

        # Deserialize last hops (array of strings)
        last_hops_count = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4
        last_hops = []
        for _ in range(last_hops_count):
            str_length = int.from_bytes(byte_array[offset:offset + 2], byteorder='big')
            offset += 2
            hop = byte_array[offset:offset + str_length].decode('ascii')
            offset += str_length
            last_hops.append(hop)

        # Deserialize neighbors (array of strings)
        neighbours_count = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4
        neighbours = []
        for _ in range(neighbours_count):
            str_length = int.from_bytes(byte_array[offset:offset + 2], byteorder='big')
            offset += 2
            neighbour = byte_array[offset:offset + str_length].decode('ascii')
            offset += str_length
            neighbours.append(neighbour)

        # Payload
        payload_bytes_count = int.from_bytes(byte_array[offset:offset + 4], byteorder='big')
        offset += 4
        if payload_bytes_count > 0:
            payload_bytes = byte_array[offset:offset + payload_bytes_count]
        else:
            payload_bytes = []

        return Packet(origin, message_type, delay, loss, number_of_hops, last_hops, neighbours, payload_bytes)

    def __str__(self):
        return (self.origin + ";" + str(self.type.value) + ";" + str(self.delay) + ";" + str(self.loss) + ";" +
                str(self.number_of_hops) + ";" + str(self.last_hops) + ";" + str(self.neighbors) + ";" +
                str(self.payload))