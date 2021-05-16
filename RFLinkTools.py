from math import ceil


def length(pulses):
    return sum(pulses)


# converts a byte array into a bit string
def bytes_to_bits(bytes_):
    return ''.join(format(byte, '08b') for byte in bytes_)


# converts a bit string into a byte array
def bits_to_bytes(bits):
    bytes_ = [bits[8 * i:8 * (i + 1)] for i in range(ceil(len(bits) / 8))]
    bytes_ = [int(i, 2) for i in bytes_]
    return bytes_


# converts pulse  string into an integer array
# "100,100,200,100" -> [100,100,200,100]
def string_to_pulses(pulse_string: str):
    return list(map(int, pulse_string.split(',')))


# encodes a bitstring into pulses suitable for RFLink-alt
# The preamble (integer array) is required because it is
# needed for the encoding context
# For example: "1010" becomes [100,200,200,200,100] (pulse time = 100)
def encode_manchester(bits, pulse_time: int, preamble):
    # convert the bit-string to symbols

    if len(preamble) == 0:
        raise Exception("preamble is required for encoding")
    else:
        if len(preamble) % 2 == 0:
            # even number of pulses so the last pulse must be a LOW
            last_bit = "0"
        else:
            # odd number of pulses so the last pulse must be a HIGH
            last_bit = "1"
        s = 0

    pulses = preamble.copy()

    for i in range(s, len(bits)):
        b = bits[i]
        if b != last_bit:
            pulses[-1] += pulse_time
            pulses.append(pulse_time)
        else:
            pulses.append(pulse_time)
            pulses.append(pulse_time)
        last_bit = b

    return pulses


# decodes pulses into a bitstring
# the pulses, an integer array, should be stripped from preamble.
# For example: [100,200,200,200,100] becomes "1010" (pulse time = 100)
def decode_manchester(pulses, pulse_time: int, last_bit: int = 0):
    symbols = ""  # '1' is High, '0' is Low

    # pulse length boundaries, 15% tolerance
    min_pulse_time = pulse_time * 0.85
    max_pulse_time = pulse_time * 1.15

    # each bit is encoded either High-Low(0) or Low-High(1)
    # But the first pulse can be longer than 1 * pulse time
    # because of a preamble
    if pulses[0] >= max_pulse_time:
        pulses[0] = pulse_time

    s = last_bit ^ 1
    for pulse in pulses:
        if min_pulse_time <= pulse <= max_pulse_time:
            symbols += str(s)
            s = s ^ 1
        elif 2 * min_pulse_time <= pulse <= 2 * max_pulse_time:
            symbols += str(s)
            symbols += str(s)
            s = s ^ 1
        else:
            raise Exception("Invalid pulse length")

    if len(symbols) % 2 != 0:
        # add a trailing low
        symbols += "0"

    bits = ""
    for i in range(0, len(symbols), 2):
        symbol = symbols[i:int(i + 2)]
        if symbol == "01":
            bits += "1"
        elif symbol == "10":
            bits += "0"
        else:
            raise Exception("Invalid encoding")

    return bits
