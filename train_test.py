
from time import sleep
from threading import Thread
from datetime import datetime, timedelta
from pathlib import Path
import json
import os, sys
from os.path import exists

import gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback

from my_config import MyConfig
from furuta_env import FurutaEnv



class TrainTest:

    def __init__(self, config_obj, numero):

        # Mon object Config
        self.config_obj = config_obj
        # Le dict de la configuration
        self.config = config_obj.conf

        self.numero = numero  # str
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
        self.best =int(self.config[self.numero]['best'])

        self.model_name = f"ppo_neo_{self.numero}"
        print(f"Nom du model {self.model_name}")
        self.env = FurutaEnv(self.config_obj, self.numero)
        self.model = None

        self.model_file = f'./my_models/{self.model_name}.zip'
        print(f"Nom et chemin du model {self.model_file}")

        self.models_dir = f"./models/PPO{self.numero}"
        self.logdir = "./logs"
        self.datas_dir = f"./datas/datas_{self.numero}"
        self.weights_dir = f"./weights/weights_{self.numero}"
        self.best_model_save_path = f"./bests/best_{self.numero}"

        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            print(f"Création de {self.models_dir}")
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)
            print(f"Création de {self.logdir}")
        if not os.path.exists(self.datas_dir):
            os.makedirs(self.datas_dir)
            print(f"Création de {self.datas_dir}")
        if not os.path.exists(self.weights_dir):
            os.makedirs(self.weights_dir)
            print(f"Création de {self.weights_dir}")
        if not os.path.exists(self.best_model_save_path):
            os.makedirs(self.best_model_save_path)
            print(f"Création de {self.best_model_save_path}")

    def create_model(self):
        """https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
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
        print(f"Model sauvegardé: {self.model_name}")

    def load_model(self):
        self.model = PPO.load(self.model_file, cloudpickle=False, verbose=0)
        print(f"Model chargé: {self.model_name} \n")

    def save_weights(self):
        dt_now = datetime.now()
        dt = dt_now.strftime("%d-%m-%Y | %H:%M")
        num = self.env.step_total
        fichier = f"{self.weights_dir}/cuda_{self.numero}_{num}.zip"
        print(f"Enregistrement de: {fichier} à {dt}")
        self.model.save(fichier)

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
        """learning_steps = 20000
        15*20000 = 5 heures
        """
        self.load_model()
        self.model.set_env(self.env)

        TIMESTEPS = self.learning_steps
        batch = int(self.config[self.numero]['batch'])

        # Temps en secondes du train complet. x Hz
        t = batch * TIMESTEPS / 14
        f = datetime.now() + timedelta(seconds=t)
        fin = f.strftime("%d-%m-%Y | %H:%M")
        print(f"\nFin à {fin}\n")

        if self.best:
            eval_callback = EvalCallback(self.env,
                                         best_model_save_path=self.best_model_save_path,
                                         log_path=self.logdir,
                                         eval_freq=500,
                                         deterministic=True,
                                         render=False)

        for i in range(batch):

            dt_now = datetime.now()
            dt = dt_now.strftime("%d-%m-%Y | %H:%M")
            print(f"\nApprentissage n° {i+1} sur {batch} Steps total = {self.env.step_total} "
                 f"Learning steps = {self.learning_steps} Steps par cycle = "
                 f"{self.env.step_maxi} à {dt}\n")

            try:
                # # if not self.best:
                self.model.learn(total_timesteps=TIMESTEPS,
                                 reset_num_timesteps=False,
                                 tb_log_name=f"PPO{self.numero}")
                # # else:
                    # # self.model.learn(total_timesteps=TIMESTEPS,
                                     # # reset_num_timesteps=False,
                                     # # tb_log_name=f"PPO{self.numero}",
                                     # # callback=eval_callback)
            except:
                print(f"Soit vous avez interrompu l'apprentissage avec Echap,\n"
                        f"   soit vous avez un problème que vous allez devoir résoudre!")
                sleep(2)
                os._exit(0)

            self.model.save(f"{self.models_dir}/{TIMESTEPS*i}")

            # Un batch fait self.learning_steps Réinitialisation des steps du batch
            self.env.batch_step = 0

            # Enregistrement dans *.ini
            self.config_obj.save_config(self.numero, 'step_total', self.env.step_total)

            dt_now = datetime.now()
            dt = dt_now.strftime("%d-%m-%Y | %H:%M")
            print(f"Sauvegarde du model {self.model_name} à {dt}\n")
            self.save_model()

            # Sauvegarde d'une copie du model et efficacité
            self.save_weights()
            self.save_efficiency()

        self.env.close()

    def testing(self):
        print("Testing ...")

        obs = self.env.reset()
        while True:
            action, _states = self.model.predict(obs)
            obs, rewards, dones, info = self.env.step(action)



def main(numero, train_test):
    """numero = nom de l'apprentissage avec str de 2 chiffres
    """
    current_dir = str(Path(__file__).parent.absolute())
    print("Dossier courrant:", current_dir)

    ini_file = current_dir + '/furuta.ini'
    print("Fichier de configuration:", ini_file)

    config_obj = MyConfig(ini_file)
    tt = TrainTest(config_obj, numero)

    if train_test == 'train':
        tt.create_model()
        tt.print_model_attr()
        tt.training()

    if train_test == 'test':
        tt.print_model_attr()
        tt.testing()



if __name__ == '__main__':
    """python3 train_test.py 100 train
    """

    print(  f"Usage:\n",
            f"Pour un training:\n",
            f"    train_test nom_de_l_apprentissage train\n",
            f"Pour un testing:\n",
            f"    train_test nom_de_l_apprentissage test\n")

    try:
        numero = sys.argv[1]
    except:
        print(f"Vous devez spécifier le nom de l'apprentissage, idem est son numero")
        sys.exit()

    try:
        train_test = sys.argv[2]
    except:
        print(f"Vous devez spécifier train ou test")
        sys.exit()

    if train_test not in ['train', 'test']:
        print(f"Vous devez spécifier train ou test")
        sys.exit()

    main(numero, train_test)


"""
Parameters:
policy: The policy model to use (MlpPolicy, CnnPolicy, …)
env: The environment to learn from
learning_rate: The learning rate, it can be a function of the current progress remaining (from 1 to 0)
n_steps: The number of steps to run for each environment per update
batch_size: Minibatch size
n_epochs: Number of epoch when optimizing the surrogate loss
gamma: Discount factor
gae_lambda: Factor for trade-off of bias vs variance for Generalized Advantage Estimator
clip_range: Clipping parameter, it can be a function of the current progress remaining (from 1 to 0).
clip_range_vf: Clipping parameter for the value function, it can be a function of the current progress remaining (from 1 to 0). This is a parameter specific to the OpenAI implementation. If None is passed (default), no clipping will be done on the value function. IMPORTANT: this clipping depends on the reward scaling.
normalize_advantage: Whether to normalize or not the advantage
ent_coef: Entropy coefficient for the loss calculation
vf_coef: Value function coefficient for the loss calculation
max_grad_norm: The maximum value for the gradient clipping
use_sde: Whether to use generalized State Dependent Exploration (gSDE) instead of action noise exploration (default: False)
sde_sample_freq: Sample a new noise matrix every n steps when using gSDE Default: -1 (only sample at the beginning of the rollout)
target_kl: Limit the KL divergence between updates, because the clipping is not enough to prevent large update. By default, there is no limit on the kl div.
tensorboard_log: the log location for tensorboard (if None, no logging)
create_eval_env: Whether to create a second environment that will be used for evaluating the agent periodically. (Only available when passing string for the environment)
policy_kwargs: additional arguments to be passed to the policy on creation
verbose: the verbosity level: 0 no output, 1 info, 2 debug
seed: Seed for the pseudo random generators
device: Device (cpu, cuda, …) on which the code should be run. Setting it to auto, the code will be run on the GPU if possible.
_init_setup_model: Whether or not to build the network at the creation of the instance
    # https://github.com/RPC2/PPO
    # learning_rate default=0.0003 11 millions

model PPO maxi = 80
policy = ActorCriticPolicy(
  (features_extractor): FlattenExtractor(
    (flatten): Flatten(start_dim=1, end_dim=-1)
  )
  (mlp_extractor): MlpExtractor(
    (shared_net): Sequential()
    (policy_net): Sequential(
      (0): Linear(in_features=5, out_features=64, bias=True)
      (1): Tanh()
      (2): Linear(in_features=64, out_features=64, bias=True)
      (3): Tanh()
    )
    (value_net): Sequential(
      (0): Linear(in_features=5, out_features=64, bias=True)
      (1): Tanh()
      (2): Linear(in_features=64, out_features=64, bias=True)
      (3): Tanh()
    )
  )
  (action_net): Linear(in_features=64, out_features=160, bias=True)
  (value_net): Linear(in_features=64, out_features=1, bias=True)
)

"""
