
# TODO à mieux intégrer
"""
Dessine les courbes d'efficacité pendant l'apprentissage
"""

import os, sys
from pathlib import Path
import json

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

from my_config import MyConfig

efficiency_dir = './efficiency'

if not os.path.exists(efficiency_dir):
    os.makedirs(efficiency_dir)
    print(f"Création de {efficiency_dir}")


def plot_efficiency(name, force):
    lines = []
    # # d = Path('./datas_1')
    d = Path(f'./datas/datas_{name}')
    for file_name in d.iterdir():
        # # print(file_name)
        with open(file_name) as f:
            data = json.loads(f.read())
            for val in data:
                lines.append(val)

    # # print(lines)  # [step, reward]

    steps = []
    rewards = []
    for item in lines:
        if isinstance(item, list):
            if len(item) == 2:
                # Pour définir le step de départ
                if item[0] > 0:
                    # pas de valeur < à .
                    if item[1] > 0.3:
                        steps.append(item[0])
                        rewards.append(item[1])

    steps, rewards = zip(*sorted(zip(steps, rewards)))

    poly = np.polyfit(steps, rewards, force)
    poly_y = np.poly1d(poly)(steps)


    fig, ax = plt.subplots(1, 1, figsize=(16,20), facecolor='#cccccc')

    ax.set_facecolor('#eafff5')
    ax.set_title('Cycles Efficiency', size=24, color='magenta')
    ax.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)
    ax.set_xlabel('Step number', color='coral', size=20)
    ax.set_ylabel('Cycle Reward', color='coral', size=20)
    # # ax.legend(loc="upper right", title="Efficiency")

    l = ax.plot(steps, rewards, color='orange', label="Loss")
    l = ax.plot(steps, poly_y, color='red', label="Loss Smoothed")

    fig.savefig(f'{efficiency_dir}/efficiency_{name}.png')
    plt.show()



if __name__ == '__main__':

    try:
        name = sys.argv[1]
    except:
        name = '15'
    try:
        force = int(sys.argv[2])
    except:
        force = 5
    print(f"name {name} force {force}")
    plot_efficiency(name, force)
