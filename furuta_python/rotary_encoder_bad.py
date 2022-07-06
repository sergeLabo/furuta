
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
from pathlib import Path
# Voir
# https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
# # print('Running' if __name__ == '__main__' else 'Importing', Path(__file__).resolve())

import numpy as np
import pigpio

from my_config import MyConfig



class RotaryEncoder:
    """Class to decode mechanical rotary encoder pulses."""

    def __init__(self, shared_value, name, gpioA, gpioB, index, offset):
        """Il faut créer une nouvelle instance de pigpio.pi()

        pi: instance pigpio
        shared_value: entier en mémoire partagé
        name: str pour reconnaitre le name
        gpioA: pin du canal A
        gpioB: pin du canal B
        index: pin du top par tour
        """
        print(f"Lancement du codeur {name}")
        self.pi = pigpio.pi()
        self.shared_value = shared_value
        self.name = name
        self.gpioA = gpioA
        self.gpioB = gpioB
        self.index = index
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

    def pulsation(self, gpio, level, tick):
        """Decode the rotary encoder pulse.

             +---------+         +---------+            1
             |         |         |         |
         A   |         |         |         |
             |         |         |         |
         ----+         +---------+         +---------+  0
         000011111111110000000000111111111100000000000
                   +---------+         +---------+      1
                   |         |         |         |
         B         |         |         |         |
                   |         |         |         |
         +---------+         +---------+         +----- 0
          000000000111111111100000000001111111111000000

                 +1                    +1
        8 changement d'état = 2 points comptés
        """
        print("pulsation")
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
            if self.position != self.offset:
                d = self.position - self.offset
                self.position = self.offset

        if self.shared_value is not None:
            self.shared_value.value = self.position
            print(self.position)
        else:
            print("bad")

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



def rotary_encoder_run(shared_value, name, gpioA, gpioB, index, offset):
    """Pour lancer depuis main.py en multiprocess"""
    print(f"Création d'un objet RotaryEncoder pour {name}")
    enc = RotaryEncoder(shared_value, name, gpioA, gpioB, index, offset)


def codeur_test(lequel):

    current_dir = str(Path(__file__).parent.absolute())
    print("Dossier courrant:", current_dir)

    ini_file = current_dir + '/furuta.ini'
    print("Fichier de configuration:", ini_file)

    cf = MyConfig(ini_file)
    config = cf.conf

    lequel = 'codeur_' + lequel
    print(lequel)
    gpioA = int(config[lequel]['gpioa'])
    gpioB = int(config[lequel]['gpiob'])
    gpioIndex = int(config[lequel]['index'])
    offset = int(config[lequel]['offset'])

    pi = pigpio.pi()
    #                      shared_value, name, gpioA, gpioB, index, offset
    moteur = RotaryEncoder(None, "moteur", gpioA, gpioB, gpioIndex, offset)
    t = time()
    while time() - t < 20:
        print("position", moteur.position)
        sleep(0.1)

    moteur.cancel()


if __name__ == "__main__":
    codeur_test("moteur")
    # # codeur_test("balancier")
