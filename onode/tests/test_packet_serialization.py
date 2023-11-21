import unittest
from server.stream_packet import Packet, PacketType


class TestPacketSerialization(unittest.TestCase):

    def test_packet_with_head_fields(self):
        packet_type, leaf, stream_id, last_hop = PacketType.SETUP, '0.0.0.0', 0, '0.0.0.0'
        packet = Packet(packet_type, leaf, stream_id, last_hop)
        packet_serialized = packet.serialize()

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.type, packet_type)
        self.assertEqual(packet_deserialized.leaf, leaf)
        self.assertEqual(packet_deserialized.stream_id, stream_id)
        self.assertEqual(packet_deserialized.last_hop, last_hop)
        self.assertEqual(packet_deserialized.payload, None)

    def test_rsetup_packet(self):
        packet_type, leaf, stream_id, last_hop, payload =\
            PacketType.RSETUP, '0.0.0.0', 0, '0.0.0.0', ['127.0.0.1', '127.0.0.2']
        packet = Packet(packet_type, leaf, stream_id, last_hop, payload)
        packet_serialized = packet.serialize()

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.type, packet_type)
        self.assertEqual(packet_deserialized.leaf, leaf)
        self.assertEqual(packet_deserialized.stream_id, stream_id)
        self.assertEqual(packet_deserialized.last_hop, last_hop)
        self.assertEqual(packet_deserialized.payload, payload)

    def test_stream_packet(self):
        packet_type, leaf, stream_id, last_hop, payload = \
            PacketType.STREAM, '0.0.0.0', 0, '0.0.0.0', b'ola'
        packet = Packet(packet_type, leaf, stream_id, last_hop, payload)
        packet_serialized = packet.serialize()

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.type, packet_type)
        self.assertEqual(packet_deserialized.leaf, leaf)
        self.assertEqual(packet_deserialized.stream_id, stream_id)
        self.assertEqual(packet_deserialized.last_hop, last_hop)
        self.assertEqual(packet_deserialized.payload, payload)

    def test_rmeasure_packet(self):
        packet_type, leaf, stream_id, last_hop, payload = \
            (PacketType.RMEASURE, '0.0.0.0', 0, '0.0.0.0'
             , [('127.0.0.1', '12.10.10.1', 100, 80), ('127.0.0.2', '15.0.0.10', 20, 100)])
        packet = Packet(packet_type, leaf, stream_id, last_hop, payload)
        packet_serialized = packet.serialize()
        print(packet_serialized)

        packet_deserialized = Packet.deserialize(packet_serialized)
        self.assertEqual(packet_deserialized.type, packet_type)
        self.assertEqual(packet_deserialized.leaf, leaf)
        self.assertEqual(packet_deserialized.stream_id, stream_id)
        self.assertEqual(packet_deserialized.last_hop, last_hop)
        self.assertEqual(packet_deserialized.payload, payload)


