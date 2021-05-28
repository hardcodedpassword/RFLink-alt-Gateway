import logging


# base class for all device instances
class DeviceInstance:
    def __init__(self, id: str):
        self.id = id

    def parse(self, timestamp, pulses):
        return False

    def get_id(self):
        return self.id

    def get_state(self):
        return 'OK'


# base class for all device types
class DeviceType:
    def __init__(self, type_name, commands):
        self.type_name = type_name
        self.instances = []
        self.commands = commands

    def add_instance(self, instance):
        self.instances.append(instance)

    def parse(self, timestamp, pulses):
        return False

    def get_instance(self, instance_id):
        for i in self.instances:
            if i.get_id() == instance_id:
                return i
        raise Exception( 'No such device instance')

    def new_instance(self, parameters: {}):
        pass

    def get_commands(self):
        return self.commands

    def execute_command(self, instance_id, command):
        instance = self.get_instance(instance_id)
        if command in self.get_commands():
            method = getattr(instance, command, None)
            if method is None:
                raise Exception('command not implemented')
            return method()
        else:
            raise Exception('no such command')


# this class handles all unknown messages
class UnknownDeviceType(DeviceType):
    def __init__(self):
        DeviceType.__init__(self, "Unknown", [])

    def add_instance(self):
        raise Exception("should not be used")

    def parse(self, timestamp, pulses):
        s = ",".join([str(i) for i in pulses])
        msg = "{dt} Unknown: {msg}".format(dt=timestamp, msg=s)
        logging.info(msg)
        return True
