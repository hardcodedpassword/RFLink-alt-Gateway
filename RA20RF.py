# RA20RF Protocol
#
# from github.com/pimatic/rfcontroljs and
# https://gl.petatech.eu/root/HomeBot/-/blob/b79dca5670634762a1ac3622cd9c7e401a98779d/FHEM/14_FLAMINGO.pm
#
# Message: [Header] [DeviceID] [Footer]
# header=8000,800
# DeviceID = 48 pulses where: 0 = 800, 1600 and 1 = 800, 2800
# footer=800,13000
# message is repeated 3 times with 20ms delay
# Apparently there is no on or off instruction?
#
import RFLinkTools
from Device import DeviceType, DeviceInstance
import logging


class RA20RFInstance(DeviceInstance):
    def __init__(self, device_id: int):
        self.device_id = [device_id>>16 & 0xff, device_id>>8 & 0xff, device_id>>0 & 0xff]
        DeviceInstance.__init__(self, str(device_id), ['alarm'])

    def handle(self):
        logging.info("RA20RF: ALARM device id: {id}".format(self.device_id))

    def alarm(self):
        bits = RFLinkTools.bytes_to_bits(self.device_id)
        pulses = [3,1] + \
                 [10*RA20RFType.pulse_time, RA20RFType.pulse_time] + \
                 RFLinkTools.encode_two_state(bits, RA20RFType.pulse_time, RA20RFType.bit_encoding) + \
                 [RA20RFType.pulse_time,RA20RFType.pulse_time*16]

        return pulses


class RA20RFType(DeviceType):
    pulse_time = 800
    bit_encoding = {'0': [1, 2], '1': [1, 3]}

    def __init__(self):
        DeviceType.__init__(self, "RA20RF")

    def parse(self, timestamp, pulses):
        if len(pulses) == 52:
            if (7000 <= pulses[0] <= 9000) and (700 <= pulses[1] <= 900):
                bits = RFLinkTools.decode_two_state(pulses[2:50], self.pulse_time, self.bit_encoding, 0.25)
                bytes = RFLinkTools.bits_to_bytes(bits)
                device_id = bytes[0] << 16 | bytes[1] << 8 | bytes[2]
                for i in self.instances:
                    if i.get_id() == str(device_id):
                        i.handle()
                        is_handled = True
                if not is_handled:
                     logging.info("RA20RF: device id:{id}".format(id=device_id))
                return True
        return False