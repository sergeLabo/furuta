
from time import time, sleep
from smbus2 import SMBus


addr = 42
bus = SMBus(1)
sleep(1)
E = 0

def request():
    global E
    try:
        b2 = bus.read_i2c_block_data(addr, 0, 4)
        b = bytearray(b2)
        pos = (b[0] << 8) + b[1]
    except IOError:
        pos = None
        E += 1
    return pos

t = time()
n = -1
e = 0
nbr = 1000
print("Speed Test ...")
while n < nbr:
    n += 1
    pos1 = request()
    sleep(0.01)
    pos2 = request()
    sleep(0.025)
    if pos1 and pos2 and nbr % 2 == 0:
        print(pos2 - pos1)


d = ((((time() - t)/nbr) - 0.035)*1000)
print("Temps de transmission", round(d, 1), "ms")
print("Nombre d'erreur:", E)
bus.close()

