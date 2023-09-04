import matplotlib.pyplot as plt
from numpy.typing import NDArray
from fingerJointBoxMaker.geometry import Path
import numpy as np

from matplotlib import cm

def plot_points(path: NDArray, **plotargs):
    """ Plot path provided as list of point [[x, y], [x, y], ....]"""

    ax: plt.Axes
    fig, ax = plt.subplots(1, 1)
    plotargs.setdefault("marker", ".")
    ax.plot(path.T[0], path.T[1], **plotargs)
    ax.scatter(path.T[0][0], path.T[1][0], marker="*", color="black")
    return fig, ax

def plot_paths(*path: Path):
    
    fig, ax = plt.subplots(1, 1)
    colors = cm.get_cmap("tab10")(np.arange(0, 1, step=.1))
    for idx, p in enumerate(path[0]):
        plot_path(p, ax=ax, color=colors[idx])

    return fig, ax


def plot_path(path: Path, ax: plt.Axes = None, color="blue"):

    if ax is None:
        fig, ax = plt.subplots(1, 1)
    else:
        fig = ax.get_figure()

    marker = "."
    for line in path.lines:
        if line.is_construction:
            line_type = "--"
        else:
            line_type = "-"
        ax.plot(line.line.T[0], line.line.T[1], color=color, marker=marker, linestyle=line_type)
    
    ax.set_ylim(-10, 200)
    ax.set_xlim(-10, 200)
    ax.scatter(path.points.T[0][0], path.points.T[1][0], marker="*", color="black")
    ax.set_aspect('equal')

    return fig, ax