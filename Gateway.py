import serial
import logging
import signal
from datetime import datetime
import re
import RFLinkTools


class Gateway:
    def __signal_handler(self, frame):  # TODO - not sure if this is correct
        logging.info("Gateway exiting gracefully")
        self.running = False

    def __init__(self):
        self.serial_port = None
        # set-up the basic device administration
        self.device_types = []
        self.running = True
        signal.signal(signal.SIGINT, self.__signal_handler)

    def add_device_type(self, device_type):
        self.device_types.append(device_type)

    def get_device_type(self, device_type_name):
        for dt in self.device_types:
            if dt.type_name == device_type_name:
                return dt
        return None

    def __del__(self):
        if not(self.serial_port is None):
            logging.debug("Closing COM port: " + self.serial_port)
            self.serial_port.close()

    def step(self, message):
        data = self.serial_port.readline()
        if len(data) > 0:
            message += data.decode("utf-8")
            eol = message[-1]
            if eol == '\n':
                # complete message: share with devices
                logging.debug('recv: ' + message)
                self.__handle_message(message)
                message = ''
        return message

    def run(self, com_port: str):
        logging.info("Opening COM port " + com_port)
        self.serial_port = serial.Serial(com_port, 57600, timeout=0.1)

        message = ''
        while self.running:
            self.step(message)

        self.serial_port.close()
        logging.debug("Serial comms thread done")

    def send(self, pulses):
        p_str = 't:' + RFLinkTools.pulses_to_string(pulses) + '\n'
        logging.info('Sending command: ' + p_str)
        self.serial_port.write(p_str.encode('utf-8'))

    def __handle_message(self, message):
        if message[0] == "r":
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
                logging.debug("Invalid message")
