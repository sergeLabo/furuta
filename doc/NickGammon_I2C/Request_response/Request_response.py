
from time import sleep
from smbus2 import SMBus

# https://buildmedia.readthedocs.org/media/pdf/smbus2/latest/smbus2.pdf

addr = 42
bus = SMBus(1)

def request_position():
    global bus, addr
    try:
        b2 = bus.read_i2c_block_data(addr, 0, 2)
        b = bytearray(b2)
        pos = (b[0] << 8) + b[1]
    except IOError:
        pos = 0
    return pos

def write(value):
    """write_byte_data(i2c_addr, register, value, force=None)
    Write a byte to a given register.
    Parameters
    • i2c_addr (int) – i2c address
    • register (int) – Register to write to
    • value (int) – Byte value to transmit
    • force (Boolean) –
    Return type None
    """
    global bus, addr
    bus.write_byte(addr, value)

m = -1
nb = 10
while m < nb:
    m += 1

    if m % 2 == 0:
        # Demande de position
        write(0)
        print("Envoi de 0")
    else:
        write(1)
        print("Envoi de 1")
        pos = request_position()
        sleep(0.1)
        print("Position:", pos)
    sleep(1)

bus.close()
