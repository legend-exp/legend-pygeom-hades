from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pyg4ometry
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pygeomhades import plot
from pygeomhades.plot import get_profile


def test_plot():
    font_size = mpl.rcParams["font.size"]
    fig, ax = plot.plot_profiles(
        {
            "vol1": {"z": [0, 1, 2], "r": [0, 1, 0], "offset": 0},
            "vol2": {"z": [0, 1, 2], "r": [0, 0.5, 0], "offset": 0.5},
        },
        title="test plot",
        show=False,
    )

    assert isinstance(fig, Figure)
    assert isinstance(ax, Axes)
    assert ax.xaxis.label.get_fontsize() == 14
    assert mpl.rcParams["font.size"] == font_size


def test_plot_show(monkeypatch):
    calls = []
    monkeypatch.setattr(plt, "show", lambda: calls.append("show"))
    plot.plot_profiles({"vol": {"z": [0, 1], "r": [0, 1], "offset": 0}}, show=True)
    assert calls == ["show"]


def test_profile():
    reg = pyg4ometry.geant4.Registry()

    polycone = pyg4ometry.geant4.solid.Polycone(
        "test_polycone",
        0,
        2 * np.pi,
        [0, 10],
        [2, 10],
        [3, 10],
        lunit="mm",
        registry=reg,
    )

    profile = get_profile(polycone)

    assert profile["r"] == [2, 10, 10, 3, 2]
    assert profile["z"] == [0, 10, 10, 0, 0]

    generic_polycone = pyg4ometry.geant4.solid.GenericPolycone(
        "test_generic_polycone",
        0,
        2 * np.pi,
        [0, 0, 10, 0],
        [2, 2, 5, 5],
        lunit="mm",
        registry=reg,
    )
    profile = get_profile(generic_polycone)
    assert profile["r"] == [0, 0, 10, 0, 0]
    assert profile["z"] == [2, 2, 5, 5, 2]
