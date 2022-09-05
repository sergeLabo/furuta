
"""
De Arduino en debug:

Read (0x3FFF) with command: 0b1111111111111111
Read returned: 1101110100001010
Setting error bit
3433
Read (0x3FFF) with command: 0b1111111111111111
Read returned: 101110100000111
Setting error bit
3432

"""

from time import time, sleep
import pigpio

CE = 8

pi = pigpio.pi()
sensor = pi.spi_open(0, 1000000, 1)

dt = 0.0001

pi.write(CE, 1)
sleep(dt)

t0 = time()
n = -1
nbr = 1000
tempo = 0.03
while n < nbr:
    n += 1
    pi.write(CE, 0)
    sleep(dt)

    # Envoi de 0b1111111111111111
    c, d = pi.spi_xfer(sensor, int.to_bytes(65535, 2, 'big'))
    if c == 2:
        val = (d[0] & 0b00111111) << 8 | d[1]
        angle = int(val/4)

    if n % 2 == 0:
        print(angle)

    pi.write(CE, 1)

    sleep(tempo)

pi.stop()

periode = ((time() - t0) / nbr) - tempo
print("periode =", round(periode, 4))
sleep(1)

"""
periode = 0.0019
~ 2 ms
"""
