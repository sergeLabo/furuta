
"""
Interface graphique pour conduire le pendule
"""

from time import sleep
import subprocess
from multiprocessing import Process, Pipe
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
Window.size = (680, 320)
from kivy.uix.screenmanager import ScreenManager, Screen

from train_test import testing, training
from my_config import MyConfig

# TODO améliorer les couleurs
# TODO gestion des batchs
# TODO sécurité sur les options possilbles
# TODO
# TODO



class MainScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.testing_conn = None
        self.training_conn = None
        self.testingP = None
        self.trainingP = None
        self.block = 0

    def do_testing(self):
        if not self.block:
            self.block = 1
            current_dir = str(Path(__file__).parent.absolute())
            print("Dossier courrant:", current_dir)
            ini_file = current_dir + '/furuta.ini'
            print("Fichier de configuration:", ini_file)
            config_obj = MyConfig(ini_file)
            numero = self.app.config.get('testing', 'numero')

            self.testing_conn, child_conn = Pipe()
            # current_dir, config_obj, numero, conn
            self.testingP = Process( target=testing,
                                     args=(current_dir,
                                           config_obj,
                                           numero,
                                           child_conn, ))
            self.testingP.start()
            print("Process Testing lancé")

    def on_stop_testing_training(self):

        if self.testing_conn is not None:
            print("Envoi de testing_loop=0")
            self.testing_conn.send(['continue', 0])
            self.testingP.terminate()
            self.testing_conn = None

        elif self.training_conn is not None:
            print("Envoi de training_loop=0")
            self.training_conn.send(['continue', 0])
            self.trainingP.terminate()
            self.training_conn = None

        # Je débloque pour nouveau choix
        self.block = 0

    def do_training(self):
        if not self.block:
            self.block = 1
            current_dir = str(Path(__file__).parent.absolute())
            print("Dossier courrant:", current_dir)
            ini_file = current_dir + '/furuta.ini'
            print("Fichier de configuration:", ini_file)
            config_obj = MyConfig(ini_file)
            numero = self.app.config.get('training', 'numero')

            self.training_conn, child_conn = Pipe()
            self.trainingP = Process( target=training,
                                      args=(current_dir,
                                            config_obj,
                                            numero,
                                            child_conn, ))
            self.trainingP.start()
            print("Process Training lancé")

    def do_quit(self):
        self.app.do_quit()

    def do_shutdown(self):
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])



class ChoiceScreen(Screen):
    pass



SCREENS = { 0: (MainScreen, 'Main'),
            1: (ChoiceScreen, 'Choice')}


class FurutaGuiApp(App):

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
        settings.add_json_panel('Furuta', self.config, data=data)

    def do_quit(self):
        scr = self.screen_manager.get_screen('Main')
        try:  # ils n'ont pas été forcément lancé
            scr.testing_conn.send(['testing_loop', 0])
            sleep(0.5)
            scr.testingP.terminate()
            scr.trainingP.terminate()
        except:
            pass
        # Kivy
        print("Quit final")
        FurutaGuiApp.get_running_app().stop()



if __name__ == '__main__':
    FurutaGuiApp().run()
