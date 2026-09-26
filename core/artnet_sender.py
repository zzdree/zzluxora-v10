"""
Art-Net 4 DMX512 UDP Transmitter Engine for ZZLUXORA v10.
Compliant with Artistic Licence Art-Net 4 Protocol Specification.
Generates OpOutput / OpDmx packets (Universe 0) to UDP Port 6454.
"""

from __future__ import annotations
import socket
import struct
import threading
from typing import Optional, Sequence, Union
import numpy as np


class ArtNetSender:
    """
    High-performance, low-latency Art-Net DMX512 sender.
    Encapsulates 512 DMX channel values into Art-Net UDP datagrams.

    ArtDmx Packet Structure (530 bytes total):
    - ID [8 bytes]      : 'Art-Net\x00'
    - OpCode [2 bytes]  : 0x5000 (OpOutput / OpDmx, Little-Endian: 0x00, 0x50)
    - ProtVer [2 bytes] : 14 (Big-Endian: 0x00, 0x0E)
    - Sequence [1 byte] : 0x00 (disabled or incrementing counter)
    - Physical [1 byte] : 0x00
    - SubUni [1 byte]   : Universe low byte (Universe 0)
    - Net [1 byte]      : Net high byte (Net 0)
    - Length [2 bytes]  : 512 (Big-Endian: 0x02, 0x00)
    - Data [512 bytes]  : DMX512 channel values (0-255)
    """

    ARTNET_PORT = 6454
    HEADER_ID = b"Art-Net\x00"
    OP_DMX = 0x5000
    PROTOCOL_VERSION = 14

    def __init__(self, target_ip: str = "127.0.0.1", universe: int = 0, port: int = ARTNET_PORT):
        self.target_ip = target_ip
        self.universe = universe
        self.port = port

        # 512 DMX channels buffer (index 0 corresponds to DMX channel 1)
        self._dmx_buffer = bytearray(512)
        self._sequence = 0
        self._lock = threading.Lock()

        # Initialize UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable broadcast if target is a broadcast address
        if target_ip.endswith(".255") or target_ip == "255.255.255.255":
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self._connected = True

    @property
    def is_connected(self) -> bool:
        return self._connected

    def set_target_ip(self, ip: str) -> None:
        """Update target IP address dynamically."""
        with self._lock:
            self.target_ip = ip
            if ip.endswith(".255") or ip == "255.255.255.255":
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def set_channel(self, channel: int, value: int) -> None:
        """
        Set a single DMX channel (1-512) to value (0-255).
        """
        if 1 <= channel <= 512:
            with self._lock:
                self._dmx_buffer[channel - 1] = max(0, min(255, value))

    def set_channels(self, start_channel: int, values: Sequence[int]) -> None:
        """
        Set multiple contiguous DMX channels starting at start_channel (1-512).
        """
        with self._lock:
            for i, val in enumerate(values):
                ch = start_channel + i
                if 1 <= ch <= 512:
                    self._dmx_buffer[ch - 1] = max(0, min(255, val))

    def get_channel(self, channel: int) -> int:
        """Get current value of channel (1-512)."""
        if 1 <= channel <= 512:
            with self._lock:
                return self._dmx_buffer[channel - 1]
        return 0

    def get_all_channels(self) -> bytes:
        """Return a copy of the 512 DMX channels."""
        with self._lock:
            return bytes(self._dmx_buffer)

    def blackout(self) -> None:
        """Reset all 512 channels to 0 and immediately send packet."""
        with self._lock:
            for i in range(512):
                self._dmx_buffer[i] = 0
        self.send_frame()

    def build_packet(self) -> bytes:
        """Construct the 530-byte ArtDmx binary packet."""
        sub_uni = self.universe & 0xFF
        net = (self.universe >> 8) & 0x7F

        # Header 18 bytes:
        # ID [8B] + OpCode 0x5000 [2B little-endian] + ProtVer 14 [2B big-endian] +
        # Sequence [1B] + Physical [1B] + SubUni [1B] + Net [1B] + Length 512 [2B big-endian]
        header = (
            self.HEADER_ID +
            b"\x00\x50" +
            b"\x00\x0e" +
            bytes([self._sequence, 0x00, sub_uni, net]) +
            b"\x02\x00"
        )

        with self._lock:
            packet = header + bytes(self._dmx_buffer)

        # Advance sequence number (1-255, 0 = disabled)
        self._sequence = (self._sequence + 1) % 256
        if self._sequence == 0:
            self._sequence = 1

        return packet

    def send_raw(self, buffer: Sequence[int]) -> bool:
        """Set DMX channels from buffer and immediately transmit packet."""
        self.set_channels(1, buffer[:512])
        return self.send_frame()

    def send_frame(self) -> bool:
        """Transmit current DMX buffer via UDP to target IP."""
        try:
            packet = self.build_packet()
            self._socket.sendto(packet, (self.target_ip, self.port))
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the socket connection."""
        self._connected = False
        try:
            self._socket.close()
        except Exception:
            pass
