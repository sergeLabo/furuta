
"""
L'environnement du Furuta pour gym et stable-baselines3

Pour le MSI et routeur
furuta_address = 192.168.1.2
furuta_port = 8000
env_address = 192.168.1.101
env_port = 8001

"""

import os, sys
from time import time, sleep, time_ns
from threading import Thread
from datetime import datetime
import json
from pathlib import Path

from oscpy.server import OSCThreadServer
import numpy as np
from pynput import keyboard
import gym
from gym import spaces


from my_config import MyConfig



class Clavier:
    """Echap pour quitter proprement."""

    def __init__(self):

        self.quit = 0
        self.j = 0

        self.listener = keyboard.Listener(on_press=self.on_press,
                                          on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            # # print(f'alphanumeric key {key.char} pressed')
            self.key = key.char
            if self.key == "j":
                if self.j == 0: self.j = 1
                else: self.j = 0

        except AttributeError:
            self.special = key.name

    def on_release(self, key):
        if key == keyboard.Key.esc:
            print("Stop listener: quit")
            self.quit = 1
            return False


class FurutaEnv(gym.Env):
    """step: observation, calcul d'IA, action et on recommence
    cycle: 2000 steps
    alpha: angle du chariot en rd
    teta: angle du balancier en rd
    vitesse angulaire en rd/s
    reward: récompense
    Un apprentissage = quelques millions de steps, ~1000 cycles
    """

    def __init__(self, config_obj, numero):

        super().__init__()

        self.config_obj = config_obj
        self.config = config_obj.conf
        self.numero = numero

        self.clavier = Clavier()

        # OSC
        self.furuta_address = self.config[self.numero]['furuta_address']
        self.furuta_port = int(self.config[self.numero]['furuta_port'])
        self.env_address = self.config[self.numero]['env_address']
        self.env_port = int(self.config[self.numero]['env_port'])
        self.create_osc_server()
        self.observation_done = 0
        self.recentering_done = 0

        # en degré dans le furuta.ini
        alpha_maxi_R = int(self.config[self.numero]['alpha_maxi_r'])
        alpha_maxi_L = int(self.config[self.numero]['alpha_maxi_l'])
        # en radian
        self.alpha_maxi_R = np.pi*(alpha_maxi_R/180)
        self.alpha_maxi_L = np.pi*(alpha_maxi_L/180)

        # Valeur par défaut
        self.alpha = 0
        self.teta = 0
        self.alpha_dot = 0
        self.teta_dot = 0

        # Actions possibles sur le moteur
        self.continu = int(self.config[self.numero]['continu'])
        range_pwm = int(self.config[self.numero]['range_pwm'])
        ratio_puissance_maxi = float(self.config[self.numero]['ratio_puissance_maxi'])
        self.puissance_maxi = int(ratio_puissance_maxi * range_pwm)

        # Durée de l'impulsion sur le moteur
        self.lenght = float(self.config[self.numero]['lenght'])

        # Nombre de steps maxi par cycle
        self.step_maxi = int(self.config[self.numero]['step_maxi'])
        self.learning_steps = int(self.config[self.numero]['learning_steps'])

        # Attente entre impulsion et observation
        self.tempo = float(self.config[self.numero]['tempo'])

        # Nombre total de step
        self.step_total = int(self.config[self.numero]['step_total'])

        self.current_step = 0  # comptage des steps pendant un cycle
        self.cycle_number = 0 # suivi du nombre de cycle
        self.batch_step = 0  # nombre de step réalisé pour un batch
        self.t_step = time_ns()  # calcul du temps par step
        self.cycle_reward = 0  # Efficacité du cycle
        self.efficiency = 0
        self.reason = ""

        # Datas enregistrés
        self.datas = []
        self.datas_dir = f"./datas/datas_{self.numero}"
        if not os.path.exists(self.datas_dir):
            os.makedirs(self.datas_dir)
            print(f"Création de {self.datas_dir}")

        # Création des espaces observations et actions
        self.observation_space, self.action_space = self.get_spaces()

        # Debug
        self.synchro = ""

    def get_spaces(self):
        """Définition des espaces:

        Espace possible des observations:
            finfo(dtype) Machine limits for floating point types
            numpy.finfo(numpy.float32) = finfo(resolution=1e-06,
                                         min=-3.4028235e+38,
                                         max=3.4028235e+38,
                                         dtype=float32)
            ici np.finfo(np.float32).max = 3.4028235e+38 ça fait grand

        Espace possible des ations:
            * entre -80 et 80
            * pas de space négatif
            * il faudra appliquer -80 à l'action pour l'impulsion sur le moteur
        """
        high = np.array([   np.finfo(np.float32).max,
                            np.finfo(np.float32).max,
                            np.finfo(np.float32).max,
                            np.finfo(np.float32).max,
                            np.finfo(np.float32).max])
        observation_space = spaces.Box(-high, high)

        if not self.continu:
            action_space = spaces.Discrete(2*self.puissance_maxi)
        else:
            action_space = spaces.Box( low=-1, high=1, shape=(1,), dtype=np.float32)

        return observation_space, action_space

    def create_osc_server(self):
        self.osc = OSCThreadServer()
        sock = self.osc.listen( address=self.env_address,
                                port=self.env_port,
                                default=True)

        @self.osc.address(b'/obs')
        def callback_obs(*values):
            self.alpha = values[0]
            self.alpha_dot = values[1]
            self.teta = values[2]
            self.teta_dot = values[3]
            self.observation_done = 1
            self.synchro = f" envoyé {self.current_step:^6} reçu {values[4]:^6}"

        @self.osc.address(b'/recentering_done')
        def callback_recentering_done(*values):
            self.recentering_done = 1

    def recentering(self):
        """Envoi en OSC d'une demande de recentering"""
        self.osc.send_message(  b'/recentering',
                                [1],
                                self.furuta_address,
                                self.furuta_port)

    def impulsion_moteur(self, puissance, lenght, sens):
        """Envoi en OSC d'une demande d'impulsion"""
        self.osc.send_message(  b'/impulse',
                                [puissance, lenght, sens],
                                self.furuta_address,
                                self.furuta_port)

    def observation_request(self):
        """Envoi de la demande d'observation au Furuta hadware"""
        self.osc.send_message(  b'/observation',
                                [self.current_step],
                                self.furuta_address,
                                self.furuta_port)

    def quit(self):
        """Envoi en OSC d'une demande de quit"""
        self.osc.send_message(  b'/quit',
                                [1],
                                self.furuta_address,
                                self.furuta_port)
        self.osc.stop_all()

    def reset(self):
        """Fin d'un cycle
        Crée des positions et vitesses aléatoires,
        retourne l'observation à la fin  du reset.
        Définition de l'état des chariot/balancier por un nouveau cycle
        Début d'un nouveau cycle
        """

        self.recentering()
        while not self.recentering_done:
            sleep(0.001)
        self.recentering_done = 0
        # Attente pour que le chariot ait le temps de se recenter
        sleep(0.1)

        # Observation de l'état de départ
        obs = np.array([np.float(self.alpha),
                        np.float(self.alpha_dot),
                        np.float(np.cos(self.teta)),
                        np.float(np.sin(self.teta)),
                        np.float(self.teta_dot)])

        e = 0
        if self.current_step > 10:
            e = (self.cycle_reward/self.current_step)
        self.efficiency = round(e, 3)

        dt_now = datetime.now()
        dt = dt_now.strftime("%d-%m-%Y | %H:%M")
        print( f"{dt} Reset: {self.reason:<16} "
                f"Step du batch = {self.batch_step}/{self.learning_steps} "
                f"Total des steps = {self.step_total:<10} "
                f"Cycle = {self.cycle_number:<6} "
                f"Efficacité = {e:<5.3f}")
        self.datas.append([self.step_total, self.efficiency])

        self.cycle_number += 1
        self.current_step = 0
        self.cycle_reward = 0

        return obs

    def save_efficiency(self):
        """Enregistrement de * step_total, cycle_reward"""
        if self.step_total % 10000 == 9999:
            if self.datas:
                dt_now = datetime.now()
                dt = dt_now.strftime("%d-%m-%Y | %H:%M")
                fichier = f"{self.datas_dir}/eff_{self.step_total}.json"
                print(f"Enregistrement de: {fichier} à {dt}")
                with open(fichier, 'w') as f:
                    d = json.dumps(self.datas)
                    f.write(d)
                self.datas = []

    def step(self, action):
        """Un step dans un cycle
                * action sur le moteur
                * attente
                * observation de l'état
                    soit postion et vitesse du chariot et du balancier
                * calcul de la récompense

            Arrêt du cycle si:
                * step_maxi atteint
                * chariot en bout de course
        """

        if not self.continu:
            # Si action de 0 à 160, impulsion de -80 à 80, sens left si < 0
            puissance = int(action - self.puissance_maxi)
        else:
            # action entre -1 et 1, puissance entre -400 et 400
            puissance = int(action * self.puissance_maxi)

        if puissance < 0:
            sens = 'left'.encode('utf-8')
        else:
            sens = 'right'.encode('utf-8')
        puissance = abs(puissance)

        # Impulsion envoyée en OSC
        self.impulsion_moteur(puissance, self.lenght, sens)

        # Attente, qui doit être plus grande que self.lenght
        sleep(self.tempo)

        # Demande d'une observation
        self.observation_request()
        # Attente de la réponse
        # # n = 0
        while not self.observation_done:
            sleep(0.0001)
        # Remise à zéro tout de suite
        self.observation_done = 0

        # Si done est True, arrêt du cycle
        done = False

        # Done avec step_maxi atteint
        if self.current_step > self.step_maxi:
            done = True
            self.reason = f"Step maxi"

        # Done avec chariot trop loin
        if self.alpha < -self.alpha_maxi_R or self.alpha > self.alpha_maxi_L:
            done = True
            self.reason = f"alpha = {self.alpha:.2f}"

        rewards = self.get_reward()
        self.cycle_reward += rewards

        if self.clavier.j:
            tttt = int((time_ns() - self.t_step)/1000000)
            self.t_step = time_ns()
            a = round(self.alpha, 3)
            t = round(self.teta, 3)
            s = round(np.sin(self.teta), 3)
            c = round(np.cos(self.teta), 3)
            va = int(self.alpha_dot)
            vt = int(self.teta_dot)
            ssss = sens.decode('utf-8')
            if ssss == 'left': ssss = 'left '

            print(f"Num {self.current_step:^7} "
                  f"action {action:^4}  puissance {puissance:^6} "
                  f"sens {ssss} "
                  f"alpha {a:^7} teta {t:^7} "
                  f"sin teta {s:^7} cos teta {c:^7} "
                  f"vitesse alpha {va:^9} vitesse teta {vt:^9} "
                  f"rewards {round(rewards, 3):^6} "
                  f"Step {self.current_step:^6} {self.synchro} "
                  f"Durée {tttt:^4}")

        # Observation de l'état: alpha = chariot, teta = balancier
        obs = np.array([np.float(self.alpha),
                        np.float(self.alpha_dot),
                        np.float(np.cos(self.teta)),
                        np.float(np.sin(self.teta)),
                        np.float(self.teta_dot)])

        self.current_step += 1
        self.step_total += 1
        self.batch_step += 1
        self.save_efficiency()

        return obs, rewards, done, {}

    def get_reward(self):
        """Calcul de la récompense.
        Chariot: 1 au centre, 0 au bout
            *
        Balancier: 0 en bas, 1 en haut
            * en bas teta = 0
            * en haut teta = +- 180° = +- pi = +- 3.14159
        """
        # Chariot
        # alpha négatif à droite, positif à gauche
        if self.alpha < 0:  # droite
            alpha_maxi = self.alpha_maxi_R
        else:
            alpha_maxi = self.alpha_maxi_L

        # Rapporté à la partie d'angle
        alpha_cor = (self.alpha * (np.pi/2)) / (alpha_maxi)
        reward_alpha = np.cos(alpha_cor)

        # Balancier
        # 0 ou 2pi --> 1
        # pi ou -pi --> 0
        reward_teta = np.sin(self.teta/2)

        # La récompense entre 0 et 1
        reward = abs(reward_teta * reward_alpha)

        return reward

    def render(self):
        """Doit exister pour gym"""
        pass

    def close(self):
        print("Close environnement.")
        self.quit()



if __name__ == '__main__':
    cf = MyConfig('./furuta.ini')
    FurutaEnv(cf.conf)
