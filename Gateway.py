from Device import UnknownDeviceType
import serial
import logging
import signal
from datetime import datetime
import re


class Gateway:
    def signal_handler(self, frame):  # TODO - not sure if this is correct
        logging.info("Gateway exiting gracefully")
        self.running = False

    def __init__(self, com_port: str):
        self.com_port = com_port
        self.serial_port = None
        logging.info("Initializing RFLink-alt-gateway")

        # set-up the basic device administration
        self.device_types = []

        signal.signal(signal.SIGINT, self.signal_handler)
        logging.info("Opening COM port " + self.com_port)
        self.serial_port = serial.Serial(self.com_port, 57600, timeout=0.1)
        self.running = True

    def add_device_type(self, device_type):
        self.device_types.append(device_type)

    def get_device_type(self, device_type_name):
        for dt in self.device_types:
            if dt.name == device_type_name:
                return dt
        return None

    def __del__(self):
        if not(self.serial_port is None):
            logging.debug("Closing COM port: " + self.com_port)
            self.serial_port.close()

    def run(self):
        message = ''
        while self.running:
            data = self.serial_port.readline()
            if len(data) > 0:
                message += data.decode("utf-8")
                eol = message[-1]
                if eol == '\n':
                    # complete message: share with devices
                    logging.debug('recv: ' + message)
                    self.handle_message(message)
                    message = ''

        self.serial_port.close()
        logging.debug("Serial comms thread done")

    def handle_message(self, message):
        if message[0] == "r":
            now = datetime.now()
            try:
                m = re.split(":|,",message)[2:]
                pulses = [int(s) for s in m]
                for d in self.device_types:
                    if d.parse(now, pulses):
                        # message has been handled
                        # Note that the unknown device should always be at the end of this list
                        break
            except:
                logging.debug("Invalid message")
