import logging


class DeviceInstance:
    def __init__(self, id):
        self.id = id
        pass

    def parse(self, timestamp, pulses):
        return False

    def get_id(self):
        return self.id

class DeviceType:
    def __init__(self, type_name):
        self.type_name = type_name
        self.instances = []

    def add_instance(self, instance):
        self.instances.append(instance)

    def get_instance(self, instance_id):
        for i in self.instances:
            if i.get_id() == instance_id:
                return i
        return None

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
        DeviceType.__init__(self, "Unknown")
        self.instances.append(UnknownDeviceInstance())

    def add_instance(self):
        raise Exception("should not be used")

    def parse(self, timestamp, pulses):
        return self.instances[0].parse(timestamp, pulses)
