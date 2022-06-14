
"""
Vérification que le furuta hard fonctionne bien
"""


import os
from time import time_ns, sleep
from multiprocessing import Process, Pipe
from threading import Thread

import numpy as np
from pynput import keyboard

from furuta import Furuta
from my_config import MyConfig



class Clavier:
    """Echap pour quitter proprement.

        s stop du controle
        a à gauche
        z à droite
        c controle codeurs
        r recentrage
        v vitesse
        i index
    """

    def __init__(self):
        self.key = None
        self.special = None
        self.ici_quit = 0
        self.a = 0
        self.z = 0
        self.s = 0
        self.r = 0
        self.c = 0
        self.f = 0
        self.g = 0
        self.h = 0
        self.j = 0
        self.v = 0
        self.i = 0
        self.puissance = 30
        self.listener = keyboard.Listener(on_press=self.on_press,
                                     on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            # # print(f'alphanumeric key {key.char} pressed')
            self.key = key.char
            if self.key == "a":
                self.a = 1
            if self.key == "z":
                self.z = 1
            if self.key == "s":
                if not self.s:
                    self.s = 1
                else:
                    self.s = 0
            if self.key == "v":
                if not self.v:
                    self.v = 1
                else:
                    self.v = 0
            if self.key == "r":
                self.r = 1
            if self.key == "c":
                if not self.c:
                    self.c = 1
                else:
                    self.c = 0
            if self.key == "f":
                self.f = 1
            if self.key == "g":
                self.g = 1
            if self.key == "h":
                self.h = 1
            if self.key == "j":
                self.j = 1
            if self.key == "r":
                self.r = 1
            if self.key == "p":
                self.puissance += 1
            if self.key == "m":
                self.puissance -= 1
            if self.key == "i":
                if not self.i:
                    self.i = 1
                else:
                    self.i = 0

        except AttributeError:
            self.special = key.name

    def on_release(self, key):
        if key == keyboard.Key.esc:
            print("Stop listener: quit")
            self.ici_quit = 1
            return False



class FurutaControl(Clavier, Furuta):

    def __init__(self, cf):

        self.cf = cf
        self.config = self.cf.conf

        Clavier.__init__(self)
        Furuta.__init__(self, self.config)
        self.control_thread()

        self.offset_a = int(self.config['codeur_moteur']['offset'])
        self.offset_t = int(self.config['codeur_balancier']['offset'])

    def control_thread(self):
        t = Thread(target=self.control)
        t.start()

    def control(self):
        """
        s stop du controle
        a à gauche
        z à droite
        c controle codeurs
        r recentrage
        i controle index
        """
        while not self.ici_quit:
            if self.a:
                self.a = 0
                self.impulsion_moteur(self.puissance, 0.10, 'left')
                print(f"impulsion à gauche {self.puissance}")

            if self.z:
                self.z = 0
                self.impulsion_moteur(self.puissance, 0.10, 'right')
                print(f"impulsion à droite")

            if self.c:
                a = round(self.alpha, 4)
                t = round(self.teta, 4)

                # # if self.f:
                    # # # Offset codeur moteur diminue
                    # # self.offset_a -= 1
                    # # self.cf.save_config('codeur_moteur', 'offset', self.offset_a)

                # # if self.g:
                    # # # Offset codeur moteur augmente
                    # # self.offset_a += 1
                    # # self.cf.save_config('codeur_moteur', 'offset', self.offset_a)

                # # if self.h:
                    # # # Offset codeur balancier diminue
                    # # self.offset_t -= 1
                    # # self.cf.save_config('codeur_moteur', 'offset', self.offset_t)

                # # if self.j:
                    # # # Offset codeur moteur augmente
                    # # self.offset_t += 1
                    # # self.cf.save_config('codeur_moteur', 'offset', self.offset_t)

                print(f"Angles: Alpha {a:^8} Teta {t:^8}")
                sleep(0.1)

            if self.v:
                a = int(self.alpha_dot)
                t = int(self.teta_dot)
                if t != 0:
                    print(f"Vitesses: {a:^4} {t:^4}")

            if self.r:
                self.r = 0
                self.recentering()
                print(f"recentering")

            if self.i:
                if abs(self.alpha) < 0.01:
                    a = round(self.alpha, 4)
                    print(f"Index alpha: {a}")
                if abs(self.teta) < 0.01:
                    t = round(self.teta, 4)
                    print(f"Index teta: {t}")

            sleep(0.1)
        self.quit()



def main():
    cf = MyConfig('./furuta_hard.ini')
    mf = FurutaControl(cf)



if __name__ == '__main__':
    main()
