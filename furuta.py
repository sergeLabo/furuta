
import os
from time import time, sleep
from threading import Thread
from pathlib import Path
import binascii

# # from crc import CrcCalculator, Crc16
import numpy as np
import pigpio

from my_config import MyConfig
from motor import MyMotor
from spi_comm import SPI_Comm



class Furuta:
    """Liens entre la Pi et le Furuta hardware, ESP32, motor."""

    def __init__(self, cf, numero, clavier):
        """cf: l'objet de configuration, objet MyConfig
        numero: string du numéro d'apprentissage = section dans *.ini
        clavier: capture input clavier, objet Clavier
        """

        self.cf = cf  # l'objet MyConfig
        self.numero = numero
        self.clavier = clavier
        self.clavier_active = 1
        self.clavier_thread()

        self.config = cf.conf  # le dict de conf
        self.pi = pigpio.pi()

        # L'objet Comm SPI
        self.spi_comm = SPI_Comm(cf, numero, self.pi, clavier)

        # alpha = moteur, teta = balancier
        self.alpha, self.alpha_dot, self.teta, self.teta_dot = 0, 0, 0, 0

        PWM = int(self.config['moteur']['pwm'])
        left = int(self.config['moteur']['left'])
        right = int(self.config['moteur']['right'])
        freq_pwm = int(self.config['moteur']['freq_pwm'])
        self.range_pwm = int(self.config[self.numero]['range_pwm'])
        self.ratio_puissance_maxi = float(self.config[self.numero]['ratio_puissance_maxi'])
        self.duration_maxi = float(self.config['moteur']['duration_maxi'])

        self.duration_of_motor_impulse = float(self.config[self.numero]['duration_of_motor_impulse'])
        # L'objet d'action sur le moteur
        self.motor = MyMotor(self.pi, PWM, left, right, freq_pwm, self.range_pwm)

        self.time_to_print = time()
        self.cycle = 0

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

    def shot(self):
        """Appelé par train_test.py pour obtenir une observation.
        Récupère les infos sur l'ESP32 pos1, pos2, speeds1, speeds2, puis
        défini self.alpha, self.teta, self.alpha_dot, self.teta_dot
        """

        pos1, pos2, speeds1, speeds2 = self.spi_comm.get_rotary_encoder_datas()

        self.alpha = self.points_to_alpha(pos2)
        self.teta = self.points_to_teta(pos1)

        try:
            self.alpha_dot = int(100000 / (sum(speeds2) / len(speeds2)))
        except:
            self.alpha_dot = 0

        try:
            self.teta_dot = int(100000 / (sum(speeds1) / len(speeds1)))
        except:
            self.teta_dot = 0

    def points_to_alpha(self, points):
        """Conversion des points en radians du chariot
        4000 points pour 2PI rd
        """
        # Conversion de 0 à 2*pi
        a = (np.pi * points / 2000) % 2*np.pi
        # De -pi à pi
        return a  - np.pi

    def points_to_teta(self, points):
        """Conversion des points en radians du balancier
        16000 points pour 2PI rd
        """
        return (np.pi * points / 8000) % 2*np.pi

    def impulsion_moteur(self, puissance, duration, sens):
        """Envoi d'une impulsion au moteur
        puissance = puissance de l'impulsion: 1 à range_pwm
        duration = durée de l'impulsion moteur: duration_of_motor_impulse
        sens = left ou right
        """
        # Sécurité pour ne pas emballer le moteur
        puissance_maxi = self.ratio_puissance_maxi * self.range_pwm
        if puissance > puissance_maxi:
            puissance = puissance_maxi
        if duration > self.duration_maxi:
            duration = self.duration_maxi

        self.motor.motor_run(puissance, sens)
        # Stop du moteur dans duration seconde
        sleep(duration)
        self.motor.stop()

    def recentering(self):
        """Recentrage du chariot si trop décalé par rapport au centre,
        impulsion proportionnelle à l'écart à zéro.
        """
        puissance_maxi = int(self.ratio_puissance_maxi * self.range_pwm)

        # pour print
        alpha_old = self.alpha

        # # n = 0
        # TODO à revoir
        # # while self.alpha > 0.5 and n < 5:
        # # n += 1
        pr = abs(int(puissance_maxi*self.alpha*1.2))
        duration = 0.10
        sens = 'right'
        if self.alpha > 0:
            sens = 'left'
        self.impulsion_moteur(pr, duration, sens)
        # Attente de la fin du recentrage
        sleep(1)
        print(f"{self.cycle} Recentrage de {pr} sens {sens} "
              f"alpha avant: {round(alpha_old, 2)} "
              f"alpha après {round(self.alpha, 2)}")

    def swing(self):
        """Un swing: des impulsion moteur pour placer le pendule dans une
        position aléatoire après un reset.
        """
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
        """Quitter proprement avec Echap,
        sinon les instances pigpio ne sont pas arrêtées, or elles sont limitées
        à 32
        """
        self.motor.cancel()
        # Fin du thread clavier
        self.clavier_active = 0
        # Attente pour que le moteur stoppe
        sleep(0.5)
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
    while i < 200:
        i += 1
        furuta.shot()
        sleep(0.1)

    furuta.quit()
