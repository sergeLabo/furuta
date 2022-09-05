
"""
L'environnement du Furuta pour gym et stable-baselines3
"""

import os
from time import sleep, time_ns, time
from datetime import datetime
import json
import random
from pathlib import Path
from threading import Thread

import numpy as np
import gym
from gym import spaces

from my_config import MyConfig
from furuta_hard import Furuta
from clavier import Clavier



class FurutaEnv(gym.Env):
    """step: observation, calcul d'IA, action et on recommence
    cycle: 2046 steps
    alpha: angle du chariot en rd
    teta: angle du balancier en rd
    vitesse angulaire en rd/s
    reward: récompense
    Un apprentissage = quelques millions de steps, ~1000 cycles
    """

    def __init__(self, current_dir, config_obj, numero, conn):
        """receiver_thread() ne sert que si test et train lancé avec le gui

        """
        # TODO doc
        super().__init__()

        self.current_dir = current_dir
        self.config_obj = config_obj
        self.config = config_obj.conf
        self.numero = numero

        # Pipe avec GUI
        self.conn = conn
        self.continue_env = True
        self.conn_loop = 0
        self.GUI = 1
        if not self.GUI:
            self.clavier = Clavier()
        else:
            self.clavier = None

        # L'objet hardware furuta
        self.furuta = Furuta(config_obj, numero, self.clavier)

        # en radian dans le furuta.ini
        self.alpha_maxi_r = float(self.config[self.numero]['alpha_maxi_r'])
        self.alpha_maxi_l = float(self.config[self.numero]['alpha_maxi_l'])

        # Valeur par défaut
        self.alpha, self.teta, self.alpha_dot, self.teta_dot = 0, 0, 0, 0

        # Actions possibles sur le moteur
        range_pwm = int(self.config[self.numero]['range_pwm'])
        ratio_puissance_maxi = float(self.config[self.numero]['ratio_puissance_maxi'])
        self.puissance_maxi = int(ratio_puissance_maxi * range_pwm)

        # Durée de l'impulsion sur le moteur
        self.lenght = float(self.config[self.numero]['duration_of_motor_impulse'])

        # Nombre de steps maxi par cycle
        self.step_maxi = int(self.config[self.numero]['step_maxi'])

        # Optimisation de l'apprentissage tous les
        self.learning_steps = int(self.config[self.numero]['learning_steps'])

        # Attente entre la fin de l'impulsion et observation
        self.tempo = float(self.config[self.numero]['tempo_step'])

        # Nombre total de step
        self.step_total = int(self.config[self.numero]['step_total'])

        self.current_step = 0  # comptage des steps pendant un cycle
        self.cycle_number = 0 # suivi du nombre de cycle
        self.batch_step = 0  # nombre de step réalisé pour un batch
        self.t_step = time_ns()  # calcul du temps par step
        self.cycle_reward = 0  # Récompense totale en cours de cycle
        self.efficiency = 0  # Efficacité du cycle
        self.reason = ""  # pour affichage
        # steps depuis le début d'un apprentissage pour training GUI
        self.from_beginning = 0

        # Datas enregistrés
        self.datas = []
        self.datas_dir = f"{self.current_dir}/datas/datas_{self.numero}"
        if not os.path.exists(self.datas_dir):
            os.makedirs(self.datas_dir)
            print(f"Création de {self.datas_dir}")

        # Création des espaces observations et actions
        self.observation_space, self.action_space = self.get_spaces()

        # Debug
        self.synchro = ""
        self.t_block = time()

    def receiver_thread(self):
        """Thread pour recevoir le stop pendant le training"""
        t = Thread(target=self.receiver)
        self.conn_loop = 1
        t.start()

    def receiver(self):
        """Boucle infinie Thread pour recevoir le stop pendant le training"""
        print("Env Receiver ok")
        while self.conn_loop:
            # # print("toto")
            if self.conn is not None:
                data = self.conn.recv()
                # # print("data reçu dans furuta_env:", data)
                if data:
                    if data == ['continue', 0]:
                        print("Dans furuta_env, continue=0 reçu")
                        self.continue_env = False
                        self.conn_loop = 0
                    if data[0] == 'woke':
                        # # print("woke")
                        pass

                # Envoi des infos
                self.conn.send([ 'infos',
                                 self.current_step,
                                 int(self.cycle_reward),
                                 self.from_beginning])

            sleep(0.3)
        print("Fin du thread .receiver")

    def step(self, action):
        """Un step dans un cycle
                * action sur le moteur, défini par model.learn()
                * attente
                * observation de l'état
                    soit postion et vitesse du chariot et du balancier
                * calcul de la récompense

            Arrêt du cycle si:
                * step_maxi atteint
                * chariot en bout de course
        """
        if self.clavier:
            if self.clavier.quit:
                self.close()

        # Si action de 0 à 160, impulsion de -80 à 80, sens left si < 0
        puissance = int(action - self.puissance_maxi)

        if puissance < 0:
            sens = 'left'
        else:
            sens = 'right'
        puissance = abs(puissance)

        if self.furuta:  # pour ne pas demander d'impulsion si quit !
            self.furuta.impulsion_moteur(puissance, self.lenght, sens)

        self.alpha, self.alpha_dot, self.teta, self.teta_dot = self.get_pos_speed()

        # Si done est True, arrêt du cycle
        done = False

        # Done avec step_maxi atteint
        if self.current_step > self.step_maxi:
            done = True
            self.reason = f"Step maxi"

        # Done avec chariot trop loin
        if self.alpha > self.alpha_maxi_r or self.alpha < self.alpha_maxi_l:
            done = True
            self.reason = f"alpha = {self.alpha:.2f}"
            self.furuta.recentering(self.alpha)

        rewards = self.get_reward()
        self.cycle_reward += rewards

        # Observation de l'état: alpha = chariot, teta = balancier
        obs = np.array([np.float(self.alpha),
                        np.float(self.alpha_dot),
                        np.float(np.cos(self.teta)),
                        np.float(np.sin(self.teta)),
                        np.float(self.teta_dot)])

        self.from_beginning += 1
        self.current_step += 1
        self.step_total += 1
        self.batch_step += 1
        self.save_efficiency()
        self.print_infos(action, puissance, rewards, sens)

        return obs, rewards, done, {}

    def get_pos_speed(self):
        """L'impulsion moteur dure duration_of_motor_impulse = 0.02
        La 2ème observation doit être faite après la fin de l'impulsion.
        self.tempo est le temps entre la fin de l'impulsion moteur et
        la 2ème observation, tempo_step dans *.ini soit 0.01
        """
        # Attente pendant l'impulsion moteur
        sleep(self.lenght)  # 0.02
        # Shot
        a0, t0 = self.furuta.shot()

        sleep(self.tempo)  # 0.01
        a1, t1 = self.furuta.shot()

        alpha = a1
        if a1 - a0 != 0:
            alpha_dot = 0.01 / (a1 - a0)
        else:
            alpha_dot = 0

        teta = t1
        if t1 - t0 != 0:
            teta_dot = 0.01 / (t1 - t0)
        else:
            teta_dot = 0

        return alpha, alpha_dot, teta, teta_dot

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
            * entre -60 et 60
            * pas de space négatif
            * il faudra appliquer -60 à l'action pour l'impulsion sur le moteur
        """
        high = np.array([   np.finfo(np.float32).max,
                            np.finfo(np.float32).max,
                            np.finfo(np.float32).max,
                            np.finfo(np.float32).max,
                            np.finfo(np.float32).max])
        observation_space = spaces.Box(-high, high)

        action_space = spaces.Discrete(2*self.puissance_maxi)

        return observation_space, action_space

    def reset(self):
        """Reset à la fin d'un cycle:
            - Donne des infos sur le cycle terminé,
            - Retourne l'observation à la fin  du reset.
        """
        # Attente pour éviter les retards
        sleep(1)

        # Observation
        self.alpha, self.alpha_dot, self.teta, self.teta_dot = self.get_pos_speed()

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

    def print_infos(self, action, puissance, rewards, sens):
        """Affichage d'infos:
            - j pour les événements à chaque step
            - k pour alpha, teta, alpha', teta' en gros pour video
        """
        if self.clavier:
            if self.clavier.j:
                tttt = int((time_ns() - self.t_step)/1000000)
                self.t_step = time_ns()
                a = round(self.alpha, 3)
                ca = round(np.cos(self.alpha/2), 3)
                t = round(self.teta, 3)
                st = round(np.sin(self.teta/2), 3)
                va = round(self.alpha_dot, 3)
                vt = round(self.teta_dot, 3)
                if sens == 'left': sens = 'left '

                print(f"Num {self.current_step:^7} "
                      f"action {action:^4}  puissance {puissance:^6} "
                      f"sens {sens}    "
                      f"alpha {a:^7} teta {t:^7} "
                      f"cos_alpha/2 {ca:^7}"
                      f"sin_teta/2 {st:^7} "
                      f"rewards {round(rewards, 3):^6} "
                      f"vitesse_alpha {va:^9} vitesse_teta {vt:^9} "
                      f"Durée {tttt:^4}")
            if self.clavier.l:
                a = round(self.alpha, 1)
                t = round(self.teta, 1)
                va = round(self.alpha_dot, 3)
                vt = round(self.teta_dot, 3)
                print(f"a: {a:^7} t: {t:^7} va: {va:^7} vt: {vt:^7} ")

    def get_reward(self):
        """Calcul de la récompense.
        Chariot:
            * 1 au centre, 0 au bout
        Balancier: 0 en bas, 1 en haut
            * en bas teta = 0
            * en haut teta = +- 180° = +- pi = +- 3.14159
        """
        # Chariot
        reward_alpha = np.cos(self.alpha/2)

        # Balancier
        # 0 ou 2pi --> 1
        # pi ou -pi --> 0
        reward_teta = np.sin(self.teta/2)

        # La récompense entre 0 et 1
        reward = abs(reward_teta * reward_alpha)

        return reward

    def render(self):
        # TODO render() doit exister pour gym ?
        pass

    def close(self):
        print("Close environnement.")
        self.furuta.quit()
        sleep(0.5)



if __name__ == "__main__":
    """
    Test de ce script avec des valeurs d'actions au hasard
    """

    current_dir = str(Path(__file__).parent.absolute())
    print("Dossier courrant:", current_dir)
    ini_file = current_dir + '/furuta.ini'
    print("Fichier de configuration:", ini_file)
    cf = MyConfig(ini_file)

    fe = FurutaEnv(None, current_dir, cf , '100')

    while 1:
        action = random.randint(60, 100)
        fe.step(action)
