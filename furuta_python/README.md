# Furuta Python

Version du soft de pilotage du pendule tout en python

###Documentation complémentaire
* [Toutes les pages sur le petit pendule de Furuta @ resources.labomedia.org](https://resources.labomedia.org)

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
Lancè avec "Testing"

Le model testé est le "102".\\
Il est possible de changer ce choix dans les options, mais vous devez être sûr que votre model est bon !


### GUI
Pour une utilisation simple du pendule par un néophyte en IA (Hi..Han..)
