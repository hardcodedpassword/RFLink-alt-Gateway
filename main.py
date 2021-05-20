from Gateway import Gateway
from Device import UnknownDeviceType
from SomfyRTS import SomfyRemoteType, SomfyRemoteInstance
from RA20RF import RA20RFType
import logging
from flask import Flask, request, jsonify
import threading

logging.getLogger().setLevel(logging.DEBUG)
gateway = Gateway()
app = Flask(__name__)


@app.route('/')
def index():
    return "Welcome to the RFLink-alt-gateway!"


@app.route('/command/<device_type>/<device_id>/<command>', methods=['GET'])
def command(device_type, device_id, command):
    try:
        dt = gateway.get_device_type(device_type)
        if dt is None:
            raise Exception('no such device type')
        di = dt.get_instance(device_id)
        if di is None:
            raise Exception('no such device instance')
        pulses = di.execute_command(command)
        gateway.send(pulses)
        return jsonify(result=True)
    except Exception as e:
        logging.info('command execution failed' + str(e))
        return jsonify(result=False, error=str(e))


@app.route('/devices', methods=['GET'])
def get_devices():
    devices = {}
    for device_type in gateway.device_types:
        devices[device_type.type_name] = []
        for device_instance in device_type.instances:
            devices[device_type.type_name].append(device_instance.id)
    return jsonify(devices=devices)


@app.route('/device_types', methods=['GET'])
def get_device_types():
    types = [t.type_name for t in gateway.device_types]
    return jsonify(device_types=types)


@app.route('/device_instances/<device_type>', methods=['GET'])
def get_device_instances(device_type):
    try:
        dt = gateway.get_device_type(device_type)
        if dt is None:
            raise Exception('no such device type')
        instances = [i.id for i in dt.instances]
        return jsonify(instances=instances)
    except Exception as e:
        logging.info('listing device instances failed' + str(e))
        return jsonify(error=str(e))


@app.route('/device_state/<device_type>/<device_id>', methods=['GET'])
def get_device_state(device_type, device_id):
    try:
        dt = gateway.get_device_type(device_type)
        if dt is None:
            raise Exception('no such device type')
        di = dt.get_instance(device_id)
        if di is None:
            raise Exception('no such device instance')
        return jsonify(result=True, state=di.get_state())
    except Exception as e:
        logging.info('getting device state failed' + str(e))
        return jsonify(result=False, error=str(e))


@app.route('/device_commands/<device_type>/<device_id>', methods=['GET'])
def get_device_commands(device_type, device_id):
    try:
        dt = gateway.get_device_type(device_type)
        if dt is None:
            raise Exception('no such device type')
        di = dt.get_instance(device_id)
        if di is None:
            raise Exception('no such device instance')
        return jsonify(result=True, state=di.get_commands())
    except Exception as e:
        logging.info('getting device commands failed' + str(e))
        return jsonify(result=False, error=str(e))


def thread_runner():
    logging.debug('Flask started')
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
    logging.debug('Gateway started')
    gateway.run(com_port="/dev/cu.usbmodem14101")
