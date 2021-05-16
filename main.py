from Gateway import Gateway
from Device import UnknownDeviceType

if __name__ == '__main__':
    gateway = Gateway(com_port="/dev/cu.usbmodem14101")
    gateway.add_device_type(UnknownDeviceType())
    # d = gateway.get_device_type("Unknown")
    gateway.run()


