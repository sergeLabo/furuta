# Furuta Python

Version du soft de pilotage du Petit Pendule tout en python

### Documentation complémentaire
* [Toutes les pages sur le petit pendule de Furuta @ resources.labomedia.org](https://resources.labomedia.org)

### Installation
* [Installer Raspberry Pi OS (64-bit)](https://www.raspberrypi.com/software/operating-systems/): le 64 bit est obligatoire car un des packages python n'existe qu'en 64 bit pour ARM.

#### Python
Dans le dossier [furuta/petit_furata](https://github.com/sergeLabo/furuta/petit_furata):
``` bash
python3 -m pip install -r requirements_minimal.txt
```
#### Autostart
Coller les fichiers de <br />
[autostart](https://github.com/sergeLabo/furuta/tree/main/furuta_python/autostart) <br />
dans <br />
~/.config/autostart

Coller les fichiers
[furuta_autostart.sh](https://github.com/sergeLabo/furuta/blob/main/furuta_python/furuta_autostart.sh) et [hdmi_autostart.sh](https://github.com/sergeLabo/furuta/blob/main/furuta_python/hdmi_autostart.sh) dans le home de la pi

Créer un lien furuta dans /usr/local/bin qui pointe vers [run_furuta_gui.sh](https://github.com/sergeLabo/furuta/blob/main/furuta_python/run_furuta_gui.sh)
``` bash
sudo ln -s /vers/le/dossier/furuta_python/run_furuta_gui.sh /usr/local/bin/furuta
```
Cela permet de lancer le pendule avec seulement la commande "furuta" en terminal!

### Convention

* alpha = angle du moteur, 0 vers l'avant
* droite = vous êtes assis sur le codeur balancier en regardant le balancier, doite est à votre droite
* gauche = de l'autre coté (et Lycée de Versailles)
* teta = angle du balancier, 0 en bas, pi (ou -pi) en haut


### Test du moteur
Test du moteur au clavier, en éxcécutant motor.py:
        - a impulsion à droite
        - z impulsion à gauche
    pendant 6 secondes.

### Réglage des codeurs
Pour vérifier que les valeurs de positions et vitesses sont logiques,
et régler les offsets des index.

### Vérification de tout le matériel
En exécutant furuta.py

### Test de l'environnement
En exécutant furuta_env.py

### Apprentissage = Training

Un apprentissage dure 3 millions de steps,
soit 30 batchs de 100 000 steps

### Test = Testing
Lancé avec "Testing"

Le model testé est le "102".<br />
Il est possible de changer ce choix dans les options, mais vous devez être sûr que votre model est bon !

### GUI
Pour une utilisation simple du pendule par un néophyte en IA (Hi..Han..)
