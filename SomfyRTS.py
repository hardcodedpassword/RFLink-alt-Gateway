# Somfy RTS protocol:
# # Pulse time is 640 microseconds
# | -- HW Sync -----|-sync-|-L-|---- data manchester encoded ---- |
# https://pushstack.wordpress.com/somfy-rts-protocol/
# | 4*pulse| 4*pulse| 4*pulse| 4*pulse| 7*pulse |1*pulse| 67648 us |  30415 us  |
# +--------+        +--------+        +---...---+
# +        +--------+        +--------+         +-------+XXXX...XXX+-----...-----
# |              hw. sync.            |   soft.         |          | Inter-frame
# |                                   |   sync.         |   data   |     gap
# Data:
#    byte
#     0       1        2       3       4       5       6
# |-------|--------|-------|-------|-------|-------|-------|
# |  key  |ctrl|cks|  Rolling Code |   Address(A0|A1|A3)   |
# |-------|--------|-------|-------|-------|-------|-------|
#
# Key:
#   “Encryption Key”, Most significant 4-bit are always 0xA, Least Significant bits is a linear counter.
#   In the Smoove Origin this counter is increased together with the rolling code.
#   But leaving this on a constant value also works. Gerardwr notes that for some other types of remotes the MSB is not constant.
# Ctrl:
#   4-bit Control codes, this indicates the button that is pressed
# Cks:
#   4-bit Checksum.
# Rolling Code:
#   16-bit rolling code (big-endian) increased with every button press.
# Address:
#   24-bit identifier of sending device (little-endian)

# The remote buttons
import RFLinkTools
from enum import Enum
from Device import DeviceType, DeviceInstance
import logging


class BlindButtons(Enum):
    none = 0x00
    stop = 0x01
    up = 0x02
    down = 0x04
    prog = 0x08


class SomfyRemoteInstance(DeviceInstance):
    def __init__(self, code, remote):
        self.code = code
        self.remote = remote
        self.last_button = BlindButtons.none
        DeviceInstance.__init__(self, str(remote))

    def __preamble(self):
        preamble = []

        # hardware sync
        for i in range(0, 4):
            preamble.append(4 * SomfyRemoteType.pulse_time)

        # soft sync
        preamble.append(7 * SomfyRemoteType.pulse_time)
        preamble.append(1 * SomfyRemoteType.pulse_time)

        return preamble

    def __get_pulses(self, button: BlindButtons):
        self.code += 1
        cmd = RtsCommand()
        cmd.encode(button, self.code, self.remote)
        bits = RFLinkTools.bytes_to_bits(cmd.data)
        pulses = RFLinkTools.encode_manchester(bits, 64, self.__preamble())
        return [1,1] + pulses

    def handle(self, cmd):
        self.code = cmd.code
        self.last_button = BlindButtons(cmd.button)
        logging.info("Somfy RTS: remote:{remote} code:{code} button:{button}".format(remote=cmd.remote,
                                                                                     code=cmd.code,
                                                                                     button=cmd.button))

    def stop(self):
        return self.__get_pulses(BlindButtons.stop)

    def up(self):
        return self.__get_pulses(BlindButtons.up)

    def down(self):
        return self.__get_pulses(BlindButtons.down)

    def prog(self):
        return self.__get_pulses(BlindButtons.prog)


class SomfyRemoteType(DeviceType):
    pulse_time = 64  # 64 * 10us = 640 us

    def __init__(self):
        DeviceType.__init__(self, "SomfyRTS")

    def parse(self, timestamp, pulses):
        if 8704 * 0.85 <= sum(pulses) <= 8704 * 1.15:
            # could be an RTS message, continue from here
            if 24*self.pulse_time*0.85 <= sum(pulses[0:5]) <= 24*self.pulse_time*1.15:
                bits = RFLinkTools.decode_manchester(pulses[5:], 64, 1)
                bytes = RFLinkTools.bits_to_bytes(bits)
                cmd = RtsCommand()
                cmd.decode(bytes)
                is_handled = False
                for i in self.instances:
                    if i.get_id() == str(cmd.remote):
                        i.handle(cmd)
                        is_handled = True
                if not is_handled:
                     logging.info("Somfy RTS (unknown remote): remote:{remote} code:{code} button:{button}".format(remote=cmd.remote,
                                                                                                 code=cmd.code,
                                                                                                 button=cmd.button))
                return True
        return False


class RtsCommand:
    data = bytearray(7)
    button = 0
    code = 0
    remote = 0

    def encode(self, button: BlindButtons, code, remote):
        self.button = button
        self.code = code
        self.remote = remote

        self.data[0] = 0xA7
        self.data[1] = (button.value << 4) & 0xff
        self.data[2] = (code >> 8) & 0xff
        self.data[3] = code & 0xFF
        self.data[4] = (remote >> 16) & 0xff
        self.data[5] = (remote >> 8) & 0xff
        self.data[6] = remote & 0xff

        checksum = self.__checksum()
        self.data[1] = self.data[1] | checksum
        self.__obfuscate()

    def decode(self, data: bytearray):
        if len(data) != 7:
            raise Exception("invalid data length")

        self.data = data.copy()
        self.__decipher()

        crc = self.data[1] & 0x0f
        self.data[1] &= 0xf0
        if crc != self.__checksum():
            raise Exception("invalid checksum")

        self.button = self.data[1] >> 4
        self.code = (self.data[2] << 8) | self.data[3]
        self.remote = (self.data[4] << 16) | (self.data[5] << 8) | self.data[6]

    def __checksum(self) -> int:
        checksum = 0
        for byte in self.data:
            checksum = checksum ^ byte ^ (byte >> 4)
        checksum = checksum & 0x0F
        return checksum

    def __obfuscate(self):
        for i in range(1, 7):
            self.data[i] = self.data[i] ^ self.data[i - 1]

    def __decipher(self):
        data = [self.data[0], 0, 0, 0, 0, 0, 0]
        for i in range(1, 7):
            data[i] = self.data[i] ^ self.data[i - 1]
        self.data = data

    def to_string(self):
        hex_string = "".join(" 0x%02x" % b for b in self.data)
        return hex_string
