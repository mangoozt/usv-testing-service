import itertools

import matplotlib.pyplot as plt
import pandas as pd


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
    code0 = df[0] + df[1] + df[5]
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
