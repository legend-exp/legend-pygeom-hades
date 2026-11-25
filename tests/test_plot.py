from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pygeomhades import plot


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
