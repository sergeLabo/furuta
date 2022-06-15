
"""
Le script principal à lancer.

L'environnement tourne dans ce process
Les codeurs et le moteur tournent dans des process individuels.

Pour la Pi avec routeur
[osc]
furuta_address = 192.168.1.2
furuta_port = 8000
env_address = 192.168.1.101
env_port = 8001

"""


import os
from time import time, time_ns, sleep
from multiprocessing import Process, Pipe
from threading import Thread

from oscpy.server import OSCThreadServer
import numpy as np

CLAVIER = 1
try:
    from pynput import keyboard
except:
    print("pynput ne peut pas être appelé.")
    CLAVIER = 0


from rotary_encoder import rotary_encoder_run
from motor_drive import mein_motor_run
from my_config import MyConfig

"""
Echap = Quit
a right
z left
i affichage des infos
b réglage codeur balancier
m réglage codeur moteur
up décalage +
down décalage -
t ???????????????????

"""


class Clavier:
    """Echap pour quitter proprement."""

    def __init__(self):
        self.key = None
        self.special = None
        self.quit = 0
        self.a = 0
        self.z = 0
        self.i = 0
        self.b = 0
        self.m = 0
        self.up = 0
        self.down = 0
        self.t = 0

        self.listener = keyboard.Listener(on_press=self.on_press,
                                     on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            self.key = key.char
            if self.key == "a":
                self.a = 1
            if self.key == "z":
                self.z = 1
            if self.key == "i":
                if self.i == 0:
                    self.i = 1
                else:
                    self.i = 0
            if self.key == "b":
                if self.b == 0: self.b = 1
                else: self.b = 0
            if self.key == "m":
                if self.m == 0: self.m = 1
                else: self.m = 0
            if self.key == "t":
                if self.t == 0: self.t = 1
                else: self.t = 0

        except AttributeError:
            if key.name == 'up':
                self.up = 1
            if key.name == 'down':
                self.down = 1

    def on_release(self, key):
        if key == keyboard.Key.esc:
            print("Stop keyboard listener: quit ...")
            self.quit = 1
            return False



class Furuta:
    global CLAVIER

    def __init__(self, cf):
        global CLAVIER
        self.cf = cf  # l'objet MyConfig
        self.config = cf.conf

        if CLAVIER:
            self.clavier = Clavier()
        else:
            self.clavier = None

        self.time_to_print = time()
        self.cycle = 0

        self.codeur_moteur_receive_loop = 1
        self.codeur_balanc_receive_loop = 1

        # alpha = moteur, teta = balancier
        self.alpha, self.alpha_dot, self.teta, self.teta_dot = 0, 0, 0, 0
        self.pile_codeurs_init()

        # Initialisation du moteur et des 2 codeurs
        self.codeur_moteur_init()
        self.codeur_balanc_init()
        self.position_codeurs_request_thread()
        self.moteur_init()

        # OSC
        self.env_address = self.config['osc']['env_address']
        self.env_port = int(self.config['osc']['env_port'])
        self.furuta_address = self.config['osc']['furuta_address']
        self.furuta_port = int(self.config['osc']['furuta_port'])
        self.create_osc_server()

    def create_osc_server(self):
        self.osc = OSCThreadServer()
        sock = self.osc.listen( address=self.furuta_address,
                                port=self.furuta_port,
                                default=True)

        @self.osc.address(b'/observation')
        def callback_observation(*values):
            # Furuta _ai me demande une observation, je la demande à furuta_hard
            # # self.position_codeurs_request()
            # A la fin de position_codeurs_request(), je suis à jour, je réponds
            self.osc.answer(b'/obs', [self.alpha,
                                      self.alpha_dot,
                                      self.teta,
                                      self.teta_dot,
                                      values[0]])
            if self.clavier.i:
                self.codeurs_settings()

        @self.osc.address(b'/impulse')
        def callback_impulse(*values):
            # # print("Impulsion demandée")
            puissance = values[0]
            lenght = values[1]
            sens = values[2].decode('utf-8')
            self.impulsion_moteur(puissance, lenght, sens)

        @self.osc.address(b'/recentering')
        def callback_recentering(*values):
            self.cycle += 1
            self.recentering()
            self.swing()

        @self.osc.address(b'/quit')
        def callback_quit(*values):
            self.quit()

    def codeurs_settings(self):
        """keyboard i affiche les infos,
        ensuite:
            - b permet de régler l'offset du codeur balancier
            - TODO m permet de régler l'offset du codeur moteur TODO
        Le réglage se fait avec flèches haut et bas.
        Couper l'alimentation moteur, et faire tourner à la main les codeurs
        pour passer par les points index.
        """
        a = round(self.alpha, 3)
        t = round(self.teta, 3)
        s = round(np.sin(self.teta), 3)
        c = round(np.cos(self.teta), 3)
        va = int(self.alpha_dot)
        vt = int(self.teta_dot)
        pa = self.pile_points_moteur[-1][0] - self.pile_points_moteur[0][0]
        pt = self.pile_points_balanc[-1][0] - self.pile_points_balanc[0][0]

        print(f"alpha {a:^8} "
              f"teta {t:^8} "
              f"sin teta {s:^8} "
              f"cos teta {c:^8} "
              f"écart des points alpha  {pa:^8} "
              f"écart des points teta {pt:^8}"
              f"vitesse alpha {va:^8} "
              f"vitesse teta {vt:^8} ")

        if self.clavier:
            if self.clavier.b:
                new = 0

                if self.clavier.up:
                    self.offset_bal += 1
                    new = 1
                    self.clavier.up = 0

                if self.clavier.down:
                    self.offset_bal -= 1
                    new = -1
                    self.clavier.down = 0

                if new == 1 or new == -1:
                    # Sauvegarde dans le fichier *.ini
                    self.cf.save_config('codeur_balancier', 'offset', self.offset_bal)
                    # Envoi à rotary_encoder balancier
                    self.codeur_balanc_conn.send(['offset', self.offset_bal, new])

            if self.clavier.m:
                new = 0

                if self.clavier.up:
                    self.offset_mot += 1
                    new = 1
                    self.clavier.up = 0

                if self.clavier.down:
                    self.offset_mot -= 1
                    new = -1
                    self.clavier.down = 0

                if new == 1 or new == -1:
                    # Sauvegarde dans le fichier *.ini
                    self.cf.save_config('codeur_moteur', 'offset', self.offset_mot)
                    # Envoi à rotary_encoder balancier
                    self.codeur_moteur_conn.send(['offset', self.offset_mot, new])

    def codeur_moteur_init(self):
        """Codeur moteur"""
        print("Initialisation du codeur du moteur")
        gpioA = int(self.config['codeur_moteur']['gpioa'])
        gpioB = int(self.config['codeur_moteur']['gpiob'])
        gpioIndex = int(self.config['codeur_moteur']['index'])
        offset = int(self.config['codeur_moteur']['offset'])
        self.offset_mot = offset
        self.codeur_moteur_conn, self.child_codeur_moteur_conn = Pipe()

        self.codeur_moteur = Process(target=rotary_encoder_run,
                                     args=(self.child_codeur_moteur_conn,
                                           'moteur',
                                           gpioA,
                                           gpioB,
                                           gpioIndex,
                                           offset))
        self.codeur_moteur.start()

    def codeur_balanc_init(self):
        """Codeur balancier"""
        print("Initialisation du Codeur balancier")

        gpioA = int(self.config['codeur_balancier']['gpioa'])
        gpioB = int(self.config['codeur_balancier']['gpiob'])
        gpioIndex = int(self.config['codeur_balancier']['index'])
        offset = int(self.config['codeur_balancier']['offset'])
        self.offset_bal = offset
        self.codeur_balanc_conn, self.child_codeur_balanc_conn = Pipe()
        self.codeur_balanc = Process(target=rotary_encoder_run,
                                     args=(self.child_codeur_balanc_conn,
                                           'balancier',
                                           gpioA,
                                           gpioB,
                                           gpioIndex,
                                           offset, ))
        self.codeur_balanc.start()

    def moteur_init(self):
        print("Initialisation du moteur ...")

        PWM = int(self.config['moteur']['pwm'])
        left = int(self.config['moteur']['left'])
        right = int(self.config['moteur']['right'])
        freq_pwm = int(self.config['moteur']['freq_pwm'])
        range_pwm = int(self.config['moteur']['range_pwm'])

        self.motor_conn, self.child_motor_conn = Pipe()
        self.motor = Process(target=mein_motor_run,
                             args=( self.child_motor_conn,
                                    PWM, left, right, freq_pwm, range_pwm))
        self.motor.start()

    def pile_codeurs_init(self):
        t = time_ns()
        # Piles: index 0 = le plus ancien, index -1 = le plus récent
        # # self.pile_points_moteur = [(0, t), (0, t), (0, t), (0, t), (0, t),
                                   # # (0, t), (0, t), (0, t), (0, t), (0, t),
                                   # # (0, t), (0, t), (0, t), (0, t), (0, t),
                                   # # (0, t), (0, t), (0, t), (0, t), (0, t)]
        # # self.pile_points_balanc = [(0, t), (0, t), (0, t), (0, t), (0, t),
                                   # # (0, t), (0, t), (0, t), (0, t), (0, t),
                                   # # (0, t), (0, t), (0, t), (0, t), (0, t),
                                   # # (0, t), (0, t), (0, t), (0, t), (0, t)]

        self.pile_points_moteur = [(0, t), (0, t), (0, t), (0, t), (0, t),
                                   (0, t), (0, t), (0, t), (0, t), (0, t)]

        self.pile_points_balanc = [(0, t), (0, t), (0, t), (0, t), (0, t),
                                   (0, t), (0, t), (0, t), (0, t), (0, t)]

    def position_codeurs_request_thread(self):
        t = Thread(target=self.position_codeurs_request)
        t.start()

    def position_codeurs_request(self):
        """Récupération des valeurs codeurs toutes les 0.004 s = 4 ms"""
        print("Le thread de demande des positions est lancé")

        while self.codeur_moteur_receive_loop and self.codeur_balanc_receive_loop:

            self.codeur_moteur_conn.send(['position'])
            self.codeur_balanc_conn.send(['position'])
            .write()

            done = 0
            okm, okb = 0, 0
            # J'attends la réponse
            while not done:

                datam = self.codeur_moteur_conn.recv()
                if datam[0] == 'codeur_position' and okm == 0:
                    points_moteur = (datam[1], time_ns())
                    self.pile_points_moteur.append(points_moteur)
                    del self.pile_points_moteur[0]
                    okm = 1

                datab = self.codeur_balanc_conn.recv()
                if datab[0] == 'codeur_position' and okb == 0:
                    points_balanc = (datab[1], time_ns())
                    self.pile_points_balanc.append(points_balanc)
                    del self.pile_points_balanc[0]
                    okb = 1

                if okm == 1 and okb == 1:
                    done = 1

                sleep(0.0001)

            self.alpha, self.alpha_dot, self.teta, self.teta_dot = self.shot()
            sleep(0.001)

            # Pour réglage seulement
            if self.clavier:
                # Affichage des infos
                if self.clavier.i:
                    if time() - self.time_to_print > 0.5:
                        self.codeurs_settings()
                        self.time_to_print = time()

                # Test moteur
                if self.clavier.a:
                    self.clavier.a = 0
                    self.impulsion_moteur(60, 0.05, 'right')
                if self.clavier.z:
                    self.clavier.z = 0
                    self.impulsion_moteur(60, 0.05, 'left')


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
        puissance = puissance de l'impulsion: 1 à 255
        lenght = durée de l'impulsion
        sens = left ou right
        """
        # Sécurité pour ne pas emballer le moteur
        ratio_puissance_maxi = float(self.config['furuta']['ratio_puissance_maxi'])
        range_pwm = int(self.config['moteur']['range_pwm'])
        puissance_maxi = ratio_puissance_maxi * range_pwm

        if puissance > puissance_maxi:
            puissance = puissance_maxi

        length_maxi = float(self.config['furuta']['length_maxi'])
        if lenght > length_maxi:
            lenght = length_maxi

        self.motor_conn.send(['impulsion', sens, puissance])
        sleep(lenght)
        self.motor_conn.send(['stop'])

    def shot(self):
        """Récupération de l'état du pendule.
        alpha = moteur
        teta = balancier
        Retourne alpha, alpha_dot, teta, teta_dot
            angle en rd
            vitesse angulaire en rd/s
        """

        # Dernières valeurs
        alpha = self.points_to_alpha(self.pile_points_moteur[-1][0])
        time_alpha = self.points_to_alpha(self.pile_points_moteur[-1][1])
        teta = self.points_to_teta(self.pile_points_balanc[-1][0])
        time_teta = self.points_to_teta(self.pile_points_balanc[-1][1])

        # Anciennes valeurs
        alpha_old = self.points_to_alpha(self.pile_points_moteur[0][0])
        time_alpha_old = self.points_to_alpha(self.pile_points_moteur[0][1])
        teta_old = self.points_to_teta(self.pile_points_balanc[0][0])
        time_teta_old = self.points_to_teta(self.pile_points_balanc[0][1])

        # Vitesse
        delta_alpha = alpha - alpha_old
        delta_time_alpha = (time_alpha - time_alpha_old) * 1e-9
        if delta_time_alpha != 0:
            alpha_dot = delta_alpha / delta_time_alpha
        else:
            alpha_dot = 0

        delta_teta = teta - teta_old
        delta_time_teta = (time_teta - time_teta_old) * 1e-9
        if delta_time_teta != 0:
            teta_dot = delta_teta / delta_time_teta
        else:
            teta_dot = 0

        return alpha, alpha_dot, teta, teta_dot

    def recentering(self):
        """Recentrage du chariot si trop décalé soit plus de 2rd"""
        ratio_puissance_maxi = float(self.config['furuta']['ratio_puissance_maxi'])
        range_pwm = int(self.config['moteur']['range_pwm'])
        puissance_maxi = int(ratio_puissance_maxi * range_pwm)

        # alpha de 0 à 3.14
        alpha_old = self.alpha

        n = 0
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
        # Swing
        ratio_puissance_maxi = float(self.config['furuta']['ratio_puissance_maxi'])
        range_pwm = int(self.config['moteur']['range_pwm'])
        puissance_maxi = int(ratio_puissance_maxi * range_pwm)

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

        self.osc.send_message(b'/recentering_done', [1], self.env_address, self.env_port)

    def quit(self):
        print("Quit dans Furuta")
        self.motor_conn.send(['quit'])
        self.motor_conn.send(['quit'])
        self.codeur_moteur_conn.send(['quit'])
        self.codeur_balanc_conn.send(['quit'])

        self.codeur_moteur_receive_loop = 0
        self.codeur_balanc_receive_loop = 0
        sleep(0.2)
        del self.motor
        del self.codeur_balanc
        del self.codeur_moteur
        print("Fin")
        os._exit(0)



def main():
    cf = MyConfig('./furuta_hard.ini')
    mf = Furuta(cf)



if __name__ == '__main__':

    main()
