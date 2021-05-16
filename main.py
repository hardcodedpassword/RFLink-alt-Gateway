from Gateway import Gateway
from Device import UnknownDeviceType
from SomfyRTS import SomfyRemoteType
import logging


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    gateway = Gateway(com_port="/dev/cu.usbmodem14101")
    gateway.add_device_type(SomfyRemoteType())
    gateway.add_device_type(UnknownDeviceType())
    # d = gateway.get_device_type("Unknown")
    gateway.run()


