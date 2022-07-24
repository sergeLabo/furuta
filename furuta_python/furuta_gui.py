
"""
Interface graphique pour domestiquer le pendule
"""

import os
from time import time, sleep
import subprocess
from multiprocessing import Process, Pipe
from pathlib import Path
from threading import Thread

from kivy.app import App
from kivy.core.window import Window
# # Window.size = (800, 480)
# # Window.fullscreen = True
Window.maximize()

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock

from train_test import testing, training
from my_config import MyConfig



class IntroScreen(Screen):
    """Ecran intro avec 1 image"""
    pass



class CreditsScreen(Screen):
    """Ecran credit avec 1 image"""
    pass



class AideScreen(Screen):
    """Ecran aide avec 1 image"""
    pass



class MainScreen(Screen):
    """Ecran principal avec 6 buttons"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def do_quit(self):
        self.app.do_quit()

    def do_shutdown(self):
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])



class TestingScreen(Screen):
    """Ecran affiché pendant un testing.
    Avec 4 buttons,
    Affiche quelques infos de suivi.
    Permet de passer à l'écran de choix d'un model à tester.
    """

    test_info = StringProperty('toto')

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.app = App.get_running_app()

        self.numero = self.app.config.get('testing', 'numero')
        self.block = 0
        self.testing_processus = None
        self.testing_conn = None
        self.testing_conn_loop = 0
        self.test_info = ""

    def enable_block(self):
        """Block si self.block == 1
        le bouton start est noir
        """
        self.block = 1
        # # self.ids.start.disable = True
        # # self.ids.start.background_color = (0,0,0,1)

    def disable_block(self):
        """Block si self.block == 1
        le bouton start est noir
        """
        self.block = 0
        # # self.ids.start.disable = False
        # # self.ids.start.background_color = (3.1, 0.8, 2.5, 1)

    def model_choice(self):
        self.stop_testing()
        sleep(1)
        self.app.screen_manager.current = 'TestingChoice'

    def start_testing(self):
        if not self.block:
            self.enable_block()
            current_dir = str(Path(__file__).parent.absolute())
            ini_file = current_dir + '/furuta.ini'
            config_obj = MyConfig(ini_file)

            self.testing_conn, child_conn = Pipe()
            self.testing_processus = Process(target=testing,
                                             args=(current_dir,
                                                   config_obj,
                                                   self.numero,
                                                   child_conn, ))
            self.testing_processus.start()
            print("Process Testing lancé")

            # Appel tous les 1 seconde
            Clock.schedule_interval(self.update_infos, 1)

    def update_infos(self, dt):
        if self.testing_conn is not None:
            self.testing_conn.send(['woke', 1])
            data = self.testing_conn.recv()
            if data:
                if data[0] == 'infos':
                    current_step = data[1]
                    cycle_reward = data[2]
                    self.set_infos(current_step, cycle_reward)

    def set_infos(self, current_step, cycle_reward):
        r = 0
        if current_step != 0:
            r = cycle_reward/current_step
        self.test_info = (f"[b]Model testé:  {self.numero}\n\n"
                           f"Step numéro:  {current_step}\n\n"
                           f"Récompense moyenne du cycle:  {round(r, 2)}[/b]")

    def retour(self):
        self.stop_testing()
        self.app.screen_manager.current = ("Main")

    def stop_testing(self):
        print("Stop testing demandé ...")
        if self.block:
            self.disable_block()
            if self.testing_conn is not None:
                print("Envoi de continue=0")
                self.testing_conn.send(['continue', 0])
            self.testing_processus.terminate()
            sleep(0.5)
            self.testing_conn = None
            self.testing_processus = None
            self.conn_loop = 0
            Clock.unschedule(self.update_infos)
        print(f"Stop testing ok.")



class TrainingScreen(Screen):

    train_info = StringProperty('toto')
    parts = NumericProperty(0)
    slider_value = StringProperty('0')

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.app = App.get_running_app()

        self.numero = self.app.config.get('training', 'numero')
        self.block = 0
        self.training_processus = None
        self.training_conn = None
        self.training_conn_loop = 0
        self.train_info = ""
        # Par défaut, on commence au début
        self.parts = 0
        self.slider_on_time = time()
        self.slider_thread_active = 0
        self.slider_value = f"Steps du model initial: 0"
        self.steps_from_beginning = 0
        self.steps_total = 0
        self.steps_init = 0

    def enable_block(self):
        """Block si self.block == 1
        le bouton start est noir
        """
        self.block = 1
        self.ids.start.disable = True
        self.ids.start.background_color = (0,0,0,1)

    def disable_block(self):
        """Block si self.block == 1
        le bouton start est noir
        """
        self.block = 0
        self.ids.start.disable = False
        self.ids.start.background_color = (3.1, 0.8, 2.5, 1)

    def do_slider(self, iD, instance, value):
        if self.block:
            self.stop_training()
            sleep(2)
            self.enable_block()

        if iD == 'parts':
            print(f"Slider {iD} {instance} {value}")
            self.parts = int(value)

            if self.parts == 0:
                d = 0
                self.steps_init = 0
            else:
                if self.parts == 1:
                    d = "100 000"
                    self.steps_init = 100000
                else:
                    d = f"{self.parts-1}00 000"
                    self.steps_init = (self.parts-1)*100000
            self.slider_value = f"Steps du model initial:  {d}"

            # Pas de modification de slider pendant 3 secondes pour être validé
            if not self.slider_thread_active:
                self.slider_thread_active = 1
                self.slider_on_time = time()
                self.slider_thread()
                print("slider_thread lancé")
            else:
                print("slider_on_time")
                self.slider_on_time = time()

    def slider_thread(self):
        t = Thread(target=self.slider_active)
        t.start()

    def slider_active(self):
        self.ids.start.background_color = (0,0,0,1)
        while time() - self.slider_on_time < 3:
            sleep(0.1)
        print("Déblockage du slider")
        self.ids.start.background_color = (3.1, 0.8, 2.5, 1)
        self.slider_thread_active = 0

    def start_training(self):
        if not self.block:
            current_dir = str(Path(__file__).parent.absolute())
            ini_file = current_dir + '/furuta.ini'
            config_obj = MyConfig(ini_file)

            self.training_conn, child_conn = Pipe()
            self.training_processus = Process(target=training,
                                             args=(current_dir,
                                                   config_obj,
                                                   self.numero,
                                                   child_conn,
                                                   self.parts ))
            self.training_processus.start()
            print("Process Training lancé")

            # Pour ne pas lancer 2 fois
            self.enable_block()

            # Appel tous les 1 seconde
            Clock.schedule_interval(self.update_infos, 1)

    def update_infos(self, dt):
        if self.training_conn is not None:
            self.training_conn.send(['woke', 1])
            data = self.training_conn.recv()
            if data:
                if data[0] == 'infos':
                    current_step = data[1]
                    cycle_reward = data[2]
                    self.steps_from_beginning = data[3]
                    self.set_infos(current_step, cycle_reward)

    def set_infos(self, current_step, cycle_reward):
        self.steps_total = self.steps_init + self.steps_from_beginning
        # Reward
        r = 0
        if current_step != 0:
            r = cycle_reward/current_step

        self.train_info = (f"[b]Steps totaux: {self.steps_total}\n"
                           f"Step du cycle:  {current_step}\n"
                           f"Récompense moyenne du cycle:  {round(r, 2)}[/b]")

    def stop_training(self):
        print("Stop training demandé ...")
        if self.block:
            self.disable_block()
            if self.training_conn is not None:
                print("Envoi de continue=0")
                self.training_conn.send(['continue', 0])
            if self.training_processus:
                self.training_processus.terminate()
            sleep(0.5)
            self.training_conn = None
            self.training_processus = None
            self.conn_loop = 0
            Clock.unschedule(self.update_infos)
        print(f"Stop training ok.")

    def retour(self):
        self.stop_training()
        self.app.screen_manager.current = ("Main")



SCREENS = { 0: (IntroScreen, 'Intro'),
            1: (MainScreen, 'Main'),
            2: (TestingScreen, 'Testing'),
            3: (TrainingScreen, 'Training'),
            4: (CreditsScreen, 'Credits'),
            5: (AideScreen, 'Aide')}

class FurutaApp(App):

    def build(self):
        """Construction des écrans"""
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))
        return self.screen_manager

    def build_config(self, config):
        """Excécuté en premier (ou après __init__()).
        Si le fichier *.ini n'existe pas,  il est créé avec ces valeurs par défaut.
        Il s'appelle comme le kv mais en ini
        Si il manque seulement des lignes, il ne fait rien !
        Cette méthode est obligatoire.
        """

        print("Création du fichier *.ini si il n'existe pas")

        config.setdefaults( 'training', {'numero': 103})
        config.setdefaults( 'testing',  {'numero': 102})

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options, pour Furuta seul,
        Les réglages Kivy sont par défaut.
        Cette méthode est appelée par app.open_settings() dans .kv,
        donc si Options est cliqué !
        """

        print("Construction de l'écran Options")

        data = """[ {   "type": "string",
                        "title": "Numero",
                        "desc": "Numero du model pour testing",
                        "section": "testing", "key": "numero"},

                    {   "type": "string",
                        "title": "Numero",
                        "desc": "Numero du model pour training",
                        "section": "training", "key": "numero"}
                    ]"""

        # self.config est le config de build_config
        settings.add_json_panel('Model', self.config, data=data)

    def on_config_change(self, config, section, key, value):
        pass

    def do_quit(self):
        # Kivy
        print("Quit final")
        FurutaApp.get_running_app().stop()




if __name__ == '__main__':
    FurutaApp().run()

# # class TestingChoiceScreen(Screen):
    # # """Sélection de test simple ou affiche un scroll pour changer le model"""
    # # def __init__(self, **kwargs):
        # # super().__init__(**kwargs)
        # # self.app = App.get_running_app()

    # # def select_model(self, model):
        # # """Si un model est choisi, retour à Testing pour ce model"""
        # # scr = self.app.screen_manager.get_screen('Testing')
        # # scr.numero = model
        # # self.app.screen_manager.current = 'Testing'
