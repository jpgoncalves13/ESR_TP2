import unittest
from server.stream_packet import Packet, PacketType


class TestPacketSerialization(unittest.TestCase):

    def test_packet_with_all_fields(self):
        origin = '127.0.0.1'
        delay = 10
        loss = 50
        hops = 5
        last_hops = ['127.0.0.3', '127.0.0.2']
        neighbours = ['127.0.0.2']
        payload = 'Ola'.encode('ascii')
        packet = Packet(origin, PacketType.SETUP, delay, loss, hops, last_hops, neighbours, payload)
        packet_serialized = packet.serialize()

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.origin, origin)
        self.assertEqual(packet_deserialized.type, PacketType.SETUP)
        self.assertEqual(packet_deserialized.delay, delay)
        self.assertEqual(packet_deserialized.loss, loss)
        self.assertEqual(packet_deserialized.number_of_hops, hops)
        self.assertEqual(packet_deserialized.last_hops, last_hops)
        self.assertEqual(packet_deserialized.neighbors, neighbours)
        self.assertEqual(packet_deserialized.payload, payload)

    def test_packet_without_lists(self):
        origin = '127.0.0.1'
        delay = 10
        loss = 50
        hops = 5
        last_hops = []
        neighbours = []
        payload = 'Ola'.encode('ascii')
        packet = Packet(origin, PacketType.SETUP, delay, loss, hops, payload=payload)
        packet_serialized = packet.serialize()

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.origin, origin)
        self.assertEqual(packet_deserialized.type, PacketType.SETUP)
        self.assertEqual(packet_deserialized.delay, delay)
        self.assertEqual(packet_deserialized.loss, loss)
        self.assertEqual(packet_deserialized.number_of_hops, hops)
        self.assertEqual(packet_deserialized.last_hops, last_hops)
        self.assertEqual(packet_deserialized.neighbors, neighbours)
        self.assertEqual(packet_deserialized.payload, payload)

    def test_packet_without_payload(self):
        origin = '127.0.0.1'
        delay = 10
        loss = 50
        hops = 5
        last_hops = ['127.0.0.3', '127.0.0.2']
        neighbours = ['127.0.0.2']
        packet = Packet(origin, PacketType.SETUP, delay, loss, hops, last_hops, neighbours)
        packet_serialized = packet.serialize()

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.origin, origin)
        self.assertEqual(packet_deserialized.type, PacketType.SETUP)
        self.assertEqual(packet_deserialized.delay, delay)
        self.assertEqual(packet_deserialized.loss, loss)
        self.assertEqual(packet_deserialized.number_of_hops, hops)
        self.assertEqual(packet_deserialized.last_hops, last_hops)
        self.assertEqual(packet_deserialized.neighbors, neighbours)
        self.assertEqual(len(packet_deserialized.payload), 0)




