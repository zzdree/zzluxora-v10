import unittest
from core.artnet_sender import ArtNetSender


class TestArtNetSender(unittest.TestCase):
    def test_artnet_packet_structure(self):
        sender = ArtNetSender(target_ip="127.0.0.1", universe=0)

        # Set some channels
        sender.set_channel(1, 255)  # Channel 1: Master Dimmer full
        sender.set_channel(2, 128)  # Channel 2: Red half
        sender.set_channel(3, 64)   # Channel 3: Green quarter

        packet = sender.build_packet()

        # Total packet must be 530 bytes (18 header + 512 channels)
        self.assertEqual(len(packet), 530)
        # Header ID
        self.assertEqual(packet[:8], b"Art-Net\x00")
        # OpCode 0x5000 little-endian
        self.assertEqual(packet[8:10], b"\x00\x50")
        # ProtVer 14 big-endian
        self.assertEqual(packet[10:12], b"\x00\x0e")
        # DMX Length 512 big-endian
        self.assertEqual(packet[16:18], b"\x02\x00")

        # Verify channel payload values
        self.assertEqual(packet[18], 255)  # DMX 1
        self.assertEqual(packet[19], 128)  # DMX 2
        self.assertEqual(packet[20], 64)   # DMX 3
        self.assertEqual(packet[21], 0)    # DMX 4

        sender.close()

    def test_artnet_blackout(self):
        sender = ArtNetSender(target_ip="127.0.0.1", universe=0)
        sender.set_channels(1, [255, 255, 255, 255])
        self.assertEqual(sender.get_channel(1), 255)

        sender.blackout()
        self.assertEqual(sender.get_channel(1), 0)
        self.assertEqual(sender.get_channel(2), 0)
        self.assertEqual(sender.get_channel(3), 0)
        self.assertEqual(sender.get_channel(4), 0)

        sender.close()


if __name__ == "__main__":
    unittest.main()
