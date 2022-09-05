
"""
Pilotage des apprentissages et tests
"""

from time import sleep
from datetime import datetime, timedelta
import json
import os, sys
from os.path import exists
from threading import Thread

from pathlib import Path

import gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from my_config import MyConfig
from furuta_env import FurutaEnv



class CustomCallback(BaseCallback):
    """ A custom callback that derives from ``BaseCallback``.
    :param verbose: (int) Verbosity level 0: not output 1: info 2: debug
    """
    def __init__(self, verbose=0):
        """Those variables will be accessible in the callback
        (they are defined in the base class).
        The RL model
            self.model = None  # type: BaseAlgorithm
        An alias for self.model.get_env(), the environment used for training
            self.training_env = None  # type: Union[gym.Env, VecEnv, None]
        Number of time the callback was called
            self.n_calls = 0  # type: int
            self.num_timesteps = 0  # type: int
        local and global variables
            self.locals = None  # type: Dict[str, Any]
            self.globals = None  # type: Dict[str, Any]
        The logger object, used to report things in the terminal
            self.logger = None  # stable_baselines3.common.logger
        Sometimes, for event callback, it is useful to have access to the parent object
            self.parent = None  # type: Optional[BaseCallback]
        """
        super().__init__()

    def _on_step(self):
        """This method will be called by the model after each call to `env.step()`.
        For child callback (of an `EventCallback`), this will be called
        when the event is triggered.
        :return: (bool) If the callback returns False, training is aborted early.
        """
        _continue = True
        if not self.model.env.envs[0].env.continue_env:
            print("Fin du training.")
            _continue = False
        return _continue


class TrainTest:

    def __init__(self, current_dir, config_obj, numero, conn):

        self.current_dir = current_dir
        # Mon object Config
        self.config_obj = config_obj
        # Le dict de la configuration
        self.config = config_obj.conf
        self.numero = numero  # str

        # Pipe
        self.conn = conn

        self.learning_steps = int(self.config[self.numero]['learning_steps'])
        self.learning_rate = float(self.config[self.numero]['learning_rate'])
        self.n_steps = int(self.config[self.numero]['n_steps'])
        self.batch_size = int(self.config[self.numero]['batch_size'])
        self.n_epochs = int(self.config[self.numero]['n_epochs'])
        self.gamma = float(self.config[self.numero]['gamma'])
        self.gae_lambda = float(self.config[self.numero]['gae_lambda'])
        self.clip_range = float(self.config[self.numero]['clip_range'])
        self.ent_coef = float(self.config[self.numero]['ent_coef'])
        self.vf_coef = float(self.config[self.numero]['vf_coef'])
        self.max_grad_norm = float(self.config[self.numero]['max_grad_norm'])

        self.model_name = f"ppo_neo_{self.numero}"
        print(f"Nom du model {self.model_name}")
        self.env = FurutaEnv(self.current_dir, self.config_obj, self.numero, self.conn)
        self.model = None

        self.model_file = f'{self.current_dir}/my_models/{self.model_name}.zip'
        print(f"Nom et chemin du model {self.model_file}")

        self.models_dir = f"{self.current_dir}/models/PPO{self.numero}"
        self.logdir = f"{self.current_dir}/logs"
        self.datas_dir = f"{self.current_dir}/datas/datas_{self.numero}"

        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            print(f"Création de {self.models_dir}")
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)
            print(f"Création de {self.logdir}")
        if not os.path.exists(self.datas_dir):
            os.makedirs(self.datas_dir)
            print(f"Création de {self.datas_dir}")

    def create_model(self):
        """https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html

        Parameters:
            policy: The policy model to use (MlpPolicy, CnnPolicy, …)
            env: The environment to learn from
            learning_rate: The learning rate, it can be a function of the
                            current progress remaining (from 1 to 0)
            n_steps: The number of steps to run for each environment per update
            batch_size: Minibatch size
            n_epochs: Number of epoch when optimizing the surrogate loss
            gamma: Discount factor
            gae_lambda: Factor for trade-off of bias vs variance
                        for Generalized Advantage Estimator
            clip_range: Clipping parameter, it can be a function
                        of the current progress remaining (from 1 to 0).
            clip_range_vf: Clipping parameter for the value function, it can be
                    a function of the current progress remaining (from 1 to 0).
                    This is a parameter specific to the OpenAI implementation.
                    If None is passed (default), no clipping will be done on the
                    value function.
                    IMPORTANT: this clipping depends on the reward scaling.
            normalize_advantage: Whether to normalize or not the advantage
            ent_coef: Entropy coefficient for the loss calculation
            vf_coef: Value function coefficient for the loss calculation
            max_grad_norm: The maximum value for the gradient clipping
            use_sde: Whether to use generalized State Dependent Exploration (gSDE)
                     instead of action noise exploration (default: False)
            sde_sample_freq: Sample a new noise matrix every n steps when using gSDE
                     Default: -1 (only sample at the beginning of the rollout)
            target_kl: Limit the KL divergence between updates, because the clipping
                       is not enough to prevent large update. By default,
                       there is no limit on the kl div.
            tensorboard_log: the log location for tensorboard (if None, no logging)
            create_eval_env: Whether to create a second environment that will be
                        used for evaluating the agent periodically.
                        (Only available when passing string for the environment)
            policy_kwargs: additional arguments to be passed to the policy on creation
            verbose: the verbosity level: 0 no output, 1 info, 2 debug
            seed: Seed for the pseudo random generators
            device: Device (cpu, cuda, …) on which the code should be run.
                    Setting it to auto, the code will be run on the GPU if possible.
            _init_setup_model: Whether or not to build the network at the creation
                               of the instance

        Valeurs par défaut:
        stable_baselines3.ppo.PPO(policy,
                                    env,
                                    learning_rate=0.0003,
                                    n_steps=2048,
                                    batch_size=64,
                                    n_epochs=10,
                                    gamma=0.99,
                                    gae_lambda=0.95,
                                    clip_range=0.2,
                                    clip_range_vf=None,
                                    normalize_advantage=True,
                                    ent_coef=0.0,
                                    vf_coef=0.5,
                                    max_grad_norm=0.5,
                                    use_sde=False,
                                    sde_sample_freq=- 1,
                                    target_kl=None,
                                    tensorboard_log=None,
                                    create_eval_env=False,
                                    policy_kwargs=None,
                                    verbose=0,
                                    seed=None,
                                    device='auto', _
                                    init_setup_model=True)
        """
        if not exists(self.model_file):
            print(f"Model créé: {self.model_name}")

            self.model = PPO(   policy="MlpPolicy",
                                env=self.env,
                                learning_rate=self.learning_rate,
                                n_steps=self.n_steps,
                                batch_size=self.batch_size,
                                n_epochs=self.n_epochs,
                                gamma=self.gamma,
                                gae_lambda=self.gae_lambda,
                                clip_range=self.clip_range,
                                clip_range_vf=None,
                                ent_coef=self.ent_coef,
                                vf_coef=self.vf_coef,
                                max_grad_norm=self.max_grad_norm,
                                use_sde = False,
                                sde_sample_freq = -1,
                                target_kl = None,
                                tensorboard_log = self.logdir,
                                verbose = 1,  # 0
                                seed = None,
                                device = "auto")
            self.save_model()
        else:
            print(f"Le modèle existe.")

    def print_model_info(self):
        if self.model:
            print(  f"\nCeci imprime tous les paramètres du model,"
                    f"donc ce qui définit le tenseur de poids\n"
                    f"{self.model.get_parameters()}\n"
                    f"self.env: {dir(self.env)}"
                    f"\nobservation_space: {self.env.observation_space}"
                    f"\naction_space:, {self.env.action_space}\n")
        else:
            print(f"Pas de model")

    def print_model_attr(self):
        """Default value:
            env = <stable_baselines3.common.vec_env.dummy_vec_env.DummyVecEnv object at 0x7f74faa31610>
            learning_rate = 0.0003
            n_steps = 2048
            batch_size = 64
            n_epochs = 10
            gamma = 0.99
            gae_lambda = 0.95
            clip_range = <function constant_fn.<locals>.func at 0x7f74faa25c10>
            clip_range_vf = None
            ent_coef = 0.0
            vf_coef = 0.5
            max_grad_norm = 0.5
            use_sde = False
            sde_sample_freq = -1
            target_kl = None
            tensorboard_log = None
            policy_kwargs = {}
            verbose = 0
            seed = None
            device = cpu
            """
        self.load_model()
        self.model.set_env(self.env)
        a = ["policy",
            "env",
            "learning_rate",
            "n_steps",
            "batch_size",
            "n_epochs",
            "gamma",
            "gae_lambda",
            "clip_range",
            "clip_range_vf",
            "ent_coef",
            "vf_coef",
            "max_grad_norm",
            "use_sde",
            "sde_sample_freq",
            "target_kl",
            "tensorboard_log",
            "policy_kwargs",
            "verbose",
            "seed",
            "device"]

        for b in a:
            print(b, "=", getattr(self.model, b))

    def save_model(self):
        self.model.save(self.model_file)
        print(f"\nModel sauvegardé: {self.model_name}\n")

    def load_model(self):
        self.model = PPO.load(self.model_file, cloudpickle=False, verbose=0)
        print(f"\nModel chargé: {self.model_name} soit {self.model_file}\n")

    def save_efficiency(self):
        """Enregistrement de * step_total, cycle_reward"""
        if self.env.datas:
            dt_now = datetime.now()
            dt = dt_now.strftime("%d-%m-%Y | %H:%M")
            num = self.env.step_total
            fichier = f"{self.datas_dir}/eff_{self.numero}_{num}.json"
            print(f"Enregistrement de: {fichier} à {dt}")
            with open(fichier, 'w') as f:
                d = json.dumps(self.env.datas)
                f.write(d)
            self.env.datas = []

    def training(self):
        """Training en lançant ce script.
        Un training complet c'est 30 batchs de 100 000 steps.

        1 batch = 100 000 steps
        A la fin du batch, sauvegarde du model, permet de stopper un training
        avant la fin, et de pouvoir le reprendre

        Si vous stoppez avant la fin, il faut déduire les batchs fait dans
        furuta.ini --> [numero] batch=xxx
        Le GUI fait cette gymnastique automatiquement.
        """
        # Reset du step_maxi, utile si a été modifié par un testing
        self.env.step_maxi = int(self.config[self.numero]['step_maxi'])

        TIMESTEPS = self.learning_steps
        batch = int(self.config[self.numero]['batch'])

        dt_now = datetime.now()
        dt = dt_now.strftime("%d-%m-%Y | %H:%M")
        # Temps en secondes du train complet.  periode = 35 ms 22 Hz
        t = int(batch * TIMESTEPS * 0.035)
        f = datetime.now() + timedelta(seconds=t)
        fin = f.strftime("%d-%m-%Y | %H:%M")
        print(f"\n\nApprentissage de {batch} batch de {TIMESTEPS} à {dt}. Fin à {fin}\n\n")

        for i in range(batch):
            self.load_model()
            self.model.set_env(self.env)
            dt_now = datetime.now()
            dt = dt_now.strftime("%d-%m-%Y | %H:%M")
            print(f"\nApprentissage n° {i+1} sur {batch} "
                  f"Steps total = {self.env.step_total} "
                  f"Learning steps = {self.learning_steps} Steps par cycle = "
                  f"{self.env.step_maxi} à {dt}\n")

            self.model.learn(total_timesteps=TIMESTEPS,
                             reset_num_timesteps=False,
                             tb_log_name=f"PPO{self.numero}")

            # sauvegarde incrementale
            self.model.save(f"{self.models_dir}/{TIMESTEPS*i}")

            # Un batch fait self.learning_steps Réinitialisation des steps du batch
            self.env.batch_step = 0

            # Enregistrement dans *.ini
            self.config_obj.save_config(self.numero, 'step_total', self.env.step_total)

            dt_now = datetime.now()
            dt = dt_now.strftime("%d-%m-%Y | %H:%M")
            print(f"\nSauvegarde du model {self.model_name} à {dt}")
            self.save_model()

            self.save_efficiency()
            # Destruction du model
            del self.model

        self.env.close()

    def testing(self):
        """Testing en lançant ce script.
        Ctrl+C pour quitter
        """
        # TODO améliorer
        print("Testing ...")
        self.load_model()
        self.model.set_env(self.env)
        obs = self.env.reset()
        while 1:
            action, _states = self.model.predict(obs)
            obs, rewards, dones, info = self.env.step(action)

    def testing_gui(self):
        """Testing en lançant avec le GUI.

        """
        print("Testing ...")

        self.load_model()

        # Lancement du thread pour stopper avec le GUI
        self.env.receiver_thread()

        # Modification du step_maxi
        self.env.step_maxi = int(self.config[self.numero]['step_maxi_testing'])

        self.model.set_env(self.env)

        print(f"Testing lancé ...")
        obs = self.env.reset()
        while self.env.continue_env:
            action, _states = self.model.predict(obs)
            obs, rewards, dones, info = self.env.step(action)
        sleep(0.5)
        self.env.close()

    def training_gui(self, parts):
        """Training en lançant avec le GUI.
        Un training complet c'est 30 batchs de 100 000 steps.

        Training de 1 seul batch
        Stop avec self.current_step = maxi
        """
        print(f"Training ... avec le GUI ... parts={parts}")

        # Lancement du thread pour stopper avec le GUI
        self.env.receiver_thread()

        TIMESTEPS = self.learning_steps

        model_file = self.get_demo_model_file(parts)
        print(f"training model_file = {model_file}")
        self.model = PPO.load(model_file, cloudpickle=False, verbose=0)
        print(f"Type de self.model = {type(self.model)}")
        self.model.set_env(self.env)

        dt_now = datetime.now()
        dt = dt_now.strftime("%d-%m-%Y | %H:%M")
        print(f"\nApprentissage: "
              f"Steps total = {self.env.step_total} "
              f"Learning steps = {self.learning_steps} à {dt}\n")

        checkpoint_callback = CustomCallback(verbose=0)

        self.model.learn(total_timesteps=TIMESTEPS,
                         reset_num_timesteps=False,
                         tb_log_name=f"PPO{self.numero}",
                         callback=checkpoint_callback)
        print(f"Fin de model.learn()")

        # Sauvegarde du model courrant
        dt_now = datetime.now()
        dt = dt_now.strftime("%d-%m-%Y | %H:%M")
        print(f"\nFin de l'apprentissage de {self.model_name} à {dt} "
              f"avec Steps total = {self.env.step_total}")

        self.env.close()
        sleep(0.5)
        del self.env
        del self

    def get_demo_model_file(self, parts):
        """De 000 000 à 2 900 000 .zip dans ./models/PPO102/

        parts de 0 à 29 soit 30 fichiers
            0 -->   000000
            1 -->   100000
            29 --> 2900000
        """

        models_dir = f"{self.current_dir}/models/PPO102"
        # # if parts == 0:
            # # model_file = f"{models_dir}/0.zip"
        # # else:
        model_file = f"{models_dir}/{parts}00000.zip"
        print(f"Fichier model pour le Training GUI = {model_file}")

        return model_file



def training(current_dir, config_obj, numero, conn, parts):
    tt = TrainTest(current_dir, config_obj, numero, conn)
    tt.training_gui(parts)


def testing(current_dir, config_obj, numero, conn):
    print(f"Testing lancé avec {numero}")
    tt = TrainTest(current_dir, config_obj, numero, conn)
    print(f"Objet tt construit !")
    tt.testing_gui()


def main(numero, train_test):
    """numero = nom de l'apprentissage = str
    C'est pratique de leur donner un numéro comme nom, il ne sont pas des êtres
    humains, ils sont des numéros (et peut-être même numéro 6 ou numéro 1,
    pourquoi pas!)
    """

    current_dir = str(Path(__file__).parent.absolute())
    print("Dossier courrant:", current_dir)

    ini_file = current_dir + '/furuta.ini'
    print("Fichier de configuration:", ini_file)

    config_obj = MyConfig(ini_file)
    tt = TrainTest(current_dir, config_obj, numero, None)

    if train_test == 'train':
        tt.create_model()
        # # tt.print_model_attr()
        tt.training_gui(0)

    if train_test == 'test':
        tt.testing(None)



if __name__ == '__main__':
    """python3 train_test.py 102 train"""

    main('102', 'train')

    # # print(  f"Usage:\n",
            # # f"Pour un training:\n",
            # # f"    train_test nom_de_l_apprentissage train\n",
            # # f"Pour un testing:\n",
            # # f"    train_test nom_de_l_apprentissage test\n")

    # # try:
        # # numero = sys.argv[1]
    # # except:
        # # print(f"Vous devez spécifier le nom de l'apprentissage, 'idem est' son numero\n"
        # # f"C'est pratique de leur donner un numéro comme nom, ils ne sont pas des êtres\n"
        # # f"humains, ils sont des numéros (et peut-être même numéro 6 ou ... numéro 1,"
        # # f" pourquoi pas!)")
        # # sys.exit()

    # # try:
        # # train_test = 'train'  #sys.argv[2]
    # # except:
        # # print(f"Vous devez spécifier train ou test")
        # # sys.exit()

    # # if train_test not in ['train', 'test']:
        # # print(f"Vous devez spécifier train ou test")
        # # sys.exit()

    # # main(numero, train_test)
