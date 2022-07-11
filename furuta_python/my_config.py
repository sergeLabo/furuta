
"""
Charge une configuration à partir d'un fichier *.ini
"""

# FIXME en cours de test!::

from configparser import SafeConfigParser


class MyConfig():
    """
    Charge la configuration depuis le fichier *.ini.
    Enregistre les changements par section, clé.
    Ajoute une section.
    """

    def __init__(self, ini_file, verbose=1):
        """
        Charge la config depuis un fichier *.ini
        Le chemin doit être donné avec son chemin absolu.
        """

        self.ini = ini_file
        self.verbose = verbose
        self.parser = None
        self.conf = {}
        self.load_config()


    def load_config(self):
        """Lit le fichier *.ini, et copie la config dans un dictionnaire."""

        self.parser = SafeConfigParser()
        self.parser.read(self.ini, encoding="utf-8")

        # Lecture et copie dans le dictionnaire
        for section_name in self.parser.sections():
            self.conf[section_name] = {}
            for key, value in self.parser.items(section_name):
                self.conf[section_name][key] = value

        if self.verbose:
            print(f"\nConfiguration chargée depuis {self.ini}")

        # Si erreur chemin/fichier
        if not self.conf:
            print("Le fichier de configuration est vide")

    def save_config(self, section, key, value):
        """
        Sauvegarde dans le fichioer *.ini  avec section, key, value.
        Uniquement int, float, str
        """

        if isinstance(value, int):
            val = str(value)
        if isinstance(value, float):
            val = str(value)
        if isinstance(value, str):
            val = value

        self.parser = SafeConfigParser()
        self.parser.read(self.ini)
        self.parser.set(section, key, val)

        with open(self.ini, "w") as f:
            self.parser.write(f)

        if self.verbose:
            print(f"Section={section} key={key} val={val} saved in {self.ini}\n")

    def add_section(section):

        self.parser.add_section(section)
        with open(self.ini, "w") as f:
            self.parser.write(f)
