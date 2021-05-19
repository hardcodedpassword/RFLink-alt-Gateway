from Gateway import Gateway
from Device import UnknownDeviceType
from SomfyRTS import SomfyRemoteType, SomfyRemoteInstance
from RA20RF import RA20RFType
import logging
from flask import Flask
import threading


logging.getLogger().setLevel(logging.DEBUG)
gateway = Gateway()  #
app = Flask(__name__)


@app.route('/')
def index():
    return "Welcome to the RFLink-alt-gateway!"


@app.route('/commands', methods=['PUT','GET'])
def command():
    somfyType = gateway.get_device_type('SomfyRTS')
    remote = somfyType.get_instance("1003001")
    if not (remote is None):
        pulses = remote.stop()
        gateway.send(pulses)
    return "OK"


def thread_runner():
    print("Starting Flask")
    # app.run(debug=True, use_reloader=False)
    app.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    somfy = SomfyRemoteType()
    remote = SomfyRemoteInstance(1, 1003001)
    somfy.add_instance(remote)
    gateway.add_device_type(somfy)

    gateway.add_device_type(RA20RFType())

    gateway.add_device_type(UnknownDeviceType())

    threading.Thread(target=thread_runner).start()
    print("Starting Gateway")
    gateway.run(com_port="/dev/cu.usbmodem14101")
    print("Done?")
