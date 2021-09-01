import itertools
import os

import matplotlib.pyplot as plt
import pandas as pd


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


def build_percent_diag(filename):
    """
    Builds percent diagram with codes and errors to velocities graph
    @param filename:
    @return:
    """
    try:
        file_extension = filename.split('.')[-1]
        if file_extension == 'parquet':
            df = pd.read_parquet(filename, engine='fastparquet')
        elif file_extension == 'xlsx':
            df = pd.read_excel(filename, engine='openpyxl')
        else:
            df = pd.read_csv(filename.path)
    except ValueError:
        df = pd.read_csv(filename.path)

    def get_distance(foldername):
        foldername = os.path.split(foldername)[1]
        n_targ = get_n_targets(foldername)
        foldername2 = foldername.split(sep="_")
        if n_targ == 1:
            return max(float(foldername2[1]), float(foldername2[2]))
        elif n_targ == 2:
            return min(float(foldername2[1]), float(foldername2[2]))

    df['dist'] = df['datadir'].apply(get_distance)
    n_targ = 2 if len(df.query('dist1!=0 & dist2 != 0')) else 1
    a = pd.pivot_table(df, values='datadir', index=['dist'], columns=['code'], aggfunc='count', fill_value=0)
    asum = a.sum(axis=1)
    a = a.divide(asum, axis=0) * 100
    dists = list(a.index)
    code0_p = list(a[0].values)
    code1_p = list(a[1].values)
    code2_p = list(a[2].values)
    code4_p = list(a[4].values)
    code5_p = list(a[5].values)
    print(list(asum.values))
    return [code0_p, code1_p, code2_p, code4_p, code5_p, dists, n_targ, ]


def plot_graph_normal(df: pd.DataFrame, title=''):
    fig = plt.figure(figsize=(10, 6), dpi=200)
    style = itertools.cycle(['b', 'r', 'y--', 'o--', 'g', 'g--'])

    plt.plot(df.index, df[df.columns[0]], next(style), label=df.columns[0], linewidth=3)
    for col in df.columns[1:]:
        plt.plot(df.index, df[col], next(style), label=col)

    plt.grid()
    plt.axis([min(df.index), max(df.index), 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=18)
    plt.ylabel('Маневр построен, %', fontsize=18)
    plt.legend(loc='upper left', shadow=True)
    plt.title(title)
    plt.tight_layout()

    return fig


def plot_minister_mode(df: pd.DataFrame, title=''):
    fig = plt.figure(figsize=(10, 6), dpi=200)
    code0 = df['Код 0'] + df['Код 1'] + df['Код 5']
    plt.plot(df.index, code0, 'b', label="Код 0", linewidth=3)
    plt.fill_between(df.index, code0, 100, color='orange', alpha=0.5)
    plt.fill_between(df.index, code0, 0, color='green', alpha=0.5)
    plt.grid()
    plt.axis([min(df.index), max(df.index), 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=18)
    plt.ylabel('Маневр построен, %', fontsize=18)
    plt.title(title)
    plt.tight_layout()

    return fig
