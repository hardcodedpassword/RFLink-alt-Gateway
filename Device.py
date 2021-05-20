import logging


class DeviceInstance:
    def __init__(self, id, commands):
        self.id = id
        self.commands = commands

    def parse(self, timestamp, pulses):
        return False

    def get_id(self):
        return self.id

    def get_state(self):
        return 'OK'

    def get_commands(self):
        return self.commands

    def execute_command(self, command):
        if command in self.commands:
            method = getattr(self, command, None)
            if method is None:
                raise Exception('command not implemented')
            return method()
        else:
            raise Exception('no such command')

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
        DeviceInstance.__init__(self, 'Unknown device handler', [''])

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
