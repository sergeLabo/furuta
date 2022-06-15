
"""
Mise en forme des datas des coeurs US Digital

Encoder du moteur:

|2 | Index = 1 top par tour | 33 | GPIO13 |
|3 | A channel              | 35 | GPIO19 |
|5 | B channel              | 36 | GPIO16 |

Encoder du balancier:
|2 | Index = 1 top par tour | 29 | GPIO5  |
|3 | A channel              | 31 | GPIO6  |
|5 | B channel              | 32 | GPIO12 |
"""

import os
from time import time, sleep
from threading import Thread

import numpy as np
import pigpio

from my_config import MyConfig


class RotaryEncoder:
    """Class to decode mechanical rotary encoder pulses."""

    def __init__(self, conn, name, gpioA, gpioB, index, offset):
        """name = str pour reconnaitre le name
        gpioA pin du canal A
        gpioB pin du canal B
        index pin du top par tour
        """

        self.pi = pigpio.pi()
        self.conn = conn
        self.name = name
        self.gpioA = gpioA
        self.gpioB = gpioB
        self.index = index
        self.index_last_time = time()
        self.offset = offset
        self.sens = 0

        self.levA = 0
        self.levB = 0
        self.position = self.offset
        self.lastGpio_A_B = None
        self.last_index = None

        # Que des INPUT
        self.set_gpio_mode(gpioA, pigpio.INPUT)
        self.set_gpio_mode(gpioB, pigpio.INPUT)
        self.set_gpio_mode(index, pigpio.INPUT)

        # Callbacks                 numero pin, front montant ou descendant, appel method
        self.cbA = self.pi.callback(self.gpioA, pigpio.EITHER_EDGE, self.pulsation)
        self.cbB = self.pi.callback(self.gpioB, pigpio.EITHER_EDGE, self.pulsation)
        self.cbi = self.pi.callback(self.index, pigpio.RISING_EDGE, self.pulsation)

        # Thread de comm avec main
        self.encoder_conn_loop = 1
        if conn:
            self.encoder_receive_thread()

    def pulsation(self, gpio, level, tick):
        """Decode the rotary encoder pulse.


             +---------+         +---------+            1
             |         |         |         |
         B   |         |         |         |
             |         |         |         |
         ----+         +---------+         +---------+  0

                   +---------+         +---------+      1
                   |         |         |         |
         A         |         |         |         |
                   |         |         |         |
         +---------+         +---------+         +----- 0
                   +1  +1    +1  +1    +1  +1   +1  ... etc ....
                   B=1
                   A change d'état=valid +1
        """

        # Qui a changé d'état
        if gpio == self.gpioA:
            self.levA = level
        else:
            self.levB = level

        # Qui avait changé au top précédent, permet de bloquer après une prise en
        # compte d'un changement d'état
        if gpio != self.lastGpio_A_B:
            self.lastGpio_A_B = gpio

        # Sens positif et front montant
        if gpio == self.gpioA and level == 1:
            if self.levB == 1:
                self.position += 1
                self.sens = 1

        # Sens négatif et front montant
        elif gpio == self.gpioB and level == 1:
            if self.levA == 1:
                self.position -= 1
                self.sens = -1

        # RAZ sur index
        if gpio == self.index:
            # Que d'un coté
            if self.sens == 1:
                if self.position != self.offset:
                    # # print(f"RAZ position avant: {self.position:^8} offset: {self.offset:^8}")
                    self.position = self.offset

    def set_gpio_mode(self, gpio, mode):
        """gpio: de 0 à 53
        mode: INPUT, OUTPUT, ALT0, ALT1, ALT2, ALT3, ALT4, ALT5.
        """
        self.pi.set_mode(gpio, mode)

    def cancel(self):
        sleep(0.1)
        self.cbA.cancel()
        self.cbB.cancel()
        self.pi.stop()
        print("Rotary encoder Fin de", self.name)

    def encoder_receive_thread(self):
        """Si réception de position envoyé par Furuta(),
        retourne la position de ce codeur
        """
        print("Lancement du thread receive dans rotary_encoder")
        t = Thread(target=self.encoder_receive)
        t.start()

    def encoder_receive(self):
        """ Dérive: [957, 94, 999, 4, 991]
            Dérive: [3985, 2, 3996, 5, 21]
            [3998, 7, 3999, 23, 4, 3997, 22, 3984, 1145, 10, 3997, 7, 3867, 3229, 3832, 2936, 3226, 3931, 5, 2, 471, 8]
            [0, 20, 0, 7, 94, 81, 19, 4, 16, 1, 38, 0, 984, 911, 54, 995, 998, 7, 13, 8, 15, 0]
        """
        while self.encoder_conn_loop:
            data = self.conn.recv()

            if data:
                if data[0] == 'quit':
                    print("quit reçu dans rotary_encoder", self.name)
                    self.encoder_conn_loop = 0
                    self.cancel()

                if data[0] == 'position':
                    # Furuta() demande la position, je la retourne
                    self.conn.send(['codeur_position', self.position])

                if data[0] == 'offset':
                    # Furuta() donne un nouvel offset
                    self.offset = data[1]
                    self.position += data[2]

            # Furuta() attend la réponse
            sleep(0.0005)

        print("Fin du thread de l'encoder", self.name)
        os._exit(0)



def codeur_moteur_test():

    cf = MyConfig('./furuta_hard.ini')
    config = cf.conf

    gpioA = int(config['codeur_moteur']['gpioa'])
    gpioB = int(config['codeur_moteur']['gpiob'])
    gpioIndex = int(config['codeur_moteur']['index'])
    offset = int(config['codeur_moteur']['offset'])

    moteur = RotaryEncoder(None, "moteur", gpioA, gpioB, gpioIndex, offset)
    t = time()
    while time() - t < 600:
        print("position", moteur.position)
        sleep(0.1)

    moteur.cancel()


def codeur_balancier_test():

    cf = MyConfig('./furuta_hard.ini')
    config = cf.conf

    gpioA = int(config['codeur_balancier']['gpioa'])
    gpioB = int(config['codeur_balancier']['gpiob'])
    gpioIndex = int(config['codeur_balancier']['index'])
    offset = int(config['codeur_balancier']['offset'])

    balancier = RotaryEncoder(None, "balancier", gpioA, gpioB, gpioIndex, offset)
    t = time()
    while time() - t < 60:
        print("position", balancier.position)
        sleep(0.1)

    balancier.cancel()


def rotary_encoder_run(conn, name, gpioA, gpioB, index, offset):
    """Pour lancer depuis main.py en multiprocess"""

    enc = RotaryEncoder(conn, name, gpioA, gpioB, index, offset)



if __name__ == "__main__":
    # # codeur_moteur_test()
    codeur_balancier_test()
