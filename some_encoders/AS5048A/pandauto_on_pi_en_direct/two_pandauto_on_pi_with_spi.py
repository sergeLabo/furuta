
from time import time, sleep
import pigpio
from threading import Thread

CE0 = 8
CE1 = 7


def motor_run():
    sleep(0.03)
    print("motor off")


pi = pigpio.pi()
sensor = pi.spi_open(0, 1000000, 1)

dt = 0.00001

pi.set_mode(CE0, pigpio.INPUT)
pi.set_mode(CE1, pigpio.INPUT)
pi.write(CE0, 1)
pi.write(CE1, 1)
sleep(dt)

t0 = time()
n = -1
nbr = 1000
tempo0 = 0.02
tempo1 = 0.01
data = int.to_bytes(65535, 2, 'big')
while n < nbr:
    n += 1
    print("motor on")
    t = Thread(target=motor_run)
    t.start()

    sleep(tempo0)
    pi.write(CE0, 0)
    sleep(dt)
    c, d = pi.spi_xfer(sensor, data)
    if c == 2:
        val = (d[0] & 0b00111111) << 8 | d[1]
        angle0 = int(val/4)
    pi.write(CE0, 1)
    sleep(dt)
    pi.write(CE1, 0)
    sleep(dt)
    c, d = pi.spi_xfer(sensor, data)
    if c == 2:
        val = (d[0] & 0b00111111) << 8 | d[1]
        angle1 = int(val/4)
    pi.write(CE1, 1)

    sleep(tempo1)
    pi.write(CE0, 0)
    sleep(dt)
    c, d = pi.spi_xfer(sensor, data)
    if c == 2:
        val = (d[0] & 0b00111111) << 8 | d[1]
        angle2 = int(val/4)
    pi.write(CE0, 1)
    sleep(dt)
    pi.write(CE1, 0)
    sleep(dt)
    c, d = pi.spi_xfer(sensor, data)
    if c == 2:
        val = (d[0] & 0b00111111) << 8 | d[1]
        angle3 = int(val/4)
    pi.write(CE1, 1)

    v0 = angle2 - angle0
    v1 = angle3 - angle1
    print(angle0, angle1, angle2, angle3, v0, v1)

pi.stop()
periode = (((time() - t0) / nbr) - tempo)*1000  # ms
print("periode =", round(periode, 2), "ms")
sleep(1)
