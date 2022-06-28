
from time import time, sleep
from threading import Thread
from pathlib import Path
from multiprocessing import Process, Pipe
from multiprocessing.sharedctypes import Value

import numpy as np
import pigpio

from my_config import MyConfig
from motor import MyMotor
from rotary_encoder import rotary_encoder_run



class Furuta:
    """Liens entre la Pi et le Furuta hardware."""

    def __init__(self, cf, numero, clavier):
        """cf: l'objet de configuration, objet MyConfig
        numero: string du numéro d'apprentissage = section dans *.ini
        clavier: capture input clavier, objet Clavier
        """

        self.cf = cf  # l'objet MyConfig
        self.numero = numero

        # Capture du clavier si ce script est éxcécuté ici
        if __name__ == '__main__':
            self.clavier = clavier
            self.clavier_active = 1
            print(f"Lancement du thread clavier, pour test moteur.")
            self.clavier_thread()

        self.config = cf.conf  # le dict de conf
        self.pi = pigpio.pi()

        self.init_motor()
        self.init_codeur_moteur()
        self.init_codeur_balancier()

    def init_motor(self):
        PWM = int(self.config['moteur']['pwm'])
        left = int(self.config['moteur']['left'])
        right = int(self.config['moteur']['right'])
        freq_pwm = int(self.config['moteur']['freq_pwm'])
        self.range_pwm = int(self.config[self.numero]['range_pwm'])
        self.ratio_puissance_maxi = float(self.config[self.numero]['ratio_puissance_maxi'])
        self.duration_maxi = float(self.config['moteur']['duration_maxi'])

        # L'objet d'action sur le moteur
        self.motor = MyMotor(self.pi, PWM, left, right, freq_pwm, self.range_pwm)

    def init_codeur_moteur(self):
        """Objet du codeur Moteur"""
        gpioA_m = int(self.config['codeur_moteur']['gpioa'])
        gpioB_m = int(self.config['codeur_moteur']['gpiob'])
        index_m = int(self.config['codeur_moteur']['index'])
        offset_m = int(self.config['codeur_moteur']['offset'])
        self.shared_value_moteur = Value("i", -4000)
        self.codeur_moteur_conn, child_conn1 = Pipe()
        self.codeur_moteur = Process(target=rotary_encoder_run,
                                     args=(child_conn1,
                                           self.shared_value_moteur,
                                           'moteur',
                                           gpioA_m,
                                           gpioB_m,
                                           index_m,
                                           offset_m, ))
        self.codeur_moteur.start()
        print(f"Codeur moteur lancé.")

    def init_codeur_balancier(self):
        """Objet du codeur balancier"""
        gpioA_b = int(self.config['codeur_balancier']['gpioa'])
        gpioB_b = int(self.config['codeur_balancier']['gpiob'])
        index_b = int(self.config['codeur_balancier']['index'])
        offset_b = int(self.config['codeur_balancier']['offset'])
        self.shared_value_balanc = Value("i", -4000)
        self.codeur_balancier_conn, child_conn2 = Pipe()
        self.codeur_balancier = Process(target=rotary_encoder_run,
                                        args=(child_conn2,
                                              self.shared_value_balanc,
                                              'balancier',
                                               gpioA_b,
                                               gpioB_b,
                                               index_b,
                                               offset_b, ))
        self.codeur_balancier.start()
        print(f"Codeur balancier lancé.")

    def shot(self):
        """Appelé par train_test.py pour obtenir une observation.
        Retourne alpha, teta
        """
        points_alpha = self.shared_value_moteur.value
        a = self.points_to_alpha(points_alpha)

        points_teta  = self.shared_value_balanc.value
        t = self.points_to_teta(points_teta)

        return a, t

    def points_to_alpha(self, points):
        """Conversion des points en radians du chariot
        1000 points pour 2PI rd
        """
        a = (np.pi * points) / 500
        return a

    def points_to_teta(self, points):
        """Conversion des points en radians du balancier
        4000 points pour 2PI rd
        """
        t = (np.pi * points) / 500
        return t

    def impulsion_moteur(self, puissance, duration, sens):
        """Envoi d'une impulsion au moteur
        puissance = puissance de l'impulsion: 1 à range_pwm
        duration = durée de l'impulsion moteur
        sens = left ou right
        """
        # Sécurité pour ne pas emballer le moteur
        puissance_maxi = self.ratio_puissance_maxi * self.range_pwm
        if puissance > puissance_maxi:
            puissance = puissance_maxi
        if duration > self.duration_maxi:
            duration = self.duration_maxi

        self.do_impulsion(puissance, duration, sens)

    def do_impulsion(self, puissance, duration, sens):
        t = Thread(target=self.do_impulsion_thread,
                     args=(puissance, duration, sens,))
        t.start()

    def do_impulsion_thread(self, puissance, duration, sens):
        self.motor.motor_run(puissance, sens)
        # Stop du moteur dans duration seconde
        sleep(duration)
        self.motor.stop()

    def recentering(self, alpha):
        """Recentrage du chariot si trop décalé par rapport au centre,
        impulsion proportionnelle à l'écart à zéro.
        """
        puissance_maxi = int(self.ratio_puissance_maxi * self.range_pwm)

        pr = abs(int(puissance_maxi*alpha*1.2))
        duration = 0.10
        sens = 'right'
        if alpha > 0:
            sens = 'left'
        self.impulsion_moteur(pr, duration, sens)

        # Attente de la fin du recentrage
        sleep(1)
        print(f"alpha= {round(alpha, 2)} Recentrage de {pr} sens {sens}")

    def clavier_thread(self):
        """Capture des événement clavier toutes les 0.2 s"""

        c = Thread(target=self.clavier_loop, )
        c.start()

    def clavier_loop(self):
        """Boucle de Capture des événement clavier toutes les 0.2 s"""

        while self.clavier_active:
            if self.clavier.a == 1:
                self.impulsion_moteur(50, 0.05, 'right')
                self.clavier.a = 0
            if self.clavier.z == 1:
                self.impulsion_moteur(50, 0.05, 'left')
                self.clavier.z = 0
            sleep(0.2)

    def quit(self):
        """Quitter proprement avec Echap,
        sinon les instances pigpio ne sont pas arrêtées, or elles sont limitées
        à 32
        """
        self.motor.cancel()
        # Attente pour que le moteur stoppe
        sleep(0.2)
        self.codeur_moteur_conn.send(['quit', 1])
        self.codeur_balancier_conn.send(['quit', 1])
        sleep(0.2)
        self.codeur_moteur.terminate()
        self.codeur_balancier.terminate()
        # Fin du thread clavier
        self.clavier_active = 0
        print("pigpio stoppé proprement ...")
        self.pi.stop()
        print("... Fin.")



if __name__ == '__main__':

    from clavier import Clavier

    current_dir = str(Path(__file__).parent.absolute())
    print("Dossier courrant:", current_dir)

    ini_file = current_dir + '/furuta.ini'
    print("Fichier de configuration:", ini_file)

    cf = MyConfig(ini_file)
    numero = "100"
    clavier = Clavier()
    furuta = Furuta(cf, numero, clavier)
    i = 0
    while i < 1:
        i += 1
        # # furuta.shot()
        furuta.motor.motor_run(35, 'left')
        sleep(10)
        furuta.motor.stop()

        if clavier.quit:
            furuta.quit()
    furuta.quit()
