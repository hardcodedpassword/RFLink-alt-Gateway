import logging


class DeviceInstance:
    def __init__(self, id):
        self.id = id
        pass

    def parse(self, timestamp, pulses):
        return False


class DeviceType:
    def __init__(self, type_name):
        self.type_name = type_name
        self.instances = []

    def add_instance(self):
        self.instances.append(DeviceInstance())

    def parse(self, timestamp, pulses):
        return False


class UnknownDeviceInstance(DeviceInstance):
    def __init__(self):
        DeviceInstance.__init__(self, "Unknown")

    def parse(self, timestamp, pulses):
        s = ",".join([str(i) for i in pulses])
        msg = "{dt} Unknown: {msg}".format(dt=timestamp, msg=s)
        logging.info(msg)
        return True


class UnknownDeviceType(DeviceType):
    def __init__(self):
        DeviceType.__init__(self, 0)
        self.instances.append(UnknownDeviceInstance())

    def add_instance(self):
        raise Exception("should not be used called")

    def parse(self, timestamp, pulses):
        return self.instances[0].parse(timestamp, pulses)
