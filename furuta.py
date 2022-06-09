
import os
from time import time, time_ns, sleep
from threading import Thread
# # import serial

import numpy as np
import pigpio

from my_config import MyConfig
from motor import MyMotor


class Furuta:
    """L'objet hardware."""

    def __init__(self, cf, numero, clavier):
        self.cf = cf  # l'objet MyConfig
        self.numero = numero
        self.clavier = clavier

        self.config = cf.conf  # le dict de conf
        self.pi = pigpio.pi()

        # # self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

        # alpha = moteur, teta = balancier
        self.alpha, self.alpha_dot, self.teta, self.teta_dot = 0, 0, 0, 0

        PWM = int(self.config['moteur']['pwm'])
        left = int(self.config['moteur']['left'])
        right = int(self.config['moteur']['right'])
        freq_pwm = int(self.config['moteur']['freq_pwm'])
        self.range_pwm = int(self.config[self.numero]['range_pwm'])
        self.ratio_puissance_maxi = float(self.config[self.numero]['ratio_puissance_maxi'])
        self.length_maxi = float(self.config['furuta']['length_maxi'])
        # L'objet d'action sur le moteur
        self.motor = MyMotor(self.pi, PWM, left, right, freq_pwm, self.range_pwm)

        self.time_to_print = time()
        self.cycle = 0

        self.sensor0 = self.pi.spi_open(0, 100000, 0)

        self.test = 1
        # # self.shot_test()

    def shot(self):
        """idem shot_test pour 1 appel"""

        if self.clavier.a == 1:
            self.impulsion_moteur(50, 0.05, 'right')
            self.clavier.a = 0
        if self.clavier.z == 1:
            self.impulsion_moteur(50, 0.05, 'left')
            self.clavier.z = 0
        if self.clavier.quit:
            self.quit()

        self.alpha, self.alpha_dot, self.teta, self.teta_dot = 0, 0, 0, 0
        return self.alpha, self.alpha_dot, self.teta, self.teta_dot

    def shot_test(self):
        while self.test:
            c0, d0 = self.pi.spi_xfer(self.sensor0, b"hello")
            print(c0, d0)
            # # if c0 == n:
                # # word0 = (d0[0] & 0b00111111) << 8 | d0[1]
                # # print(word0)
            if self.clavier.quit:
                self.quit()
            sleep(0.05)

        pi.spi_close(sensor0)
        sleep(0.1)
        pi.stop()
        # # while self.test:
            # # self.ser.write(b'obs')
            # # sleep(0.5)
            # # x = self.ser.readlines()
            # # print(x)

    def points_to_alpha(self, points):
        """Conversion des points en radians du chariot
        1000 points pour 360° soit 2PI rd
        """
        return  np.pi * points / 500

    def points_to_teta(self, points):
        """Conversion des points en radians du balancier
        4000 points pour 360° soit 2PI rd
        """
        return  np.pi * points / 2000

    def impulsion_moteur(self, puissance, lenght, sens):
        """Envoi d'une impulsion au moteur
        puissance = puissance de l'impulsion: 1 à range_pwm
        lenght = durée de l'impulsion
        sens = left ou right
        """
        # Sécurité pour ne pas emballer le moteur
        puissance_maxi = self.ratio_puissance_maxi * self.range_pwm

        if puissance > puissance_maxi:
            puissance = puissance_maxi

        if lenght > self.length_maxi:
            lenght = self.length_maxi

        self.motor.motor_run(puissance, sens)
        # Stop du moteur dans lenght seconde non bloquant
        self.wait_and_stop_thread(lenght)

    def wait_and_stop_thread(self, lenght):
        t = Thread(target=self.wait, args=(lenght,))
        t.start()

    def wait(self, some):
        """Attente de lenght, puis stop moteur"""
        sleep(some)
        self.motor.stop()

    def recentering(self):
        """Recentrage du chariot si trop décalé soit plus de 2rd"""
        puissance_maxi = int(self.ratio_puissance_maxi * self.range_pwm)

        # pour print
        alpha_old = self.alpha

        n = 0
        # TODO à revoir
        while self.alpha > 0.5 and n < 5:
            n += 1
            pr = abs(int(puissance_maxi*self.alpha*0.4))
            l = 0.10
            sens = 'right'
            if self.alpha > 0:
                sens = 'left'
            self.impulsion_moteur(pr, l, sens)
            # Attente de la fin du recentrage
            sleep(1)
            print(f"{self.cycle} Recentrage de {pr} sens {sens} "
                  f"alpha avant: {round(alpha_old, 2)} "
                  f"alpha après {round(self.alpha, 2)}")

    def swing(self):
        """Un swing"""
        puissance_maxi = int(self.ratio_puissance_maxi * self.range_pwm)

        sens = 'right'
        anti_sens = 'left'
        if self.alpha > 0:
            sens = 'left'
            anti_sens = 'right'

        ps = puissance_maxi * 0.4
        self.impulsion_moteur(ps, 0.08, sens)
        sleep(0.35)
        self.impulsion_moteur(ps, 0.1, anti_sens)
        sleep(0.05)
        print(f"{self.cycle} Swing {ps}")

    def quit(self):
        self.motor.cancel()
        self.test = 0
        print("Fin")
        os._exit(0)



def main():
    cf = MyConfig('./furuta.ini')
    mf = Furuta(cf)



if __name__ == '__main__':
    main()

"""
from time import time, sleep
import pigpio

pi = pigpio.pi()

freq = 1000000

# # pi.spi_close(0)
# # pi.spi_close(1)
sensor0 = pi.spi_open(0, freq, 0)

# # # MOSI=10
# # for i in [10]:
    # # a = pi.spi_write(sensor0, "1")
    # # sleep(0.01)
    # # print(a)

n = 8
while 1:
    # # count, rx_data = pi.spi_xfer(sensor0, b'\x01\x80\x00')
    # # print(count, rx_data)

    pi.spi_write(0, b'\x02\xc0\x80')

    c0, d0 = pi.spi_read(sensor0, n)
    print(c0, d0)
    # # if c0 == n:
        # # word0 = (d0[0] & 0b00111111) << 8 | d0[1]
        # # print(word0)
    sleep(0.1)

pi.spi_close(sensor0)
sleep(0.1)
pi.stop()
"""
