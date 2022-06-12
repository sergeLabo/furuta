
from pynput import keyboard


class Clavier:
    """Echap pour quitter proprement.

        Echap = Quit
        a motor right
        z motor left
        j suivi temps réel
        k print des temps
        l print des infos comm SPI
    """

    def __init__(self):
        self.key = None
        self.quit = 0
        self.a = 0
        self.z = 0
        self.j = 0
        self.k = 0
        self.l = 0
        self.m = 0

        self.listener = keyboard.Listener(on_press=self.on_press,
                                     on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            self.key = key.char
            if self.key == "a":  # moteur à droite
                self.a = 1
            if self.key == "z":  # moteur à gauche
                self.z = 1
            if self.key == "j":  # print valeurs en cours
                if self.j == 0:
                    self.j = 1
                else:
                    self.j = 0
            if self.key == "k":  # print temps
                if self.k == 0:
                    self.k = 1
                else:
                    self.k = 0
            if self.key == "l":  # print pour controle
                if self.l == 0:
                    self.l = 1
                else:
                    self.l = 0
            if self.key == "m":  # print controle datas réception
                if self.m == 0:
                    self.m = 1
                else:
                    self.m = 0

        except AttributeError:
            pass

    def on_release(self, key):
        if key == keyboard.Key.esc:
            print("Stop keyboard listener: quit ...")
            self.quit = 1
            return False
