import datetime
import os

import matplotlib.pyplot as plt
import pandas as pd

vel_param = [4, 6.5, 8.5, 9.8, 12.2, 16, 19, 20]
vel_param_x = [4, 4.333, 4.666, 5, 6, 7, 8, 8.333]

vel_func = lambda x: 3.06 * x - 5.502

unsolved_x = [5, 6, 7, 8, 9, 10, 11, 11.5]
unsolved_y = [81, 91, 96, 100, 100, 100, 100, 100]


def get_n_targets(name):
    """
    Detects number of targets in case
    @param name: foldername with path
    @return:
    """
    foldername = os.path.split(name)[1]
    foldername2 = foldername.split(sep="_")
    if float(foldername2[1]) == 0 or float(foldername2[2]) == 0:
        return 1
    else:
        return 2


def build_percent_diag(filename, dist_max, dist_min, step):
    """
    Builds percent diagram with codes and errors to velocities graph
    @param filename:
    @param dist_max:
    @param dist_min:
    @param step:
    @return:
    """
    try:
        df = pd.read_excel(filename, engine='openpyxl')
    except:
        df = pd.read_csv(filename)
    names = df['datadir']
    codes = df['code']
    N = int((dist_max - dist_min) / step)
    dists = [dist_min + i * step for i in range(N + 1)]
    N_dists = [0 for i in range(N + 1)]
    code0 = [0 for i in range(N + 1)]
    code1 = [0 for i in range(N + 1)]
    code2 = [0 for i in range(N + 1)]
    code4 = [0 for i in range(N + 1)]
    code5 = [0 for i in range(N + 1)]
    code4_fnmes = []
    vel2 = []
    dist2 = []
    f_names2 = []
    n_targ = 1
    for i, name in enumerate(names):
        foldername = os.path.split(name)[1]
        n_targ = get_n_targets(foldername)
        foldername2 = foldername.split(sep="_")
        dist = 0
        if n_targ == 1:
            dist = max(float(foldername2[1]), float(foldername2[2]))
        elif n_targ == 2:
            dist = min(float(foldername2[1]), float(foldername2[2]))
        if codes[i] == 0:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code0[ind] += 1
                N_dists[ind] += 1
        elif codes[i] == 2:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code2[ind] += 1
                N_dists[ind] += 1
            vel2.append(float(foldername2[3]))
            dist2.append(dist)
            if float(foldername2[3]) < vel_func(dist):
                f_names2.append(foldername)
        elif codes[i] == 4:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code4[ind] += 1
                N_dists[ind] += 1
            code4_fnmes.append(foldername)
        elif codes[i] == 1:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code1[ind] += 1
                N_dists[ind] += 1
        elif codes[i] == 5:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code5[ind] += 1
                N_dists[ind] += 1
    for i in range(N + 1):
        if N_dists[i] == 0:
            N_dists[i] = 1
    code0_p = [code0[i] / N_dists[i] * 100 for i in range(N + 1)]
    code1_p = [code1[i] / N_dists[i] * 100 for i in range(N + 1)]
    code2_p = [code2[i] / N_dists[i] * 100 for i in range(N + 1)]
    code4_p = [code4[i] / N_dists[i] * 100 for i in range(N + 1)]
    code5_p = [code5[i] / N_dists[i] * 100 for i in range(N + 1)]
    print(N_dists)
    name_n = plot_graph_normal(name, code0_p, code1_p, code2_p, code4_p, code5_p, dists, n_targ, dist_min, dist_max)
    name_m = plot_minister_mode(name, code0_p, code1_p, code2_p, code4_p, code5_p, dists, n_targ, dist_min, dist_max)
    return [code0_p, code1_p, code2_p, code4_p, code5_p, dists, n_targ, name_n, name_m]


def plot_graph_normal(name, code0_p, code1_p, code2_p, code4_p, code5_p, dists, n_targ, dist_min, dist_max):
    plt.figure(figsize=(10, 6), dpi=200)
    plt.plot(dists, code0_p, 'b', label="Код 0", linewidth=3)
    plt.plot(dists, code1_p, 'r', label="Код 1")
    plt.plot(dists, code2_p, 'y--', label="Код 2")
    plt.plot(dists, code4_p, 'o--', label="Код 4")
    plt.plot(dists, code5_p, 'g', label="Код 5")
    plt.grid()
    plt.axis([dist_min, dist_max, 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=20)
    plt.ylabel('Маневр построен, %', fontsize=20)
    # plt.plot(unsolved_x, unsolved_y, 'o--')
    plt.legend(loc='upper left', shadow=True)
    plt.title("Дата: " + str(datetime.date.today()) + ", цели: " + str(n_targ))
    i_name = "./media/" + str(datetime.date.today()) + "_" + str(n_targ) + "_" + name + "_stats.png"
    plt.savefig(i_name)
    return os.path.split(i_name)[1]


def plot_minister_mode(name, code0_p, code1_p, code2_p, code4_p, code5_p, dists, n_targ, dist_min, dist_max):
    plt.figure(figsize=(10, 6), dpi=200)
    code0 = [code0_p[i] + code1_p[i] + code5_p[i] for i in range(len(dists))]
    plt.plot(dists, code0, 'b', label="Код 0", linewidth=3)
    plt.fill_between(dists, code0, 100, color='orange', alpha=0.5)
    plt.fill_between(dists, code0, 0, color='green', alpha=0.5)
    plt.grid()
    plt.axis([dist_min, dist_max, 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=20)
    plt.ylabel('Маневр построен, %', fontsize=20)
    plt.title("Дата: " + str(datetime.date.today()) + ", цели: " + str(n_targ))
    i_name = "./media/" + str(datetime.date.today()) + "_" + str(n_targ) + "_" + name + "_minister.png"
    plt.savefig(i_name)
    return os.path.split(i_name)[1]
