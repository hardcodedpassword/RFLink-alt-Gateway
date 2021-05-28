import serial
import logging
import signal
from datetime import datetime
import re
import RFLinkTools
from tinydb import TinyDB
from Device import UnknownDeviceType


class Gateway:
    def __signal_handler(self, frame):  # TODO - not sure if this is correct
        logging.info('Gateway exiting gracefully')
        self.running = False

    def __init__(self):
        self.serial_port = None

        self.running = True

        self.filename = './gateway.db'
        self.db = TinyDB(self.filename)
        self.device_type_table = self.db.table('device_type')

        # set-up the basic device administration
        self.device_types = [UnknownDeviceType()]

        for dt in self.device_type_table.all():
            self._add_device_type_instance(device_module=dt['device_module'], device_type=dt['device_type'])

        signal.signal(signal.SIGINT, self.__signal_handler)

    def _add_device_type_instance(self, device_module, device_type):
        matches = [dt for dt in self.device_types if type(dt).__name__ == device_type]

        if len(matches) == 0:
            device_type_module = __import__(device_module)
            device_type_class = getattr(device_type_module, device_type)
            device_type_instance = device_type_class()
            # the unknown device type should always be the last
            i = max(len(self.device_types) - 1, 0)
            self.device_types.insert(i, device_type_instance)
            logging.info('Added device type {module}.{type}, id={id}'.format(module=device_module, type=device_type, id=i))
            return i
        else:
            raise Exception('Cannot add second instance of same device type')

    def add_device_type(self, device_module, device_type):
        i = self._add_device_type_instance(device_module, device_type)
        self.device_type_table.insert({'id': str(i), 'device_module': device_module, 'device_type': device_type})

    def get_device_type(self, device_type_name):
        for dt in self.device_types:
            if dt.type_name == device_type_name:
                return dt
        return None

    def __del__(self):
        if not (self.serial_port is None):
            logging.debug('Closing COM port: ' + self.serial_port)
            self.serial_port.close()

    def step(self, message):
        data = self.serial_port.readline()
        if len(data) > 0:
            message += data.decode('utf-8')
            eol = message[-1]
            if eol == '\n':
                # complete message: share with devices
                logging.debug('recv: ' + message)
                self.__handle_message(message)
                message = ''
        return message

    def run(self, com_port: str):
        logging.info('Opening COM port ' + com_port)
        self.serial_port = serial.Serial(com_port, 57600, timeout=0.1)

        message = ''
        while self.running:
            self.step(message)

        self.serial_port.close()
        logging.debug('Gateway run stopped')

    def send(self, pulses):
        p_str = 't:' + RFLinkTools.pulses_to_string(pulses) + '\n'
        logging.info('Sending command: ' + p_str)
        self.serial_port.write(p_str.encode('utf-8'))

    def __handle_message(self, message):
        # received messages start with 'r'
        if message[0] == 'r':
            now = datetime.now()
            try:
                m = re.split('[:,]', message)[2:]
                pulses = [int(s) for s in m]
                for d in self.device_types:
                    if d.parse(now, pulses):
                        # message has been handled
                        # Note that the unknown device should always be at the end of this list
                        break
            except Exception as e:
                logging.debug('Invalid message')

    # def load(self, filename):
    #     self.filename = filename
    #     with open(self.filename, 'rb') as f:
    #         self.device_types = pickle.load(file=f)
    #
    # def save(self, filename):
    #     with open(filename, 'wb') as f:
    #         pickle.dump(self.device_types, file=f)
